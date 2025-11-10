from flask import Blueprint


bp = Blueprint('ldap', __name__, url_prefix='/ldap', template_folder='templates', static_folder='static')

# Импорт views после создания Blueprint
from . import views
from .views import quick_add_contact
from .views import quick_update_contact
from .views import get_building_plan
from app.modules.auth_mod.decorators import login_required

# вывод списка серверов
@bp.route('/servers')
@login_required  
def list_ldap_servers():
    return views.list_ldap_servers()

# Добавление сервера

@bp.route('/servers/add', methods=['GET', 'POST'])
@login_required  
def add_ldap_server():
    return views.add_ldap_server()

# редактировать сервер
@bp.route('/servers/<int:server_id>/edit', methods=['GET', 'POST'])
@login_required 
def edit_ldap_server(server_id):
    return views.edit_ldap_server(server_id)

@bp.route('/server/<int:server_id>/delete', methods=['POST'])
@login_required 
def delete_ldap_server(server_id):
    return views.delete_ldap_server(server_id)

@bp.route('/test-connection', methods=['POST'])
@login_required 
def test_ldap_connection():
    return views.test_ldap_connection()


@bp.route('/<int:server_id>/users')
@login_required 
def list_ldap_contacts(server_id):
    return views.list_ldap_contacts(server_id)

@bp.route('/save-selected', methods=['POST'])
@login_required 
def save_selected_contacts():
    return views.save_selected_contacts()

@bp.route('/saved-users/<int:server_id>')
@login_required 
def show_list_saved_contacts(server_id):
    return views.show_list_saved_contacts(server_id)

@bp.route('/saved-users/delete/<int:user_id>', methods=['POST'])
@login_required 
def delete_saved_contact(user_id):
    return views.delete_saved_contact(user_id)

@bp.route('/saved-users/edit/<int:user_id>', methods=['GET', 'POST']) 
@login_required 
def edit_saved_contact(user_id):
    return views.edit_saved_contact(user_id)

@bp.route('/add-user/<int:server_id>', methods=['GET', 'POST'])
@login_required 
def add_new_contact(server_id):
    return views.add_new_contact(server_id)

@bp.route('/sync_server/<int:server_id>', methods=['POST'])
@login_required 
def sync_server(server_id):
    return views.sync_server(server_id)

@bp.route('/test-smtp', methods=['POST'])
@login_required 
def test_smtp_connection():
    return views.test_smtp_connection()

bp.add_url_rule('/servers/<int:server_id>/quick-add/<string:contact_guid>', 
                'quick_add_contact', login_required(quick_add_contact), methods=['GET'])

bp.add_url_rule('/servers/<int:server_id>/quick-update/<string:contact_guid>', 
                'quick_update_contact', login_required(quick_update_contact), methods=['GET'])

@bp.route('/server/<int:id>/building_plan')  # ← ДОБАВЬТЕ @
def get_building_plan(id):
    return views.get_building_plan(id)

