import uuid

from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask_wtf import FlaskForm
from habits.core import flash_form_errors
from habits.core.user import select_user, change_password, hash_password
from habits.models import db, User
from wtforms import PasswordField, EmailField
from wtforms.validators import DataRequired

app = Blueprint('account', __name__)



@app.get('/account')
def ui_get_account():
    return render_template('account/account.html')


class DeleteAccountForm(FlaskForm):
    password = PasswordField(validators=[DataRequired()])


@app.get('/account/delete-account')
def ui_get_delete_account():
    form = DeleteAccountForm()

    return render_template('account/delete-account.html', form=form)


@app.post('/account/delete-account')
def ui_post_delete_account():
    form = DeleteAccountForm()

    if not (select_user(session['username'], form.password.data)):
        return redirect(url_for('account.ui_get_delete_account'))

    if form.validate_on_submit():
        with db:
            _delete_account(session['user_id'])
        return redirect(url_for('home.ui_home'))

    return redirect(url_for('account.ui_get_delete_account'))


def _delete_account(user_id):
    User.delete().where(
        User.id == user_id
    ).execute()

    session.clear()


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(validators=[DataRequired()])
    new_password = PasswordField(validators=[DataRequired()])
    new_confirm_password = PasswordField(validators=[DataRequired()])


@app.get('/account/change-password')
def ui_get_change_password():
    form = ChangePasswordForm()

    return render_template('/account/change-password.html', form=form)


@app.post('/account/change-password')
def ui_post_change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        with db:
            if not (select_user(session['username'], form.current_password.data)):
                flash('The current password is invalid.', 'error')
                return redirect(url_for('account.ui_get_change_password'))

            if form.new_password.data != form.new_confirm_password.data:
                flash('The new passwords do not match.', 'error')
                return redirect(url_for('account.ui_get_change_password'))

            password = hash_password(form.new_password.data)

            change_password(session['user_id'], password)

        flash('Password has been successfully changed', 'success')

    flash_form_errors(form)

    return redirect(url_for('account.ui_get_change_password'))


class ChangeEmailForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired()])
    confirm_email = EmailField('confirm email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


@app.get('/account/change-email')
def ui_get_change_email():
    form = ChangeEmailForm()

    form.email.data = session.pop('change_email_email', None)
    form.confirm_email.data = session.pop('change_email_confirm_email', None)

    return render_template('/account/change-email.html', form=form)


@app.post('/account/change-email')
def ui_post_change_email():

    form = ChangeEmailForm()

    session['change_email_email'] = form.email.data
    session['change_email_confirm_email'] = form.confirm_email.data

    if form.validate_on_submit():
        if form.email.data != form.confirm_email.data:
            flash('Emails did not match.', 'error')
            return redirect(url_for('account.ui_get_change_email'))

        with db:
            if not (select_user(session['username'], form.password.data)):
                flash('The current password is invalid.', 'error')
                return redirect(url_for('account.ui_get_change_email'))

            _change_email(session['user_id'], form.email.data)

            flash('Email has been changed.', 'success')

    flash_form_errors(form)

    return redirect(url_for('account.ui_get_change_email'))


def _change_email(user_id, email):
    User.update(
        email=email
    ).where(
        User.id == user_id
    ).execute()


