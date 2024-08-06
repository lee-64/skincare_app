import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from skincare_app.db import get_users_db, routine_str_to_list

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method != 'POST':
        # When the user initially navigates to auth/register, or there was a validation error, an HTML page with the
        # registration form should be shown. render_template() will render a template containing the HTML
        return render_template('auth/create_account_page.html')

    username = request.form['username']
    password = request.form['password']
    error = validate_auth_form(username, password)

    if error is None:
        db = get_users_db()
        try:
            db.execute(
                "INSERT INTO users (username, password, routine) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), None)
            )
            db.commit()
        # a sqlite3.IntegrityError will occur if the username already exists
        except db.IntegrityError:
            error = f"User {username} is already registered."
        else:
            session.clear()
            # grabbing user info separately from g because their account has been created within this request
            user = db.execute(
                'SELECT * FROM users WHERE username=?', (username,)
            ).fetchone()
            session.update({
                'user_id': user['id'],
                'username': user['username'],
                'routine': routine_str_to_list(user['routine'])
            })

            return redirect(url_for('routine.routine_home'))

    flash(error)
    return render_template('auth/create_account_page.html')


def validate_auth_form(username, password):
    if not username:
        return 'Username is required.'
    elif not password:
        return 'Password is required.'
    return None


@bp.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method != 'POST':
        return render_template('auth/sign_in_page.html')

    # user is already signed in
    if session.get('user_id') is not None:
        return redirect(url_for('routine.routine_home'))

    username = request.form['username']
    password = request.form['password']
    error = validate_auth_form(username, password)

    db = get_users_db()
    user = db.execute(
        'SELECT * FROM users WHERE username=?', (username,)
    ).fetchone()

    if user is None:
        error = 'Incorrect username.'
    # check_password_hash() hashes the submitted password in the same way as the stored hash and securely compares them. If they match, the password is valid.
    elif not check_password_hash(user['password'], password):
        error = 'Incorrect password.'

    if error is None:
        session.clear()
        session.update({
            'user_id': user['id'],
            'username': user['username'],
            'routine': routine_str_to_list(user['routine'])
        })
        return redirect(url_for('routine.routine_home'))

    flash(error)
    return render_template('auth/sign_in_page.html')


# bp.before_app_request() registers a function that runs before the view function, no matter what URL is requested.
# load_signed_in_user checks if a user id is stored in the session and gets that user’s data from the database, storing
# it on g.user, which lasts for the length of the request. If there is no user id, or if the id doesn’t exist, g.user
# will be None.
# WHY?: User data might change between requests. For instance, the user might update their profile, or their permissions
# might be altered. By querying the database on every request, the application ensures it has the most up-to-date user
# information
# essentially: keeps the database FRESH
# @bp.before_app_request
# def load_signed_in_user():
#     user_id = session.get('user_id')
#
#     if user_id is None:
#         g.user = None
#         session.clear()
#         flash('You have been signed out. Please sign in again.')
#     else:
#         g.user = get_users_db().execute(
#             'SELECT * FROM users WHERE id=?', (user_id,)
#         ).fetchone()


@bp.route('/sign_out', methods=['GET', 'POST'])
def sign_out():
    if request.method == 'POST':
        session.clear()
    return redirect(url_for('routine.routine_home'))


# a decorator can be used to check if the user is logged in for each view it’s applied to
# This decorator returns a new view function that wraps the original view it’s applied to. The new function checks if a
# user is loaded and redirects to the login page otherwise. If a user is loaded the original view is called and
# continues normally.
def sign_in_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('auth.sign_in'))

        return view(**kwargs)

    return wrapped_view


# TODO: Make create account page look better (similar to sign in page)
