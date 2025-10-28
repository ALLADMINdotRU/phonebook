from flask import Blueprint

# Создание Blueprint для публичной телефонной книги
bp = Blueprint('phonebook', __name__, url_prefix='/phonebook', template_folder='templates', static_folder='static')

# Импорт views должен быть после создания blueprint чтобы избежать циклических импортов
from . import views

@bp.route('/phonebook_index')
def phonebook_index():
    return views.phonebook_index()

@bp.route('/map/<int:server_id>')
@bp.route('/map/<int:server_id>/<int:user_id>')
def view_map(server_id, user_id=None):
    return views.view_map(server_id, user_id)
