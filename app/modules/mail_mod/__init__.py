from flask import Blueprint
from app.modules.auth_mod.decorators import login_required

bp = Blueprint('mail', __name__, url_prefix='/mail', template_folder='templates', static_folder='static')
