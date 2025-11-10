from flask import render_template, redirect, url_for, flash, request
from app import db
from .forms import LDAPServerForm
from .models import LDAPServer, LDAPUsers
from .ldap_class import LDAPManager
from app import cache                       # Импортируем глобальный кеш
from flask import session
from datetime import datetime, timedelta
from flask import current_app
from flask import Response
import base64


def utc_to_local(utc_dt):
    """Конвертирует UTC datetime в локальное время используя смещение из конфига"""
    if not utc_dt:
        return utc_dt
    
    # Получаем смещение из конфига приложения
    offset_hours = current_app.config.get('TIME_ZONE_OFFSET', 0)
    
    # Просто прибавляем смещение (часы)
    return utc_dt + timedelta(hours=offset_hours)

def local_to_utc(local_dt):
    """Конвертирует локальное время в UTC используя смещение из конфига"""
    if not local_dt:
        return local_dt
    
    # Получаем смещение из конфига
    offset_hours = current_app.config.get('TIME_ZONE_OFFSET', 0)
    
    # Вычитаем смещение (часы)
    return local_dt - timedelta(hours=offset_hours)

# Также можно добавить функцию для форматирования времени
def format_local_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Форматирует datetime в локальное время"""
    if not dt:
        return ""
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)



def list_ldap_servers():
    """
    Отображает список всех LDAP серверов
    """
    servers = LDAPServer.query.order_by(LDAPServer.name).all()

    # Конвертируем время для каждого сервера
    for server in servers:
        if server.last_sync:
            server.last_sync_local = utc_to_local(server.last_sync)
        else:
            server.last_sync_local = None

    return render_template('list_servers.html', servers=servers)


def add_ldap_server():
    """
    Обрабатывает добавление нового LDAP сервера
    """
    # Создание экземпляра формы
    form = LDAPServerForm()
    
    # Проверка отправки и валидации формы
    if form.validate_on_submit():
        try:
            # Создание нового объекта сервера
            server = LDAPServer(
                name=form.name.data,
                host=form.host.data,
                port=form.port.data,
                use_ssl=form.use_ssl.data,
                base_dn=form.base_dn.data,
                bind_login=form.bind_login.data,
                bind_password=form.bind_password.data,
                description=form.description.data,
                search_filter=form.search_filter.data,
                is_active=form.is_active.data,

                last_sync = local_to_utc(datetime.now()),  # Автоматически устанавливаем текущее время  и Конвертируем время  в UTC

                # Новые SMTP поля
                smtp_host=form.smtp_host.data,
                smtp_port=form.smtp_port.data,
                smtp_username=form.smtp_username.data,
                smtp_password=form.smtp_password.data,
                smtp_use_tls=form.smtp_use_tls.data,
                smtp_use_ssl=form.smtp_use_ssl.data,
                smtp_from_email=form.smtp_from_email.data,
                smtp_to_email=form.smtp_to_email.data,
                smtp_is_active=form.smtp_is_active.data,

                # Новые поля уведомлений
                notify_on_add=form.notify_on_add.data,
                notify_on_update=form.notify_on_update.data
            )
                
            # Обработка загрузки плана здания
            if form.building_plan.data:
                plan_file = form.building_plan.data
                server.building_plan_data = plan_file.read()
                server.building_plan_filename = plan_file.filename
                server.building_plan_mimetype = plan_file.content_type
                
            # Сохранение в БД
            db.session.add(server)
            db.session.commit()
            flash('LDAP сервер успешно добавлен', 'success')
            return redirect(url_for('ldap.list_ldap_servers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении сервера: {str(e)}', 'danger')
            
    # Отображение формы
    return render_template('add_server.html', form=form)

# редактировать существующий LDAP сервер
def edit_ldap_server(server_id):
    """
    Обрабатывает редактирование существующего LDAP сервера
    """
    server = LDAPServer.query.get_or_404(server_id)                                 # получаем данные сервера по его ID
    form = LDAPServerForm()                                                         # Создаем форму БЕЗ предзаполнения obj=server

    # Для GET запроса - предзаполняем форму конвертированным временем
    if request.method == 'GET':
        form = LDAPServerForm(obj=server)                                           # заполняем форму
        # Конвертируем время только для отображения
        if server.last_sync:
            form.last_sync.data = utc_to_local(server.last_sync)                    # вставляем в форму время + время зоны


    if form.validate_on_submit():
        try:
            original_password = server.bind_password                                # Сохраняем оригинальный пароль перед обновлением
            original_smtp_password = server.smtp_password                           # Сохраняем оригинальный SMTP пароль

            # Ручное копирование полей вместо populate_obj
            server.name = form.name.data
            server.host = form.host.data
            server.port = form.port.data
            server.base_dn = form.base_dn.data
            server.search_filter = form.search_filter.data
            server.use_ssl = form.use_ssl.data
            server.bind_login = form.bind_login.data
            server.is_active = form.is_active.data
            server.description = form.description.data

            # Новые SMTP поля
            server.smtp_host = form.smtp_host.data
            server.smtp_port = form.smtp_port.data
            server.smtp_username = form.smtp_username.data
            server.smtp_use_tls = form.smtp_use_tls.data
            server.smtp_use_ssl = form.smtp_use_ssl.data
            server.smtp_from_email = form.smtp_from_email.data
            server.smtp_to_email = form.smtp_to_email.data
            server.smtp_is_active = form.smtp_is_active.data

            # поля уведомлений
            server.notify_on_add = form.notify_on_add.data
            server.notify_on_update = form.notify_on_update.data

            # Обновление плана здания (если загружен новый)
            if form.building_plan.data:
                plan_file = form.building_plan.data
                server.building_plan_data = plan_file.read()
                server.building_plan_filename = plan_file.filename
                server.building_plan_mimetype = plan_file.content_type

            # Конвертируем время обратно в UTC
            if form.last_sync.data:
                server.last_sync = local_to_utc(form.last_sync.data)
            else:
                server.last_sync = None

            # Пароль обрабатываем отдельно
            if form.bind_password.data:
                server.bind_password = form.bind_password.data
            else:
                server.bind_password = original_password

            # SMTP пароль обрабатываем отдельно
            if form.smtp_password.data:
                server.smtp_password = form.smtp_password.data
            else:
                server.smtp_password = original_smtp_password

            db.session.commit()
            flash('Изменения сохранены', 'success')
            return redirect(url_for('ldap.list_ldap_servers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

    return render_template('edit_server.html', form=form, server=server)

# удаление сервера LDAP из списка
def delete_ldap_server(server_id):
    server = LDAPServer.query.get_or_404(server_id)

    try:
        db.session.delete(server)
        db.session.commit()
        flash('Сервер успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    
    return redirect(url_for('ldap.list_ldap_servers'))


"""
Тестирует подключение к LDAP серверу по его ID из БД
"""
def test_ldap_connection():
    server_id = request.form.get('server_id')
    if not server_id:
        flash('Не указан ID сервера', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    server = LDAPServer.query.get(server_id)
    if not server:
        flash('Сервер не найден', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    try:
        # Создаем LDAP менеджер с настройками из БД
        ldap = LDAPManager(
            server_url=f"{server.host}:{server.port}",
            user=server.bind_login,
            password=server.bind_password,
            base_dn=server.base_dn,
            use_ssl=server.use_ssl
        )
        
        # Пытаемся подключиться
        success, message = ldap.connect()
        
        if success:
            flash(f'Подключение к серверу "{server.name}" успешно!', 'success')
            ldap.disconnect()
        else:
            flash(f'Ошибка подключения к "{server.name}": {message}', 'danger')
            
    except Exception as e:
        flash(f'Ошибка проверки "{server.name}": {str(e)}', 'danger')
    
    return redirect(url_for('ldap.list_ldap_servers'))


"""
Тестирует SMTP подключение отправкой тестового письма
"""
def test_smtp_connection():

    server_id = request.form.get('server_id')
    if not server_id:
        flash('Не указан ID сервера', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    server = LDAPServer.query.get(server_id)
    if not server:
        flash('Сервер не найден', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    # Проверяем, активированы ли SMTP настройки
    if not server.smtp_is_active:
        flash('SMTP настройки не активированы для этого сервера', 'warning')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    # Проверяем, указан ли email для уведомлений
    if not server.smtp_to_email:
        flash('Не указан email для отправки тестового письма', 'warning')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    try:
        # Используем наш почтовый сервис
        from app.modules.mail_mod.mail_service import MailService
        
        # Создаем конфигурацию SMTP из настроек сервера
        smtp_config = server.get_smtp_config()
        if not smtp_config:
            flash('Не удалось получить SMTP конфигурацию', 'danger')
            return redirect(url_for('ldap.list_ldap_servers'))
        
        # Создаем сервис и отправляем тестовое письмо
        mail_service = MailService(smtp_config)
        success, message = mail_service.send_email(
            to_email=server.smtp_to_email,
            subject='Тестовое письмо от PHONEBOOK сервиса',
            body=f'''Это тестовое письмо от справочника "{server.name}".

Проверка SMTP настроек прошла успешно!

Настройки SMTP:
- Хост: {server.smtp_host}
- Порт: {server.smtp_port}
- Пользователь: {server.smtp_username}
- TLS: {'Да' if server.smtp_use_tls else 'Нет'}
- SSL: {'Да' if server.smtp_use_ssl else 'Нет'}

Время отправки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
''',
            from_email=server.smtp_from_email or server.smtp_username
        )
        
        if success:
            flash(f'Тестовое письмо отправлено на {server.smtp_to_email}', 'success')
        else:
            flash(f'Ошибка отправки: {message}', 'danger')
            
    except Exception as e:
        flash(f'Ошибка SMTP: {str(e)}', 'danger')
    
    return redirect(url_for('ldap.list_ldap_servers'))



# получаем список пользователей LDAP
def list_ldap_contacts(server_id):
    server = LDAPServer.query.get_or_404(server_id)
    cache_key = f'ldap_users_{session.sid}'                                                             # уникальный  ID сессии

    ldap = LDAPManager(                                                                                 # подключаемся к LDAP
        server_url=f"{server.host}:{server.port}",
        user=server.bind_login,
        password=server.bind_password,
        base_dn=server.base_dn,
        use_ssl=server.use_ssl  # Добавляем параметр SSL
    )

    success, message = ldap.connect()                                                                   # подключаемся к LDAP серверу
    if not success:                                                                                     # если не удачно подключились
        flash(message, 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    try:
        users = ldap.get_all_users(search_filter=server.search_filter)                                  # получаем список пользователей LDAP , предварительно передавая парамтер фильтра
        users = sorted(users, key=lambda x: x.get('cn', '').lower())                                    # После получения users из LDAP добавляем сортировку
        cache.set(cache_key, users)                                                                     # Сохранение полученный список  LDAP пользователей в кеш

        saved_users = LDAPUsers.query.filter_by(server_id=server_id).all()                              # получаем список пользователей из БД
        saved_guids = {user.guid for user in saved_users}                                               # создвем множество из guid элементов
    
        return render_template('list_ldap_contacts.html', users=users, server_id=server_id, saved_guids=saved_guids)   # прорисуем список пользователей LDAP
    except Exception as e:
        flash(f"Ошибка получения данных: {str(e)}", 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    finally:
        ldap.disconnect()


"""
Обработчик для сохранения выбранных пользователей LDAP в локальную БД.
Получает список GUID выбранных пользователей из формы и сохраняет их данные.
"""
def save_selected_contacts():
    # Импорт необходимых моделей внутри функции для избежания циклических импортов
    from app.modules.ldap_mod.models import LDAPUsers
    #from app import db

    try:
        # 1. Получаем ID текущего LDAP сервера из скрытого поля формы
        server_id = request.form.get('server_id')
        if not server_id:
            flash('Ошибка: не указан сервер LDAP', 'error')
            return redirect(url_for('ldap.list_ldap_contacts'))
        
        # 2. Получаем список GUID выбранных пользователей из формы
        selected_guids = request.form.getlist('selected_users')
        if not selected_guids:
            flash('Не выбрано ни одного пользователя', 'warning')
            return redirect(url_for('ldap.list_ldap_contacts', server_id=server_id))
        
        # 3. Получаем кешированные данные пользователей из сессии
        ldap_users_cache = cache.get(f'ldap_users_{session.sid}')
        if not ldap_users_cache:
            flash('Данные пользователей устарели, выполните новый поиск', 'error')
            return redirect(url_for('ldap.list_ldap_contacts', server_id=server_id))
        
        # 4. Обрабатываем каждого выбранного пользователя
        for guid in selected_guids:            
            user_data = next((u for u in ldap_users_cache if u.get('guid') == guid), None)  # Находим данные пользователя в кеше
            if not user_data:
                continue  # Пропускаем если данные не найдены

            existing_user = LDAPUsers.query.filter_by(guid=guid).first()                    # Проверяем существует ли пользователь в БД

            if existing_user:                                                               # Обновляем существующую запись
                existing_user.cn =          user_data.get('cn', existing_user.cn)
                existing_user.mail =        user_data.get('mail', existing_user.mail)
                existing_user.telephone =   user_data.get('telephone', existing_user.telephone)
                existing_user.mobile =      user_data.get('mobile', existing_user.mobile)
                existing_user.title =       user_data.get('title', existing_user.title)
                existing_user.department =  user_data.get('department', existing_user.department)
                existing_user.photo =       user_data.get('photo', existing_user.photo)
                existing_user.server_id =   server_id
            else:
                new_user = LDAPUsers(                                                       # Создаем новую запись
                    guid=guid,
                    server_id=server_id,
                    cn=user_data.get('cn', ''),
                    mail=user_data.get('mail'),
                    telephone=user_data.get('telephone'),
                    mobile=user_data.get('mobile'),
                    title=user_data.get('title'),
                    department=user_data.get('department'),
                    photo=user_data.get('photo')
                )
                db.session.add(new_user)
        db.session.commit()                                                                 # Фиксируем изменения в БД
        flash(f'Успешно сохранено/обновленно {len(selected_guids)} пользователей', 'success')
    
    except Exception as e:                                                                  # Обработка ошибок
        db.session.rollback()
        flash(f'Ошибка при сохранении: {str(e)}', 'error')        

    return redirect(url_for('ldap.list_ldap_contacts', server_id=server_id))                   # Перенаправляем обратно к списку пользователей

"""Показать пользователей, сохраненных в БД для конкретного сервера"""
def show_list_saved_contacts(server_id):
    server = LDAPServer.query.get_or_404(server_id)

    saved_users = LDAPUsers.query.filter_by(server_id=server_id).order_by(LDAPUsers.cn).all()  # получаем список пользователей из БД
    
    return render_template('list_saved_contacts.html', users=saved_users, server=server)


"""Удаление сохраненного пользователя из БД"""
def delete_saved_contact(user_id):
    user = LDAPUsers.query.get_or_404(user_id)
    server_id = user.server_id                                                              # сохраняем server_id для редиректа

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user.cn} успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')

    return redirect(url_for('ldap.show_list_saved_contacts', server_id=server_id))


"""Редактирование сохраненного пользователя"""
def edit_saved_contact(user_id):    
    user = LDAPUsers.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # Обновляем поля из формы
            guid_input = request.form.get('guid', '').strip()
            user.guid = guid_input if guid_input else None
            user.cn = request.form.get('cn', user.cn)
            user.mail = request.form.get('mail', user.mail)
            user.telephone = request.form.get('telephone', user.telephone)
            user.mobile = request.form.get('mobile', user.mobile)
            user.title = request.form.get('title', user.title)
            user.department = request.form.get('department', user.department)

            # Обработка удаления фотографии
            if request.form.get('remove_photo'):
                user.photo = None  # Удаляем фото если чекбокс отмечен
            # Обработка фотографии
            if 'photo' in request.files:                                                    # Проверяем, был ли передан файл с именем 'photo' в форме
                photo_file = request.files['photo']                                         # Получаем объект файла из запроса
                if photo_file and photo_file.filename:                                      # Проверяем, что файл существует и имеет имя (не пустой)
                    user.photo = base64.b64encode(photo_file.read()).decode('utf-8')        # Конвертируем файл в base64

            db.session.commit()
            flash('Данные пользователя обновлены', 'success')
            return redirect(url_for('ldap.show_list_saved_contacts', server_id=user.server_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'danger')
    
    # Для GET запроса показываем форму редактирования
    return render_template('edit_contact.html', user=user)


#Добавление нового контакта вручную
def add_new_contact(server_id=None):
    target_server_id = server_id or request.form.get('server_id')               # Если server_id передан, используем его, иначе получаем из формы

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            server_id = request.form.get('server_id')
            cn = request.form.get('cn')
            mail = request.form.get('mail')
            telephone = request.form.get('telephone')
            mobile = request.form.get('mobile')
            title = request.form.get('title')
            department = request.form.get('department')
                        
            # Создаем нового пользователя
            new_user = LDAPUsers(
                guid=None,
                server_id=target_server_id,
                cn=cn,
                mail=mail,
                telephone=telephone,
                mobile=mobile,
                title=title,
                department=department
            )
            
            # Обработка загрузки фотографии
            if 'photo' in request.files:
                photo_file = request.files['photo']
                if photo_file and photo_file.filename:
                    # Конвертируем файл в base64
                    new_user.photo = base64.b64encode(photo_file.read()).decode('utf-8')
            
            # Сохраняем в БД
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Пользователь {cn} успешно добавлен', 'success')
            return redirect(url_for('ldap.show_list_saved_contacts', server_id=target_server_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении пользователя: {str(e)}', 'danger')
            return render_template('add_contact.html', server_id=target_server_id)
    
    # Для GET запроса показываем форму добавления
    if not target_server_id:
        # Если server_id не указан, показываем список серверов
        servers = LDAPServer.query.all()
        redirect (url_for('ldap.list_ldap_servers'))
    else:
        # Если server_id указан, используем его
        return render_template('add_contact.html', server_id=target_server_id)


"""Ручная синхронизация конкретного сервера"""
def sync_server(server_id):
    success, message = sync_ldap_contacts(server_id)
    if success:
        flash(f'Синхронизация завершена: {message}', 'success')
    else:
        flash(f'Ошибка синхронизации: {message}', 'danger')
    return redirect(url_for('ldap.list_ldap_servers'))


"""
Синхронизирует контакты между LDAP и локальной БД
Проверяет новые контакты и обновления существующих
"""
def sync_ldap_contacts(server_id):
    server = LDAPServer.query.get_or_404(server_id)                                                     # получаем данные по серверу из БД по его ID

    ldap = LDAPManager(                                                                                 # создаем объект LDAP
        server_url=f"{server.host}:{server.port}",
        user=server.bind_login,
        password=server.bind_password,
        base_dn=server.base_dn,
        use_ssl=server.use_ssl                                                                          # Добавляем параметр SSL
    )

    success, message = ldap.connect()                                                                   # Подключаемся к серверу LDAP

    if not success:                                                                                     # неудачно подключились выхоидм
        return False, message
    
    try:
        ldap_users = ldap.get_all_users(search_filter=server.search_filter)                             # Получаем всех пользователей из LDAP  по фильтру

        db_users = {user.guid: user for user in LDAPUsers.query.filter_by(server_id=server_id).filter(  # Генерируем словарь всех пользователей из БД у которых есть GUID для этого сервера  исключае пустые строки
            LDAPUsers.guid.isnot(None),             # guid не NULL
            LDAPUsers.guid != ''                    # guid не пустая строка
        ).all()}                                                                                        

        new_users = 0
        updated_users = 0
        deleted_users = 0
        new_contacts = []                                                                               # Список для хранения новых контактов для уведомлений
        updated_contacts = []                                                                           # Для хранения информации об измененных контактах


        # Собираем GUID всех пользователей из LDAP
        ldap_guids = set()
        for ldap_user in ldap_users:                                                                    # Обрабатываем каждого пользователя из LDAP
            guid = ldap_user.get('guid')
            if guid:
                ldap_guids.add(guid)

        # Удаляем пользователей, которых нет в LDAP
        for guid in db_users:
            db_user = db_users[guid]
            if guid not in ldap_guids:
                db.session.delete(db_user)
                deleted_users += 1

        # Обрабатываем каждого пользователя из LDAP
        for ldap_user in ldap_users:                                                                    # Обрабатываем каждого пользователя из LDAP
            guid = ldap_user.get('guid')
            if not guid:
                continue

            # Получаем временные метки из LDAP (не сохраняем в БД)
            when_created = ldap_user.get('when_created')
            when_changed = ldap_user.get('when_changed')

            if guid in db_users:                                                                        # находим пользоваться в LDAP по guid из БД 
                db_user = db_users[guid]                                                                # обновляем данные пользователя
                if (_user_data_changed(db_user, ldap_user)) and (when_changed is None or when_changed > server.last_sync):   # Обновляем только если контакт изменился после последней синхронизации
                    if server.notify_on_update:                                                         # если стоит крыжик уведомлять об изменениях контакта
                        changes = _get_changes_dict(db_user, ldap_user) 
                        updated_contacts.append({
                            'guid': guid,
                            'cn': ldap_user.get('cn', ''),
                            'changes': changes
                        })
                    else:                                                                               # Автоматическое обновление
                        _update_user_from_ldap(db_user, ldap_user)
                        updated_users += 1
            else:                                                                                       # тут идет логика добавления пользователя из LDAP в БД
                if when_created is None or when_created > server.last_sync:                             # если врем создания больше времени синхронизации
                    if server.notify_on_add:                                                            # и если стоит галочка уведомлять по емали
                        new_contacts.append(ldap_user)                                                  # Добавляем новый контакт в список для уведомлений
                    else:                                                                               # если галочки уведомлять по емайлу нету
                        _create_user_from_ldap(ldap_user, server_id)                                    # сразу добавляем контакт
                        new_users += 1


        # Отправляем email уведомление о новых контактах если они есть и уведомления включены
        if new_contacts and server.notify_on_add and server.smtp_is_active:
            from app.modules.mail_mod.notification_service_new_contact import send_new_contacts_notification
            send_new_contacts_notification(server, new_contacts)

        # После цикла отправляем уведомления об изменениях
        if updated_contacts and server.notify_on_update and server.smtp_is_active:
            from app.modules.mail_mod.notification_service_update_contact import send_update_contacts_notification
            send_update_contacts_notification(server, updated_contacts)

        server.last_sync =  datetime.utcnow().replace(microsecond=0)                                       # Обновляем время последней синхронизации
        db.session.commit()


        if server.notify_on_add:
            return True, f"Обнаружено {len(new_contacts)} новых контактов. Отправлены уведомления."
        else:
            return True, f"Синхронизация завершена. Новых: {new_users}, Обновлено: {updated_users}"
    except Exception as e:
        db.session.rollback()
        return False, f"Ошибка синхронизации: {str(e)}"
    finally:
        ldap.disconnect()

"""Проверяет, изменились ли данные пользователя"""
def _user_data_changed(db_user, ldap_user):
    return (db_user.cn != ldap_user.get('cn') or
            db_user.mail != ldap_user.get('mail') or
            db_user.telephone != ldap_user.get('telephone') or
            db_user.mobile != ldap_user.get('mobile') or
            db_user.title != ldap_user.get('title') or
            db_user.department != ldap_user.get('department'))

"""Обновляет данные пользователя из LDAP"""
def _update_user_from_ldap(db_user, ldap_user):
    db_user.cn = ldap_user.get('cn', db_user.cn)
    db_user.mail = ldap_user.get('mail', db_user.mail)
    db_user.telephone = ldap_user.get('telephone', db_user.telephone)
    db_user.mobile = ldap_user.get('mobile', db_user.mobile)
    db_user.title = ldap_user.get('title', db_user.title)
    db_user.department = ldap_user.get('department', db_user.department)
    db_user.photo = ldap_user.get('photo', db_user.photo)

"""Создает нового пользователя из LDAP данных"""
def _create_user_from_ldap(ldap_user, server_id):
    new_user = LDAPUsers(
        guid=ldap_user.get('guid'),
        server_id=server_id,
        cn=ldap_user.get('cn', ''),
        mail=ldap_user.get('mail'),
        telephone=ldap_user.get('telephone'),
        mobile=ldap_user.get('mobile'),
        title=ldap_user.get('title'),
        department=ldap_user.get('department'),
        photo=ldap_user.get('photo')
    )
    db.session.add(new_user)

"""Возвращает словарь измененных полей"""
def _get_changes_dict(db_user, ldap_user):
    
    changes = {}
    fields = ['cn', 'mail', 'telephone', 'mobile', 'title', 'department']
    
    for field in fields:
        db_value = getattr(db_user, field, None)
        ldap_value = ldap_user.get(field)
        
        if db_value != ldap_value:
            changes[field] = (db_value, ldap_value)
    
    return changes


"""
Быстрое добавление контакта по GUID из email уведомления
"""
def quick_add_contact(server_id, contact_guid):

    server = LDAPServer.query.get_or_404(server_id)
    
    # Проверяем существование контакта
    existing_contact = LDAPUsers.query.filter_by(guid=contact_guid, server_id=server_id).first()
    if existing_contact:
        flash(f'Контакт {existing_contact.cn} уже существует', 'warning')
        return redirect(url_for('ldap.show_list_saved_contacts', server_id=server_id))
    
    # Подключаемся к LDAP для получения данных контакта
    ldap = LDAPManager(
        server_url=f"{server.host}:{server.port}",
        user=server.bind_login,
        password=server.bind_password,
        base_dn=server.base_dn,
        use_ssl=server.use_ssl
    )
    
    success, message = ldap.connect()
    if not success:
        flash(f'Ошибка подключения к LDAP: {message}', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    try:
        # Получаем ВСЕХ пользователей и находим нужный по GUID
        all_users = ldap.get_all_users(search_filter=server.search_filter)
        ldap_user = None

        for user in all_users:
            if user.get('guid') == contact_guid:
                ldap_user = user
                break

        if not ldap_user:
            flash('Контакт не найден в LDAP', 'danger')
            return redirect(url_for('ldap.list_ldap_servers'))
        
        # Создаем контакт
        new_user = LDAPUsers(
            guid=contact_guid,
            server_id=server_id,
            cn=ldap_user.get('cn', ''),
            mail=ldap_user.get('mail'),
            telephone=ldap_user.get('telephone'),
            mobile=ldap_user.get('mobile'),
            title=ldap_user.get('title'),
            department=ldap_user.get('department'),
            photo=ldap_user.get('photo')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Контакт {new_user.cn} успешно добавлен', 'success')
        return redirect(url_for('ldap.show_list_saved_contacts', server_id=server_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка добавления контакта: {e}', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    finally:
        ldap.disconnect()



def quick_update_contact(server_id, contact_guid):
    """
    Быстрое обновление контакта по ссылке из email уведомления
    """
    server = LDAPServer.query.get_or_404(server_id)
    
    # Находим существующий контакт в БД
    existing_contact = LDAPUsers.query.filter_by(guid=contact_guid, server_id=server_id).first()
    if not existing_contact:
        flash(f'Контакт с GUID {contact_guid} не найден в базе данных', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    # Подключаемся к LDAP для получения актуальных данных
    ldap = LDAPManager(
        server_url=f"{server.host}:{server.port}",
        user=server.bind_login,
        password=server.bind_password,
        base_dn=server.base_dn,
        use_ssl=server.use_ssl
    )
    
    success, message = ldap.connect()
    if not success:
        flash(f'Ошибка подключения к LDAP: {message}', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    
    try:
        # Получаем ВСЕХ пользователей и находим нужный по GUID
        all_users = ldap.get_all_users(search_filter=server.search_filter)
        ldap_user = None
        
        for user in all_users:
            if user.get('guid') == contact_guid:
                ldap_user = user
                break
        
        if not ldap_user:
            flash('Контакт не найден в LDAP', 'danger')
            return redirect(url_for('ldap.list_ldap_servers'))
        
        # Сохраняем старые значения для лога
        old_values = {
            'cn': existing_contact.cn,
            'mail': existing_contact.mail,
            'telephone': existing_contact.telephone,
            'mobile': existing_contact.mobile,
            'title': existing_contact.title,
            'department': existing_contact.department
        }
        
        # Обновляем данные контакта
        existing_contact.cn = ldap_user.get('cn', existing_contact.cn)
        existing_contact.mail = ldap_user.get('mail', existing_contact.mail)
        existing_contact.telephone = ldap_user.get('telephone', existing_contact.telephone)
        existing_contact.mobile = ldap_user.get('mobile', existing_contact.mobile)
        existing_contact.title = ldap_user.get('title', existing_contact.title)
        existing_contact.department = ldap_user.get('department', existing_contact.department)
        existing_contact.photo = ldap_user.get('photo', existing_contact.photo)
        
        # Определяем какие поля изменились
        changed_fields = []
        for field in ['cn', 'mail', 'telephone', 'mobile', 'title', 'department']:
            old_val = old_values[field]
            new_val = getattr(existing_contact, field)
            if old_val != new_val:
                changed_fields.append(f"{field}: '{old_val}' → '{new_val}'")
        
        db.session.commit()
        
        if changed_fields:
            flash(f'Контакт {existing_contact.cn} успешно обновлен. Изменения: {", ".join(changed_fields)}', 'success')
        else:
            flash(f'Контакт {existing_contact.cn} актуален, изменений не требуется', 'info')
            
        return redirect(url_for('ldap.show_list_saved_contacts', server_id=server_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка обновления контакта: {e}', 'danger')
        return redirect(url_for('ldap.list_ldap_servers'))
    finally:
        ldap.disconnect()

""" Просмотр загруженной карты здания в БД"""
def get_building_plan(id):
    server = LDAPServer.query.get_or_404(id)
    if not server.building_plan_data:
        abort(404)
    
    # Простое имя файла без русских символов
    filename = 'building_plan'
    if server.building_plan_filename:
        # Берем только расширение файла
        import os
        _, ext = os.path.splitext(server.building_plan_filename)
        filename = f'building_plan{ext}'
    
    return Response(
        server.building_plan_data,
        mimetype=server.building_plan_mimetype,
        headers={
            'Content-Disposition': f'inline; filename="{filename}"'
        }
    )

