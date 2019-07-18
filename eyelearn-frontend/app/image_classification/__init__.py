from flask import Blueprint

bp = Blueprint('image_classification', __name__)

from app.image_classification import routes