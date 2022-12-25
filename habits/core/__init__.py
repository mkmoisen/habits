from datetime import timedelta

from flask import flash


def date_loop(start_date, end_date):
    while start_date <= end_date:
        yield start_date
        start_date += timedelta(days=1)


def flash_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}')
