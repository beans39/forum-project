from flask import Flask, g
import sqlite3
from .routes import bp

DATABASE = 'forum.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'
    app.register_blueprint(bp)
    app.teardown_appcontext(close_db)
    app.get_db = get_db
    return app
