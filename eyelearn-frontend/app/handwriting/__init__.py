from flask import Blueprint

bp = Blueprint('handwriting', __name__)

from app.handwriting import routes