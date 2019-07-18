from flask import Blueprint

bp = Blueprint('doodle', __name__)

from app.doodle import routes