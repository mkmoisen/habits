from flask import Blueprint, session, redirect, url_for

app = Blueprint('logout', __name__)


@app.get('/logout')
def ui_get_logout():
    session.clear()

    return redirect(url_for('login.ui_login'))

