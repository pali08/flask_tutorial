import functools

from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app)

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from flask_simple_captcha import CAPTCHA
YOUR_CONFIG = {
    'SECRET_CAPTCHA_KEY': 'LONG_KEY',
    'CAPTCHA_LENGTH': 6,
    'CAPTCHA_DIGITS': False,
    'EXPIRE_SECONDS': 600,
}
SIMPLE_CAPTCHA = CAPTCHA(config=YOUR_CONFIG)
CAPTCHA_TEST_MODE = True

# create new blueprint named auth. __name__ is passed as second argument so bp knows, where it is defined
# '/auth is URL prefix'
bp = Blueprint('auth', __name__, url_prefix='/auth')


# decorator asociates url register with register function
# when flask receivers request to auth/register
@bp.route('/register', methods=('GET', 'POST'))
def register():
    new_captcha_dict = SIMPLE_CAPTCHA.create()
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
        c_hash = request.form.get('captcha-hash')
        c_text = request.form.get('captcha-text')
        # not sure, what is the best way to automate captcha testing, so we currently avoid captcha testing
        if not current_app.config['TESTING']:
            if not SIMPLE_CAPTCHA.verify(c_text, c_hash):
                error = 'Captcha verification failed'
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
    return render_template('auth/register.html', captcha=new_captcha_dict)


# toto je len dekorator. Zoberie fciu, ktoru obaluje a checkne, ci je uzivatel lognuty - inak ho vrati na login page
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


@bp.route('/user_settings', methods=('GET', 'POST'))
@login_required
def user_settings():
    if request.method == 'POST':
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        db = get_db()
        error = None
        if not password:
            error = 'Password is required'
        elif password != password_confirm:
            error = 'Password does not match.'
        if error is None:
            db.execute("UPDATE user SET password = ? WHERE id = ?;",
                       (generate_password_hash(password), g.user['id']
                        )
                       )
            db.commit()
            # if no exception occured
            session.clear()
            return redirect(url_for("auth.login"))
        # flash stores messages that can be retrieved when rendering template
        flash(error)
    return render_template('auth/user_settings.html')


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


