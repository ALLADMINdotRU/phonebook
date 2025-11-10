from datetime import datetime
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def send_update_contacts_notification(server, updated_contacts):
    """
    Отправляет email уведомление об измененных контактах в LDAP с ссылками для быстрого обновления
    
    Args:
        server: Объект LDAPServer
        updated_contacts: Список измененных контактов с информацией об изменениях
            Каждый контакт должен содержать:
            - guid: GUID контакта
            - cn: Имя контакта
            - changes: Словарь изменений {поле: (старое_значение, новое_значение)}
            
    Returns:
        bool: True если уведомление отправлено успешно, False в случае ошибки
    """
    try:
        from .mail_service import MailService
        
        # Проверяем что SMTP настроен и указан email получателя
        if not server.smtp_to_email:
            logger.warning(f"Не указан email для уведомлений на сервере {server.name}")
            return False
        
        # Проверяем что уведомления об обновлениях включены для этого сервера
        if not server.notify_on_update:
            logger.info(f"Уведомления об обновлениях контактов отключены для сервера {server.name}")
            return False
        
        # Проверяем что SMTP активен
        if not server.smtp_is_active:
            logger.warning(f"SMTP не активен для сервера {server.name}")
            return False
        
        # Получаем базовый URL из конфигурации приложения
        base_url = current_app.config.get('APP_BASE_URL', 'http://localhost:5000')
        
        # Формируем тему письма
        subject = f"Изменения контактов в LDAP: {server.name}"
        
        # Формируем текстовую версию списка измененных контактов
        text_contacts_list = "\n".join([
            f"- {contact['cn']} (GUID: {contact['guid']})\n"
            + "\n".join([f"  {field}: {old_value} → {new_value}" 
                        for field, (old_value, new_value) in contact['changes'].items()])
            + f"\n  Обновить: {base_url}/ldap/servers/{server.id}/quick-update/{contact['guid']}"
            for contact in updated_contacts
        ])
        
        # Формируем HTML версию списка контактов со ссылками
        html_contacts_list = "\n".join([
            f"""<li style="margin-bottom: 15px; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                <strong style="font-size: 16px;">{contact['cn']}</strong> 
                <span style="font-size: 12px; color: #666;">(GUID: {contact['guid']})</span><br>
                
                <table style="border-collapse: collapse; margin: 8px 0; width: 100%;">
                {"".join([f"""
                <tr>
                    <td style="padding: 4px 8px; border: 1px solid #ddd; background: #f8f9fa; width: 120px;">
                        <strong>{field}:</strong>
                    </td>
                    <td style="padding: 4px 8px; border: 1px solid #ddd; color: #dc3545; text-decoration: line-through;">
                        {old_value or 'нет'}
                    </td>
                    <td style="padding: 4px 8px; border: 1px solid #ddd; color: #28a745; font-weight: bold;">
                        {new_value or 'нет'}
                    </td>
                </tr>
                """ for field, (old_value, new_value) in contact['changes'].items()])}
                </table>
                
                <a href="{base_url}/ldap/servers/{server.id}/quick-update/{contact['guid']}"
                   style="display: inline-block; color: #fff; text-decoration: none; 
                          background: #28a745; padding: 6px 12px; border-radius: 4px; 
                          border: none; font-weight: bold;">
                   Обновить
                </a>
            </li>"""
            for contact in updated_contacts
        ])
        
        # Текстовая версия тела письма
        text_body = f"""Обнаружены изменения контактов в LDAP сервере "{server.name}":

{text_contacts_list}

Всего измененных контактов: {len(updated_contacts)}

Для применения изменений перейдите по ссылкам в HTML версии этого письма.

---
Это автоматическое уведомление от системы Phonebook.
Время обнаружения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # HTML версия тела письма
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Изменения контактов в LDAP</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h2 {{ color: #007bff; margin-top: 0; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin-bottom: 15px; }}
        .changes-table {{ width: 100%; border-collapse: collapse; }}
        .changes-table td {{ padding: 4px 8px; border: 1px solid #ddd; }}
        .old-value {{ color: #dc3545; text-decoration: line-through; }}
        .new-value {{ color: #28a745; font-weight: bold; }}
        .update-btn {{ display: inline-block; background: #28a745; color: white; padding: 6px 12px; 
                      text-decoration: none; border-radius: 4px; font-weight: bold; border: none; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Изменения контактов в LDAP сервере "{server.name}"</h2>
        
        <p>Обнаружены изменения в следующих контактах:</p>
        
        <ul>
        {html_contacts_list}
        </ul>
        
        <p><strong>Всего измененных контактов:</strong> {len(updated_contacts)}</p>
        
        <p>Для применения изменений нажмите кнопку "Обновить" рядом с нужным контактом.</p>
        
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
            body=text_body,
            html_body=html_body,
            from_email=server.smtp_from_email or server.smtp_username
        )
        
        if success:
            logger.info(f"Уведомление об {len(updated_contacts)} измененных контактах отправлено на {server.smtp_to_email}")
        else:
            logger.error(f"Ошибка отправки уведомления: {message}")
            
        return success
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления об измененных контактах: {e}")
        return False
