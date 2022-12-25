import itertools

from flask import Blueprint, session
from flask import render_template
from datetime import datetime, timedelta, date

from habits.core import date_loop
from habits.core.habits import select_habits
from habits.models import HabitLog, Habit, User, db

app = Blueprint('home', __name__)


@app.route('/')
def ui_home():
    start_date, end_date = _calculate_date_boundaries()

    with db:
        _insert_incremental_habit_schedule(session['user_id'])
        habits_by_dates = _select_habit_logs(session['user_id'], start_date, end_date)

    rows = _cut_into_rows(habits_by_dates)

    return render_template('home.html', rows=rows, username=session['username'])


def _calculate_date_boundaries():
    today = date.today()
    this_monday = today
    while this_monday.weekday() != 0:
        this_monday -= timedelta(days=1)

    start_date = this_monday - timedelta(days=14)
    end_date = this_monday + timedelta(days=13)

    return start_date, end_date


def _select_habit_logs(user_id, start_date, end_date):
    habit_logs = list(
        HabitLog.select(
            HabitLog.scheduled_date,
            HabitLog.completed,
            Habit.id.alias('habit_id'),
            Habit.name,
        ).join(
            Habit
        ).where(
            Habit.user_id == user_id,
            HabitLog.scheduled_date.between(start_date, end_date)
        ).order_by(
            HabitLog.scheduled_date,
            HabitLog.habit_id
        ).dicts()
    )

    habits_by_dates = _group_habit_logs_by_date(habit_logs)

    habits_by_dates = _add_missing_days(habits_by_dates, start_date, end_date)

    return habits_by_dates


def _group_habit_logs_by_date(habit_logs):
    habits_by_dates = [
        {
            'scheduled_date': key,
            'date_string': key.strftime('%Y-%m-%d'),
            'habits': [
                {
                    'id': row['habit_id'],
                    'name': row['name'],
                    'completed': row['completed']
                }
                for row in group
            ]
        }
        for key, group in itertools.groupby(habit_logs, key=lambda x: x['scheduled_date'])
    ]

    return habits_by_dates


def _add_missing_days(habit_by_dates, start_date, end_date):
    habit_by_dates = {
        habit_by_date['scheduled_date']: habit_by_date
        for habit_by_date in habit_by_dates
    }

    missing = {
        scheduled_date: {
            'scheduled_date': scheduled_date,
            'date_string': scheduled_date.strftime('%Y-%m-%d')
        }
        for scheduled_date in date_loop(start_date, end_date)
        if scheduled_date not in habit_by_dates
    }

    habit_by_dates.update(missing)

    return list(sorted(habit_by_dates.values(), key=lambda x: x['scheduled_date']))


def _cut_into_rows(habits_by_dates):
    rows = []
    current_row = []
    for habits_by_date in habits_by_dates:
        if habits_by_date['scheduled_date'].weekday() == 0 and current_row:
            rows.append(current_row)
            current_row = []
        current_row.append(habits_by_date)

    if current_row:
        rows.append(current_row)

    return rows


def _insert_incremental_habit_schedule(user_id):
    db.execute_sql(
        """
        WITH date_boundaries as (
                SELECT MIN(scheduled_date) start_date,
                    CURRENT_DATE + 28 end_date
                FROM (
                    SELECT habit_id, MAX(scheduled_date) scheduled_date
                    FROM habit_logs
                    WHERE 1=1
                        AND user_id = %(user_id)s
                    GROUP BY habit_id
                ) habit_logs
            )
        insert into habit_logs (habit_id, scheduled_date, completed, user_id)
        select habit_days.habit_id, scheduled_date, False, %(user_id)s
        from generate_series(
            (
                SELECT date_boundaries.start_date
                FROM date_boundaries
            ), 
            (
                SELECT date_boundaries.end_date
                FROM date_boundaries
            ),
            interval '1 day'
        ) as t(scheduled_date)
        join habit_days
            on extract(isodow from scheduled_date) - 1 = habit_days.day
        where 1=1
            and habit_days.user_id = %(user_id)s
            and not exists (
                select 1
                from habit_logs
                where 1=1
                    and habit_logs.habit_id = habit_days.habit_id
                    and habit_logs.scheduled_date = t.scheduled_date
            )
        """,
        {
            'user_id': user_id,
        }
    )
