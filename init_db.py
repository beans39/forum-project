import sqlite3

conn = sqlite3.connect('forum.db')
with open('schema.sql') as f:
    conn.executescript(f.read())
# Add an admin user
from werkzeug.security import generate_password_hash
conn.execute(
    "INSERT INTO user (username, password, is_admin) VALUES (?, ?, ?)",
    ("admin", generate_password_hash("adminpass"), 1)
)
conn.commit()
conn.close()
print("Database initialized! Admin username: admin, password: adminpass")
