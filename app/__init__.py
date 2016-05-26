from flask import Flask
from flask.ext.bootstrap import Bootstrap

bootstrap = Bootstrap()

def create_app():
    app = Flask(__name__)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    bootstrap.init_app(app)
    
    return app