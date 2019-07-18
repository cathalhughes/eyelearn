import os
basedir = os.path.abspath(os.path.dirname(__file__))

class TestConfig():
    DEBUG = False
    #TESTING = True
    #LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    USERNAME = "student"
    PASSWORD = "1"

class Config(object):
    # ...
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    print(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_EMAIL_SENDER_NAME = 'Your name'
    USER_EMAIL_SENDER_EMAIL = 'yourname@gmail.com'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'


