from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from datetime import datetime  # put this at the top with your imports!
from werkzeug.utils import secure_filename
import os 
from PIL import Image

# Uploading images for thumbnail
THUMB_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads", "thumbs")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(THUMB_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def make_thumbnail(infile, thumbfile):
    size = (150, 150)
    img = Image.open(infile)
    img.thumbnail(size)
    img.save(thumbfile)

bp = Blueprint('main', __name__)
CATEGORIES = ["General", "Technology", "News", "Random"]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/create_thread', methods=['GET', 'POST'])
def create_thread():
    db = current_app.get_db()
    error = None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("description", "").strip()
        category = request.form.get("category", "General").strip()
        if not title or not desc:
            error = "Title and description required."
        elif category not in CATEGORIES:
            error = "Choose a valid category."
        else:
            db.execute(
                "INSERT INTO thread (title, description, category, created_at) VALUES (?, ?, ?, ?)",
                (title, desc, category, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            )
            db.commit()
            return redirect(url_for('main.forums'))
    return render_template("create_thread.html", error=error, categories=CATEGORIES)

@bp.route('/forums')
def forums():
    db = current_app.get_db()
    category = request.args.get('category')
    if category and category in CATEGORIES:
        forums = db.execute(
            "SELECT * FROM thread WHERE category=? ORDER BY is_sticky DESC, created_at DESC", (category,)
        ).fetchall()
    else:
        forums = db.execute(
            "SELECT * FROM thread ORDER BY is_sticky DESC, created_at DESC"
        ).fetchall()
    return render_template('forums.html', forums=forums, categories=CATEGORIES)


@bp.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    db = current_app.get_db()
    forum = db.execute("SELECT * FROM thread WHERE id = ?", (thread_id,)).fetchone()
    posts = db.execute("SELECT * FROM post WHERE thread_id = ?", (thread_id,)).fetchall()
    error = None

    if request.method == 'POST':
        author = request.form.get('author', 'Anonymous')
        content = request.form.get('content', '')
        image = request.files.get('image')
        image_path = thumb_path = None

    if image and allowed_file(image.filename):
        filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{image.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image.save(filepath)
        image_path = f"uploads/{filename}"

        # Create thumbnail
        thumbfile = os.path.join(THUMB_FOLDER, filename)
        make_thumbnail(filepath, thumbfile)
        thumb_path = f"thumbs/{filename}"

    if not content.strip() and not image:
        error = "Content or image required."
    else:
        db.execute(
            "INSERT INTO post (thread_id, author, content, image_path, thumb_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (thread_id, author, content, image_path, thumb_path, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        )
        db.commit()
        return redirect(url_for('main.thread', thread_id=thread_id))


@bp.route('/delete_post/<int:post_id>/<int:thread_id>')
def delete_post(post_id, thread_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    db = current_app.get_db()
    db.execute("DELETE FROM post WHERE id = ?", (post_id,))
    db.commit()
    return redirect(url_for('main.thread', thread_id=thread_id))

@bp.route('/delete_thread/<int:thread_id>')
def delete_thread(thread_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    db = current_app.get_db()
    db.execute("DELETE FROM post WHERE thread_id = ?", (thread_id,))
    db.execute("DELETE FROM thread WHERE id = ?", (thread_id,))
    db.commit()
    return redirect(url_for('main.forums'))

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

@bp.route('/edit_post/<int:post_id>/<int:thread_id>', methods=['GET', 'POST'])
def edit_post(post_id, thread_id):
    db = current_app.get_db()
    post = db.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()
    if not post:
        return redirect(url_for('main.thread', thread_id=thread_id))
    error = None
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            error = "Content required."
        else:
            db.execute("UPDATE post SET content = ? WHERE id = ?", (content, post_id))
            db.commit()
            return redirect(url_for('main.thread', thread_id=thread_id))
    return render_template("edit_post.html", post=post, error=error, thread_id=thread_id)

@bp.route('/edit_thread/<int:thread_id>', methods=['GET', 'POST'])
def edit_thread(thread_id):
    db = current_app.get_db()
    thread = db.execute("SELECT * FROM thread WHERE id = ?", (thread_id,)).fetchone()
    if not thread:
        return redirect(url_for('main.forums'))
    error = None
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not description:
            error = "Title and description required."
        else:
            db.execute("UPDATE thread SET title = ?, description = ? WHERE id = ?", (title, description, thread_id))
            db.commit()
            return redirect(url_for('main.thread', thread_id=thread_id))
    return render_template("edit_thread.html", thread=thread, error=error)

@bp.route('/sticky_thread/<int:thread_id>', methods=['POST'])
def sticky_thread(thread_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    db = current_app.get_db()
    db.execute("UPDATE thread SET is_sticky = 1 WHERE id = ?", (thread_id,))
    db.commit()
    return redirect(url_for('main.thread', thread_id=thread_id))

@bp.route('/unsticky_thread/<int:thread_id>', methods=['POST'])
def unsticky_thread(thread_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    db = current_app.get_db()
    db.execute("UPDATE thread SET is_sticky = 0 WHERE id = ?", (thread_id,))
    db.commit()
    return redirect(url_for('main.thread', thread_id=thread_id))


# SIGN UP DISABLED!
'''
@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    return "Sign up is disabled. Only admin can log in."
'''
