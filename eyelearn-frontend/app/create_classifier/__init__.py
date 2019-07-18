from flask import Blueprint

bp = Blueprint('create_classifier', __name__)

from app.create_classifier import routes