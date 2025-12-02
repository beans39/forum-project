import sqlite3
from werkzeug.security import generate_password_hash
from flask import Flask
# SQLite 
conn = sqlite3.connect('forum.db')
with open('schema.sql') as f:
    conn.executescript(f.read())


# Add an admin user
conn.execute(
    "INSERT INTO user (username, password, is_admin) VALUES (?, ?, ?)",
    ("admin", generate_password_hash("adminpass"), 1)
)
conn.commit()
conn.close()
print("Database initialized! Admin username: admin, password: adminpass")



def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    # Import and register your blueprints here
    from .routes import bp
    app.register_blueprint(bp)
    return app