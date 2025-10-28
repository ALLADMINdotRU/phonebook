from flask import render_template, request, jsonify
from app import db
from app.modules.ldap_mod.models import LDAPServer, LDAPUsers

def show_map(server_id):
    """Показать карту здания с пользователями"""
    server = LDAPServer.query.get_or_404(server_id)
    # Получаем ВСЕХ пользователей для этого сервера
    all_users = LDAPUsers.query.filter_by(server_id=server_id).all()
    return render_template('map/admin.html', server=server, users=all_users)

def update_user_coordinates(user_id):
    """Обновить координаты пользователя"""
    user = LDAPUsers.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'coordinates' in data:
        user.coordinates = data['coordinates']
        user.is_on_map = True if data['coordinates'] else False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Координаты обновлены'})
    
    return jsonify({'success': False, 'message': 'Не указаны координаты'}), 400

def get_users_for_map(server_id):
    """Получить список пользователей для отображения на карте"""
    server = LDAPServer.query.get_or_404(server_id)
    
    users = LDAPUsers.query.filter_by(server_id=server_id).all()
    users_data = []
    
    for user in users:
        users_data.append({
            'id': user.id,
            'name': user.cn,
            'email': user.mail,
            'phone': user.telephone,
            'title': user.title,
            'department': user.department,
            'coordinates': user.coordinates,
            'is_on_map': user.is_on_map
        })
    
    return jsonify(users_data)

def remove_from_map(user_id):
    """Убрать пользователя с карты"""
    user = LDAPUsers.query.get_or_404(user_id)
    user.coordinates = None
    user.is_on_map = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'Пользователь удален с карты'})

