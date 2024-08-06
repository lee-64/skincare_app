import json
import sqlite3 as sl
import click
from flask import current_app, g


# returns a database connection, which is used to execute the commands read from the file
def get_users_db():
    if 'users_db' not in g:
        g.users_db = sl.connect(
            current_app.config['DATABASE'],
            detect_types=sl.PARSE_DECLTYPES
        )
        g.users_db.row_factory = sl.Row  # allows accessing cols by name

    return g.users_db


def close_users_db(e=None):
    users_db = g.pop('users_db', None)

    if users_db is not None:
        users_db.close()


def routine_str_to_list(routine_str):
    if routine_str is not None:
        routine_list = json.loads(routine_str)
        return routine_list
    else:
        return None


def set_routine(username, routine_list):
    routine_json = json.dumps(routine_list)
    users_db = get_users_db()
    users_db.execute(
        'UPDATE users SET routine=? WHERE username=?', (routine_json, username)
    )
    users_db.commit()


def init_users_db():
    users_db = get_users_db()

    # open_resource opens a file relative to the skincare_app package, which is useful since you won’t necessarily know where
    # that location is when deploying the application later
    with current_app.open_resource('schema.sql') as f:
        users_db.executescript(f.read().decode('utf8'))


# click.command() defines a command line command called init-db that calls the init_db function and shows a success
# message to the user
# creates skincare_app.db in the instance folder
@click.command('init-users_db')
def init_users_db_command():
    """Clear the existing data and create new tables."""
    init_users_db()
    click.echo('Initialized the database.')
    # once init-db has been registered with the skincare_app, it can be called using the flask command, similar to the run
    # command: $ flask --app skincare_app run --debug    goes to   flask --app skincare_app init-users_db


def init_app(app):
    app.teardown_appcontext(close_users_db)  # tells Flask to call that function when cleaning up after returning the response
    app.cli.add_command(init_users_db_command)  # adds a new command that can be called with the flask command