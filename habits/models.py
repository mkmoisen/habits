from datetime import date, datetime

from peewee import Model, TextField, ForeignKeyField, IntegerField, DateField, BooleanField, DateTimeField
from playhouse.pool import PooledPostgresqlExtDatabase
from habits.config import DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT

db = PooledPostgresqlExtDatabase(
    DATABASE_NAME, user=DATABASE_USERNAME, password=DATABASE_PASSWORD,
    host=DATABASE_HOST, port=DATABASE_PORT,
    max_connections=16, stale_timeout=300, timeout=0, autoconnect=False
)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = TextField(null=False, unique=True, index=True)
    email = TextField(null=True, index=True)
    password = TextField(null=False)
    last_date_active = DateField(null=False, default=date.today)

    class Meta:
        db_table = 'users'


class Habit(BaseModel):
    user = ForeignKeyField(User, null=False, on_delete='CASCADE')
    name = TextField(null=False)
    start_date = DateField(null=False)

    class Meta:
        db_table = 'habits'
        indexes = [
            (('user', 'name'), True)
        ]


class HabitTag(BaseModel):
    user = ForeignKeyField(User, null=False, on_delete='CASCADE')
    habit = ForeignKeyField(Habit, null=False, on_delete='CASCADE')
    tag = TextField(null=False)

    class Meta:
        db_table = 'habit_tags'
        indexes = [
            (('habit', 'tag'), True)
        ]


class HabitDays(BaseModel):
    user = ForeignKeyField(User, null=False, on_delete='CASCADE')
    habit = ForeignKeyField(Habit, null=False, backref='days', on_delete='CASCADE')
    day = IntegerField(null=False)

    class Meta:
        db_table = 'habit_days'
        indexes = [
            (('habit', 'day'), True)
        ]


class HabitLog(BaseModel):
    user = ForeignKeyField(User, null=False, on_delete='CASCADE')
    habit = ForeignKeyField(Habit, null=False, index=True, on_delete='CASCADE')
    scheduled_date = DateField(null=False)
    completed = BooleanField(null=False, default=False)

    class Meta:
        db_table = 'habit_logs'
        indexes = [
            (('habit', 'scheduled_date'), True)
        ]


class HabitLogTag(BaseModel):
    user = ForeignKeyField(User, null=False, on_delete='CASCADE')
    habit_log = ForeignKeyField(HabitLog, null=False, on_delete='CASCADE')
    habit_tag = ForeignKeyField(HabitTag, null=True, on_delete='SET NULL')
    minutes = IntegerField(null=True)
    creation_date = DateTimeField(null=False, default=datetime.now)

    class Meta:
        db_table = 'habit_log_tags'
        indexes = [
            (('habit_log_id', 'habit_tag_id',), True)
        ]
