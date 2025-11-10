from flask import render_template, request, flash, redirect, url_for
from app import db
from app.modules.ldap_mod.models import LDAPUsers, LDAPServer

def phonebook_index():
    """
    Главная страница телефонной книги для пользователей
    """
    try:
        # Параметры поиска
        search_query = request.args.get('search', '').strip()
        
        # Базовый запрос
        query = LDAPUsers.query.order_by(LDAPUsers.cn)
        
        # Применяем поиск (если нужно серверный поиск)
        if search_query:
            query = query.filter(
                (LDAPUsers.cn.ilike(f'%{search_query}%')) |
                (LDAPUsers.mail.ilike(f'%{search_query}%')) |
                (LDAPUsers.telephone.ilike(f'%{search_query}%')) |
                (LDAPUsers.title.ilike(f'%{search_query}%')) |
                (LDAPUsers.department.ilike(f'%{search_query}%'))  # Добавляем поиск по отделу
            )
        
        # Получаем контакты
        contacts = query.all()
        
        # Добавляем информацию об организации к каждому контакту
        contacts_with_org = []
        for contact in contacts:
            server = LDAPServer.query.get(contact.server_id)
            # Добавляем organization как атрибут контакта
            contact.organization = server.name if server else 'Неизвестно'
            contacts_with_org.append(contact)
        
        # Получаем уникальные организации для фильтра
        organizations = db.session.query(LDAPServer.name).distinct().filter(
            LDAPServer.name.isnot(None),
            LDAPServer.name != ''
        ).order_by(LDAPServer.name).all()
        
        organizations = [org[0] for org in organizations if org[0]]
        
        return render_template('phonebook/index.html',
                             contacts=contacts_with_org,  # Теперь передаем обычные контакты
                             search_query=search_query,
                             organizations=organizations,
                             total_contacts=len(contacts))
        
    except Exception as e:
        # Упрощенная обработка ошибок
        flash(f'Ошибка загрузки телефонной книги: {e}', 'danger')
        return redirect(url_for('main.index'))  # Перенаправляем на главную

def view_map(server_id, user_id=None):
    """
    Показать карту здания только для просмотра (без возможности редактирования)
    """
    server = LDAPServer.query.get_or_404(server_id)
    
    # Получаем всех пользователей для этого сервера и преобразуем в словари
    users = LDAPUsers.query.filter_by(server_id=server_id).all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'cn': user.cn,
            'coordinates': user.coordinates,
            'title': user.title,
            'department': user.department
        })
    
    # Если указан user_id, находим этого пользователя для подсветки
    highlight_user_data = None
    if user_id:
        user = LDAPUsers.query.get(user_id)
        if user and user.server_id == server_id:
            highlight_user_data = {
                'id': user.id,
                'cn': user.cn,
                'coordinates': user.coordinates,
                'title': user.title,
                'department': user.department
            }
    
    return render_template('phonebook/map_view.html',
                        server=server,
                        users=users_data,
                        highlight_user=highlight_user_data)
