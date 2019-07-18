from flask import Blueprint

bp = Blueprint('tiles', __name__)

from app.tiles import routes