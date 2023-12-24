import pytest
from flask import g, session
from flaskr.db import get_db


def test_register(client, app):
    assert client.get('/auth/register').status_code == 200
    response = client.post('/auth/register', data={'username': 'a', 'password': 'a', 'password_confirm': 'a'})
    assert response.headers['Location'] == '/auth/login'
    with app.app_context():
        assert get_db().execute("SELECT * FROM user WHERE username = 'a'").fetchone() is not None


@pytest.mark.parametrize(('username', 'password', 'message'), (
        ('', '', b'Username is required'),
        ('a', '', b'Password is required'),
        ('test', 'test', b'already registered'),
))
def test_register_validate_input(client, username, password, message):
    response = client.post('/auth/register',
                           data={'username': username, 'password': password, 'password_confirm': password})
    # data contains body of response as bytes
    assert message in response.data


def test_login(client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers['Location'] == '/'
    with client:
        # Using client in a with block allows accessing context variables
        # such as session after the response is returned.
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'


def test_change_password(client, auth):
    auth.login()
    assert client.get('/auth/user_settings').status_code == 200
    client.post('/auth/user_settings', data={'password': 'a', 'password_confirm': 'a'})
    response = client.post('/auth/login',
                           data={'username': 'test', 'password': 'a'})
    assert response.headers['Location'] == '/'
    with client:
        # Using client in a with block allows accessing context variables
        # such as session after the response is returned.
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(
    ('username', 'password', 'message'),
    (
            ('a', 'test', b'Incorrect username'),
            ('test', 'a', b'Incorrect password')
    )
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()
    with client:
        auth.logout()
        assert 'user_id' not in session
