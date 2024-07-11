import sqlite3 as sl
import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sl.connect(
            current_app.config['DATABASE'],
            detect_types=sl.PARSE_DECLTYPES
        )
        g.db.row_factory = sl.Row  # allows accessing cols by name

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()  # returns a database connection, which is used to execute the commands read from the file

    # open_resource opens a file relative to the flaskr package, which is useful since you won’t necessarily know where
    # that location is when deploying the application later
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


# click.command() defines a command line command called init-db that calls the init_db function and shows a success
# message to the user
@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')
    # once init-db has been registered with the app, it can be called using the flask command, similar to the run
    # command: $ flask --app flaskr run --debug


def init_app(app):
    app.teardown_appcontext(close_db)  # tells Flask to call that function when cleaning up after returning the response
    app.cli.add_command(init_db_command)  # adds a new command that can be called with the flask command