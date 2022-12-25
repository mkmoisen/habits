from datetime import datetime

from flask import Blueprint, session
from habits.models import HabitLog, db, Habit, HabitLogTag
from peewee import fn

app = Blueprint('habit_logs', __name__)


@app.put('/habit-logs/<scheduled_date>/<habit_id>/')
def ui_put_habit_log(scheduled_date, habit_id):
    scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d')

    with db:
        habit_log = HabitLog.update(
            completed=True
        ).where(
            HabitLog.habit_id == habit_id,
            HabitLog.scheduled_date == scheduled_date,
            fn.exists(
                Habit.select().where(
                    Habit.id == habit_id,
                    Habit.user_id == session['user_id']
                )
            )
        ).returning(
            HabitLog.id
        ).execute()[0]

        subquery = HabitLogTag.select(
            fn.max(HabitLogTag.creation_date)
        ).join(
            HabitLog,
        ).where(
            HabitLog.habit_log_id == habit_log.id
        )

        HabitLogTag.insert(
            user_id=session['user_id'],
            habit_id=habit_id,
            habit_log_id=habit_log.id,
            minutes=HabitLogTag.select(
                HabitLogTag.minutes
            ).where(
                HabitLogTag.creation_date == subquery
            ),
            habit_tag_id=HabitLogTag.select(
                HabitLogTag.habit_tag
            ).where(
                HabitLogTag.creation_date == subquery
            ),
            creation_date=datetime.now()
        ).execute()

    return {}, 200


@app.delete('/habit-logs/<scheduled_date>/<habit_id>/')
def ui_delete_habit_log(scheduled_date, habit_id):
    scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d')

    with db:
        HabitLog.update(
            completed=False
        ).where(
            HabitLog.habit_id == habit_id,
            HabitLog.scheduled_date == scheduled_date,
            fn.exists(
                Habit.select().where(
                    Habit.id == habit_id,
                    Habit.user_id == session['user_id']
                )
            )
        ).execute()

    return {}, 200
