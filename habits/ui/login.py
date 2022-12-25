from datetime import date

from flask import Blueprint, redirect, render_template, session, flash

from flask_wtf import FlaskForm
from habits.core import flash_form_errors
from habits.core.init_session import init_session
from habits.core.user import select_user, update_last_date_active
from habits.models import db
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired


app = Blueprint('login', __name__)


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


@app.route('/login', methods=['GET', 'POST'])
def ui_login():
    form = LoginForm()

    if form.validate_on_submit():
        with db:
            user = select_user(
                username=form.username.data,
                password=form.password.data
            )

        if user:
            init_session(
                username=user.username,
                user_id=user.id
            )

            update_last_date_active(user.id, user.last_date_active)

            return redirect('/')
        else:
            flash('The username or password is incorrect.', 'error')

    flash_form_errors(form)

    return render_template('login.html', form=form)
