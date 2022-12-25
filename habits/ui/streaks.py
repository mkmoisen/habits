from flask import Blueprint, session
from habits.models import db

app = Blueprint('streaks', __name__)


@app.get('/streaks')
def ui_get_streaks():
    with db:
        streaks = _determine_streaks(session['user_id'])

    return {
        'items': streaks
    }, 200


def _determine_streaks(user_id):
    rows = db.execute_sql(
        '''
        select name, CASE WHEN max_not_completed_date is not null then cnt - 1 else cnt end cnt
        from (
            select name, lol.max_not_completed_date, COUNT(1) cnt
            from habit_logs
                join (
                    select habits.id,
                        habits.name, 
                    max_completed_date.max_completed_date,
                    max(scheduled_date) filter(
                        where completed = false 
                        and (
                            scheduled_date < max_completed_date.max_completed_date
                            or 
                            max_completed_date.max_completed_date is null
                        )
                    ) max_not_completed_date,
                    min(scheduled_date) filter(where completed = true) min_completed_date
                    from habit_logs
                    join habits
                        on habit_logs.habit_id = habits.id
                    join (
                        select habits.id,
                            max(scheduled_date) filter(where completed = true) max_completed_date
                        from habit_logs
                        join habits
                            on habit_logs.habit_id = habits.id
                        where 1=1
                            and habits.user_id = %s
                        group by habits.id
                    ) max_completed_date
                        on habit_logs.habit_id = max_completed_date.id
                    where 1=1
                        and habits.user_id = %s
                    group by habits.id, habits.name, max_completed_date
                ) lol
                on habit_logs.habit_id = lol.id
            where 1=1
                and habit_logs.scheduled_date between 
                    coalesce(lol.max_not_completed_date, lol.min_completed_date)
                    and coalesce(lol.max_completed_date, lol.max_not_completed_date)
            group by name, lol.max_not_completed_date
        ) foo;
        ''',
        (
            user_id,
            user_id,
        )
    ).fetchall()

    return [
        {
            'name': row[0],
            'streak': row[1]
        }
        for row in rows
    ]
