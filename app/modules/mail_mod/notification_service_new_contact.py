from datetime import datetime
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def send_new_contacts_notification(server, new_contacts):
    """
    Отправляет email уведомление о новых контактах в LDAP с ссылками для быстрого добавления
    
    Args:
        server: Объект LDAPServer
        new_contacts: Список новых контактов из LDAP
        
    Returns:
        bool: True если уведомление отправлено успешно, False в случае ошибки
    """
    try:
        from .mail_service import MailService
        
        # Проверяем что SMTP настроен и указан email получателя
        if not server.smtp_to_email:
            logger.warning(f"Не указан email для уведомлений на сервере {server.name}")
            return False
        
        # Проверяем что уведомления включены для этого сервера
        if not server.notify_on_add:
            logger.info(f"Уведомления о новых контактах отключены для сервера {server.name}")
            return False
        
        # Проверяем что SMTP активен
        if not server.smtp_is_active:
            logger.warning(f"SMTP не активен для сервера {server.name}")
            return False
        
        # Получаем базовый URL из конфигурации приложения
        base_url = current_app.config.get('APP_BASE_URL', 'http://localhost:5000')
        
        # Формируем тему письма
        subject = f"Новые контакты в LDAP: {server.name}"
        
        # Формируем текстовую версию списка контактов
        text_contacts_list = "\n".join([
            f"- {contact.get('cn', 'Без имени')} "
            f"(Email: {contact.get('mail', 'нет')}, "
            f"Телефон: {contact.get('telephone', 'нет')})"
            for contact in new_contacts
        ])
        
        # Формируем HTML версию списка контактов со ссылками
        html_contacts_list = "\n".join([
            f"<li>"
            f"{contact.get('cn', 'Без имени')} "
            f"(Email: {contact.get('mail', 'нет')}, "
            f"Телефон: {contact.get('telephone', 'нет')}) "
            f"<a href='{base_url}/ldap/servers/{server.id}/quick-add/{contact.get('guid')}' "
            f"style='color: #007bff; text-decoration: none; background: #f8f9fa; "
            f"padding: 2px 6px; border-radius: 3px; border: 1px solid #007bff;'>"
            f"Добавить</a>"
            f"</li>"
            for contact in new_contacts
        ])
        
        # Текстовая версия тела письма
        text_body = f"""Обнаружены новые контакты в LDAP сервере "{server.name}":

{text_contacts_list}

Всего новых контактов: {len(new_contacts)}

Для быстрого добавления перейдите по ссылкам в HTML версии этого письма.

---
Это автоматическое уведомление от системы Phonebook.
Время обнаружения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # HTML версия тела письма
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Новые контакты в LDAP</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #007bff;">Новые контакты в LDAP сервере "{server.name}"</h2>
        
        <p>Обнаружены следующие новые контакты:</p>
        
        <ul style="list-style: none; padding: 0;">
        {html_contacts_list}
        </ul>
        
        <p><strong>Всего новых контактов:</strong> {len(new_contacts)}</p>
        
        <p>Для быстрого добавления контакта в базу данных нажмите на кнопку "Добавить" рядом с нужным контактом.</p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        
        <p style="font-size: 12px; color: #666;">
            <em>Это автоматическое уведомление от системы Phonebook.<br>
            Время обнаружения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em>
        </p>
    </div>
</body>
</html>"""
        
        # Получаем SMTP конфигурацию
        smtp_config = server.get_smtp_config()
        if not smtp_config:
            logger.error(f"Не удалось получить SMTP конфигурацию для сервера {server.name}")
            return False
            
        # Отправляем письмо с HTML и текстовой версией
        mail_service = MailService(smtp_config)
        success, message = mail_service.send_email(
            to_email=server.smtp_to_email,
            subject=subject,
            body=text_body,      # Текстовая версия для почтовых клиентов без HTML
            html_body=html_body, # HTML версия с форматированием и ссылками
            from_email=server.smtp_from_email or server.smtp_username
        )
        
        if success:
            logger.info(f"Уведомление о {len(new_contacts)} новых контактах отправлено на {server.smtp_to_email}")
        else:
            logger.error(f"Ошибка отправки уведомления: {message}")
            
        return success
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о новых контактах: {e}")
        return False
