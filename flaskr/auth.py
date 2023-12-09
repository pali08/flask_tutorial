import functools

from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

# create new blueprint named auth. __name__ is passed as second argument so bp knows, where it is defined
# '/auth is URL prefix'
bp = Blueprint('auth', __name__, url_prefix='/auth')


# decorator asociates url register with register function
# when flask receivers request to auth/register
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        db = get_db()
        error = None
        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif password != password_confirm:
            error = 'Password does not match.'
        if error is None:
            try:
                db.execute("INSERT INTO user (username, password) VALUES (?, ?)",
                           (username,
                            generate_password_hash(password)
                            )
                           )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                # if no exception occured
                return redirect(url_for("auth.login"))
        # flash stores messages that can be retrieved when rendering template
        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM user where username = ?', (username,)).fetchone()
        if user is None:
            error = 'Incorrect username'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            # when validation succeeds , user id is stored in new session.
            # Data is stored in cookie that is sent to browser
            # and it sends back with subsequent requests. Flask securely signs the data, so it cant be tampered with
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash(error)
    return render_template('auth/login.html')


# registruje fciu ktora bezi pred view fciu bez ohladu na to, ake URL je vyzadovane
# tato fcia konkretne checkne, ci je user id ulozene v session a ak ano, nataha data z DB a ulozi ich v g.user.
# ak nemame user id, alebo user id neexistuje, g.user bude None
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# toto je len dekorator. Zoberie fciu, ktoru obaluje a checkne, ci je uzivatel lognuty - inak ho vrati na login page
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view
