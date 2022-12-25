from flask import Flask, session, redirect, request, url_for
from habits.core.user import update_last_date_active
from habits.ui.home import app as home_app
from habits.ui.login import app as login_app
from habits.ui.logout import app as logout_app
from habits.ui.habits import app as habits_app
from habits.ui.sign_up import app as sign_up_app
from habits.ui.habit_logs import app as habit_logs_app
from habits.ui.streaks import app as streaks_app
from habits.ui.account import app as account_app

from habits.config import SECRET_KEY


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    _register_blueprints(app)

    app.before_request(_before_request)
    app.after_request(_after_request)

    return app


def _register_blueprints(app):
    app.register_blueprint(login_app)
    app.register_blueprint(logout_app)
    app.register_blueprint(home_app)
    app.register_blueprint(habits_app)
    app.register_blueprint(sign_up_app)
    app.register_blueprint(habit_logs_app)
    app.register_blueprint(streaks_app)
    app.register_blueprint(account_app)


def _before_request():
    if _should_redirect_to_login_page():
        return redirect(url_for('login.ui_login'))

    if session.get('user_id'):
        update_last_date_active(session['user_id'], session['last_date_active'])


def _should_redirect_to_login_page():
    return (
        'username' not in session
        and request.endpoint not in (
            'login.ui_login',
            'sign_up.ui_get_sign_up',
            'sign_up.ui_post_sign_up',
        )
    )


def _after_request(response):
    return response
