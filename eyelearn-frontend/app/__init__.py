from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'user_management.login'
login.login_message = 'Please log in to access this page.'



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    # app.app_context().push()
    # db.create_all()
    migrate.init_app(app, db)
    login.init_app(app)


    from app.user_management import bp as user_management_bp
    app.register_blueprint(user_management_bp)

    from app.user_analytics import bp as user_analytics_bp
    app.register_blueprint(user_analytics_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.speech_recognition import bp as speech_recognition_bp
    app.register_blueprint(speech_recognition_bp)

    from app.image_classification import bp as image_classification_bp
    app.register_blueprint(image_classification_bp)

    from app.handwriting import bp as handwriting_bp
    app.register_blueprint(handwriting_bp)

    from app.doodle import bp as doodle_bp
    app.register_blueprint(doodle_bp)

    from app.tiles import bp as tiles_bp
    app.register_blueprint(tiles_bp)

    from app.everyday_object_classification import bp as everyday_object_classification_bp
    app.register_blueprint(everyday_object_classification_bp)

    from app.create_classifier import bp as create_classifier_bp
    app.register_blueprint(create_classifier_bp)

    return app


from app import models