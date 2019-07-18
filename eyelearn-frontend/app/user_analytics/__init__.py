from flask import Blueprint

bp = Blueprint('user_analytics', __name__)

from app.user_analytics import routes