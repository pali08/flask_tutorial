import sqlite3
import click
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types = sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def close_db(e=None):
    db=g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    # close_db sa zavola az sa bude cleanovat po vrateni response
    app.teardown_appcontext(close_db)
    # pridaj command, ktory sa moze volat cez flask command
    app.cli.add_command(init_db_command)
