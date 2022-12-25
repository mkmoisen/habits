from datetime import date, timedelta

import peewee
from flask import Blueprint, session, render_template, redirect, url_for, flash
from habits.core import flash_form_errors
from habits.core.habits import select_habits

from habits.models import db, Habit, HabitDays, HabitLog, HabitTag

from flask_wtf import FlaskForm
from peewee import fn
from wtforms import StringField, SelectMultipleField, DateField, HiddenField, TextAreaField
from wtforms.validators import DataRequired

app = Blueprint('habits', __name__)


def parse_validator(form, field):
    if field.data:
        field.data = field.data.splitlines()


class HabitForm(FlaskForm):
    id = HiddenField()
    name = StringField('name', validators=[DataRequired()])
    days = SelectMultipleField(
        'days',
        choices=list(
            enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        ),
        coerce=int,
        validators=[DataRequired()]
    )
    start_date = DateField(
        'start_date',
        default=date.today,
        validators=[DataRequired()]
    )
    tags = TextAreaField('tags (separated by newline)', validators=[parse_validator])


@app.route('/habits', methods=['GET', 'POST'])
def ui_habits():
    form = HabitForm()

    with db:
        if form.validate_on_submit():

            if not form.id.data:
                ui_create_habit(
                    user_id=session['user_id'],
                    name=form.name.data,
                    start_date=form.start_date.data,
                    days=form.days.data,
                    tags=form.tags.data,
                )

            else:
                ui_update_habit(
                    user_id=session['user_id'],
                    habit_id=form.id.data,
                    name=form.name.data,
                    start_date=form.start_date.data,
                    days=form.days.data,
                    tags=form.tags.data,
                )

        flash_form_errors(form)

        habits = select_habits(session['user_id'])

    return render_template('habits.html', habits=habits, form=form)


def ui_create_habit(user_id, name, start_date, days, tags):
    try:
        create_habit(user_id, name, start_date, days, tags)
    except DuplicateHabitError:
        flash('A Habit with this name has already been created.', 'error')
    else:
        flash('Habit created successfully.', 'success')


class DuplicateHabitError(Exception):
    ...


def create_habit(user_id, name, start_date, days, tags):
    try:
        habit = _insert_habit(
            user_id=user_id,
            name=name,
            start_date=start_date
        )
    except peewee.IntegrityError:
        db.rollback()
        raise DuplicateHabitError()

    _insert_habit_days(
        habit_id=habit.id,
        days=days,
        user_id=user_id,
    )

    _insert_habit_tags(
        habit_id=habit.id,
        tags=tags,
        user_id=user_id
    )

    _insert_habit_schedule(
        habit.id,
        days=days,
        start_date=start_date,
        user_id=user_id,
    )


def ui_update_habit(user_id, habit_id, name, start_date, days, tags):
    try:
        update_habit(user_id, habit_id, name, start_date, days, tags)
    except DuplicateHabitError:
        flash('A Habit with this name has already been created.', 'error')
    else:
        flash('Habit created successfully.', 'success')


def update_habit(user_id, habit_id, name, start_date, days, tags):
    try:
        Habit.update(
            name=name,
            start_date=start_date
        ).where(
            Habit.id == habit_id,
            Habit.user_id == user_id,
        ).execute()
    except peewee.IntegrityError:
        db.rollback()
        raise DuplicateHabitError()

    HabitDays.delete().where(
        HabitDays.habit_id == habit_id,
    ).execute()

    _insert_habit_days(
        habit_id=habit_id,
        days=days,
        user_id=user_id,
    )

    _update_habit_tags(
        habit_id=habit_id,
        tags=tags,
        user_id=user_id,
    )

    HabitLog.delete().where(
        HabitLog.habit_id == habit_id,
        HabitLog.completed == False,
        HabitLog.scheduled_date >= start_date
    ).execute()

    _insert_habit_schedule(
        habit_id=habit_id,
        days=days,
        start_date=start_date,
        user_id=user_id
    )


def _update_habit_tags(habit_id, tags, user_id):
    HabitTag.delete().where(
        HabitTag.habit_id == habit_id,
        HabitTag.user_id == user_id,
        HabitTag.tag.not_in(tags)
    ).execute()

    db.execute_sql(
        '''
        INSERT INTO habit_tags (
            habit_id, tag, user_id
        ) SELECT
            %(habit_id)s, 
            tags.tag,
            %(user_id)s
        FROM (
            SELECT tag
            FROM unnest(%(tags)s) tag
        ) tags
        ON CONFLICT (habit_id, tag)
        DO NOTHING
        ''',
        {
            'tags': tags,
            'user_id': user_id,
            'habit_id': habit_id
        }
    )


@app.get('/habits/<habit_id>/delete')
def ui_delete_habit(habit_id):
    with db:
        HabitLog.delete().where(
            HabitLog.habit_id == habit_id,
            fn.exists(
                Habit.select().where(
                    Habit.user_id == session['user_id'],
                    HabitLog.habit_id == Habit.id
                )
            )
        ).execute()

        HabitDays.delete().where(
            HabitDays.habit_id == habit_id,
            fn.exists(
                Habit.select().where(
                    Habit.user_id == session['user_id'],
                    HabitDays.habit_id == Habit.id,
                )
            )
        ).execute()

        Habit.delete().where(
            Habit.id == habit_id,
            Habit.user_id == session['user_id']
        ).execute()

    flash('Habit deleted successfully.', 'success')

    return redirect(url_for('habits.ui_habits'))


@app.get('/habits/<int:habit_id>/edit')
def ui_edit_habit(habit_id):
    form = HabitForm()

    with db:
        habits = select_habits(session['user_id'])

    habit = next((habit for habit in habits if habit.id == habit_id), None)

    if habit:
        form.id.data = habit.id
        form.name.data = habit.name
        form.days.data = habit.days
        form.start_date.data = habit.start_date
        form.tags.data = '\n'.join(habit.tags)

    return render_template('habits.html', habits=habits, form=form)


def _insert_habit(user_id, name, start_date):
    habit = Habit.create(
        user=user_id,
        name=name,
        start_date=start_date
    )

    return habit


def _insert_habit_days(habit_id, days, user_id):
    rows = [
        (habit_id, day, user_id)
        for day in days
    ]

    HabitDays.insert_many(
        rows,
        fields=[HabitDays.habit, HabitDays.day, HabitDays.user_id]
    ).execute()


def _insert_habit_tags(habit_id, tags, user_id):
    rows = [
        (habit_id, tag, user_id)
        for tag in tags
    ]

    HabitTag.insert_many(
        rows,
        fields=[HabitTag.habit, HabitTag.tag, HabitTag.user_id]
    ).execute()


def _insert_habit_schedule(habit_id, days, start_date, user_id):
    end_date = _determine_end_date(start_date)

    db.execute_sql(
        """
        insert into habit_logs (habit_id, scheduled_date, completed, user_id)
        select %(habit_id)s, scheduled_date, False, %(user_id)s
        from generate_series(%(start_date)s, %(end_date)s, interval '1 day') as t(scheduled_date)
        where 1=1
            and extract(isodow from scheduled_date) - 1 in %(days)s
            and not exists (
                select 1
                from habit_logs
                where 1=1
                    and habit_logs.habit_id = %(habit_id)s
                    and habit_logs.scheduled_date = t.scheduled_date
            )
        """,
        {
            'habit_id': habit_id,
            'start_date': start_date,
            'end_date': end_date,
            'days': tuple(days),
            'user_id': user_id
        }
    )




"""
select scheduled_date, extract(isodow from scheduled_date) - 1
from generate_series(timestamp'2022-11-01', timestamp'2022-11-30', interval '1 day') as scheduled_date
where 1=1
    and extract(isodow from scheduled_date) - 1 in (1, 3)
"""


def _determine_date_boundaries(start_date=None):
    start_date = start_date or date.today()
    next_sunday = start_date
    while next_sunday.day != 6:
        next_sunday = next_sunday + timedelta(days=1)

    final_sunday = next_sunday + timedelta(days=28)

    return start_date, final_sunday


def _determine_end_date(start_date):
    end_date = date.today()
    if start_date > end_date:
        end_date = start_date

    next_sunday = end_date
    while next_sunday.day != 6:
        next_sunday = next_sunday + timedelta(days=1)

    final_sunday = next_sunday + timedelta(days=28)

    return final_sunday
