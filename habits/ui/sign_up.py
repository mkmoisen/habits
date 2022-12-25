import random
from datetime import date

import peewee
from flask import Blueprint, redirect, render_template, session, url_for, flash

from flask_wtf import FlaskForm
from habits.core import flash_form_errors
from habits.core.init_session import init_session
from habits.core.user import hash_password
from habits.models import User, db
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired, ValidationError
from cryptography.fernet import Fernet
import operator


app = Blueprint('sign_up', __name__)

fernet = Fernet(Fernet.generate_key())


def validate_spam_check(form, field):
    if not (correct_spam_check := session.pop('spam_check', None)):
        raise ValidationError('Spam check was incorrect')

    try:
        correct_spam_check = int(fernet.decrypt(correct_spam_check))
    except Exception:
        raise ValidationError('Spam check was incorrect')

    if correct_spam_check != field.data:
        raise ValidationError('Spam check was incorrect')


class SignUpForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = StringField('email')
    password = PasswordField('password', validators=[DataRequired()])
    spam_check = IntegerField('spam_check', validators=[DataRequired(), validate_spam_check])


@app.route('/sign-up', methods=['POST'])
def ui_post_sign_up():
    form = SignUpForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data

        password = hash_password(form.password.data)

        with db:
            user_id = _ui_insert_user(
                username=username,
                email=email,
                hashed_password=password
            )

        if user_id:
            init_session(
                username=username,
                user_id=user_id
            )

            return redirect('/')

    flash_form_errors(form)

    session['sign_up_username'] = form.username.data
    session['sign_up_email'] = form.email.data

    return redirect(url_for('sign_up.ui_get_sign_up'))


@app.route('/sign-up', methods=['GET'])
def ui_get_sign_up():
    form = SignUpForm()

    form.username.data = session.pop('sign_up_username', None)
    form.email.data = session.pop('sign_up_email', None)

    left, op, right, answer = _make_spam_check()

    session['spam_check'] = fernet.encrypt(str(answer).encode())

    return render_template('sign_up.html', left=left, operator=op, right=right, form=form)


def _make_spam_check():
    ops = {
        operator.mul: '*',
        operator.add: '+',
        operator.sub: '-',
    }
    op = random.choice([
        operator.mul,
        operator.add,
        operator.sub,
    ])

    left = random.randint(-10, 10)
    right = random.randint(-10, 10)

    answer = op(left, right)

    operator_string = ops[op]

    return left, operator_string, right, answer


class DuplicateUsernameError(Exception):
    pass


def _ui_insert_user(username, email, hashed_password):
    try:
        user_id = _insert_user(username, email, hashed_password)
    except peewee.IntegrityError:
        flash('This username already exists.', 'error')
    else:
        return user_id


def _insert_user(username, email, hashed_password):
    user = User.create(
        username=username,
        email=email,
        password=hashed_password
    )

    return user.id
