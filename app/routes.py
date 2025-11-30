from flask import Blueprint, render_template, request, redirect, url_for, session, current_app

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/forums')
def forums():
    db = current_app.get_db()
    forums = db.execute("SELECT * FROM thread").fetchall()
    return render_template('forums.html', forums=forums)

@bp.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    db = current_app.get_db()
    forum = db.execute("SELECT * FROM thread WHERE id = ?", (thread_id,)).fetchone()
    posts = db.execute("SELECT * FROM post WHERE thread_id = ?", (thread_id,)).fetchall()
    error = None

    if request.method == 'POST':
        author = request.form.get('author', 'Anonymous')
        content = request.form.get('content', '')
        if not content.strip():
            error = "Content required."
        else:
            db.execute(
                "INSERT INTO post (thread_id, author, content) VALUES (?, ?, ?)",
                (thread_id, author, content)
            )
            db.commit()
            return redirect(url_for('main.thread', thread_id=thread_id))
    return render_template('thread.html', forum=forum, posts=posts, error=error)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = current_app.get_db()
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()
        if not user:
            error = "Invalid username or password."
        elif not user['is_admin']:
            error = "Only admin can log in."
        else:
            from werkzeug.security import check_password_hash
            if not check_password_hash(user['password'], password):
                error = "Invalid username or password."
            else:
                session['user'] = username
                session['is_admin'] = True
                return redirect(url_for('main.forums'))
    return render_template('login.html', error=error)

@bp.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('is_admin', None)
    return redirect(url_for('main.index'))

# SIGN UP DISABLED!
'''
@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    return "Sign up is disabled. Only admin can log in."
'''
