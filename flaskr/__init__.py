import os
from flask import Flask

from flaskr.auth import SIMPLE_CAPTCHA
from flaskr.jinja_custom_filters import replace_whitespace


def create_app(test_config=None):
    # create and configure app
    # __name__ name of current module
    # config files are relative to instance path
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # dev used for development, random value for prod
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite')
    )

    if test_config is None:
        # load instance config, if it exists, when not testing
        # overrides default with stuffs in config.py
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed
        app.config.from_mapping(test_config)
    
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/hello')
    def hello():
        return 'Hello, World!'


    from . import db
    db.init_app(app)
    from . import auth
    # import and register blueprint
    app.register_blueprint(auth.bp)
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')
    app.jinja_env.filters['replace_whitespace'] = replace_whitespace
    app = SIMPLE_CAPTCHA.init_app(app)
    return app
