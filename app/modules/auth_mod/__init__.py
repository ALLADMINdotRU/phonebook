from flask import Blueprint
from . import views


# Создание Blueprint для модуля карты
bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates', static_folder='static')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    return views.login()


@bp.route('/logout', methods=['GET'])
def logout():
    return views.logout()