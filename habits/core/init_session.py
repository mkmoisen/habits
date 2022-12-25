from datetime import date

from flask import session


def init_session(username, user_id, today=None):
    today = today or date.today()

    session['username'] = username
    session['user_id'] = user_id
    session['last_date_active'] = today.strftime('%Y-%m-%d')