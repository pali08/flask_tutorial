from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, likes'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC').fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('INSERT INTO post (title, body, author_id)'
                       ' VALUES (?, ?, ?)', (title, body, g.user['id']))
            db.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute('SELECT p.id, title, body, created, author_id, username, likes'
                            ' FROM post p JOIN user u ON p.author_id = u.id'
                            ' WHERE p.id = ?', (id,)).fetchone()
    if post is None:
        abort(404, f"Post id {id} does not exist.")
    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('UPDATE post SET title = ?, body = ?'
                       ' WHERE id = ?', (title, body, id))
            db.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/view', methods=('GET', 'POST'))
def view(id):
    post = get_post(id, check_author=False)
    db = get_db()
    if g.user:
        post_has_like_actual_user = db.execute('SELECT has_like FROM post_user_like WHERE user_id = ? and post_id = ?',
                                               (g.user['id'], id)).fetchone()
        if request.method == 'POST':
            if post_has_like_actual_user is None:
                print('post has like is none')
                db.execute('INSERT INTO post_user_like (user_id, post_id, has_like) VALUES (?, ?, ?)', (g.user['id'], id, 1))
                db.execute('UPDATE post SET likes = ? WHERE id = ?', (post['likes'] + 1, id))
            elif post_has_like_actual_user[0] == 0:
                print(f'post has like should be 0, is: {post_has_like_actual_user}')
                db.execute('UPDATE post_user_like SET has_like = ? WHERE post_id = ? AND user_id = ?', (1, id, g.user['id']))
                db.execute('UPDATE post SET likes = ? WHERE id = ?', (post['likes'] + 1, id))
            elif post_has_like_actual_user[0] == 1:
                print(f'post has like should be 1, is: {post_has_like_actual_user}')
                db.execute('UPDATE post_user_like SET  has_like = ? WHERE post_id = ? AND user_id = ?', (0, id, g.user['id']))
                db.execute('UPDATE post SET likes = ? WHERE id = ?', (post['likes'] - 1, id))
            db.commit()
            return redirect(url_for('blog.view', id=id))
        # db.commit()
        # return redirect(url_for('blog.view', id=id))
    else:
        post_has_like_actual_user = None
    return render_template('blog/view.html', post=post, post_has_like_actual_user=post_has_like_actual_user)
