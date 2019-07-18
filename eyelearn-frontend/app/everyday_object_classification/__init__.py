from flask import Blueprint

bp = Blueprint('everyday_object_classification', __name__)

from app.everyday_object_classification import routes