from habits.models import Habit, HabitDays, HabitTag
import itertools

from peewee import fn


def select_habits(user_id):
    habits = list(
        Habit.select(
            Habit,
            fn.array(
                HabitDays.select(
                    HabitDays.day
                ).where(
                    HabitDays.habit_id == Habit.id
                )
            ).alias('days'),
            fn.array(
                HabitTag.select(
                    HabitTag.tag
                ).where(
                    HabitTag.habit_id == Habit.id
                )
            ).alias('tags')
        ).where(
            Habit.user_id == user_id
        )
    )

    return habits
