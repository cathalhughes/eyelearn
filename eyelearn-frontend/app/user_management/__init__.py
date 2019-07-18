from flask import Blueprint

bp = Blueprint('user_management', __name__)

from app.user_management import routes