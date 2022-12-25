from datetime import date, datetime

from flask import session
from habits.models import User, db

from passlib.context import CryptContext

crypt_context = CryptContext(schemes=['argon2'])


def select_user(username, password):
    if not (user := User.get_or_none(username=username)):
        return None

    if is_authenticated_password(password, user.password):
        return user

    return None


def change_password(user_id, new_password):
    User.update(
        password=new_password
    ).where(
        User.id == user_id
    ).execute()


def is_authenticated_password(password, hashed_password):
    return crypt_context.verify(password, hashed_password)


def hash_password(password):
    return crypt_context.hash(password)


def update_last_date_active(user_id, last_date_active, today=None):
    today = today or date.today()

    if isinstance(last_date_active, str):
        last_date_active = datetime.strptime(last_date_active, '%Y-%m-%d').date()

    if today > last_date_active:
        with db:
            User.update(
                last_date_active=today
            ).where(
                User.id == user_id
            ).execute()

            session['last_date_active'] = today.strftime('%Y-%m-%d')
