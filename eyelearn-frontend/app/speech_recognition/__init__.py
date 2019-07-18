from flask import Blueprint

bp = Blueprint('speech_recognition', __name__)

from app.speech_recognition import routes