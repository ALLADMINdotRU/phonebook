from flask import Blueprint
from app.modules.auth_mod.decorators import login_required

# Создание Blueprint для модуля карты
bp = Blueprint('map', __name__, url_prefix='/map', template_folder='templates', static_folder='static')

from . import views
from .views import show_map, update_user_coordinates, get_users_for_map, remove_from_map

# Регистрация маршрутов
bp.add_url_rule('/<int:server_id>', 'show_map', login_required(show_map), methods=['GET'])
bp.add_url_rule('/update_coordinates/<int:user_id>', 'update_user_coordinates', login_required(update_user_coordinates), methods=['POST'])
bp.add_url_rule('/users/<int:server_id>', 'get_users_for_map', login_required(get_users_for_map), methods=['GET'])
bp.add_url_rule('/remove/<int:user_id>', 'remove_from_map', login_required(remove_from_map), methods=['POST'])
