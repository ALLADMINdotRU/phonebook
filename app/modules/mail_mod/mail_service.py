import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

class MailService:
    def __init__(self, smtp_config=None):
        self.smtp_config = smtp_config or {}
    
    def send_email(self, to_email, subject, body, from_email=None, html_body=None):
        """
        Отправляет email с поддержкой HTML и текстовой версии
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            body: Текстовая версия письма
            from_email: Email отправителя (опционально)
            html_body: HTML версия письма (опционально)
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Определяем email отправителя
            from_email = from_email or self.config.get('username')

            # Создаем сообщение
            if html_body:
                # Создаем multipart сообщение с HTML и текстовой версией
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            else:
                # Простое текстовое сообщение
                msg = MIMEText(body, 'plain', 'utf-8')


            # Заполняем заголовки
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            

            
            
            # Подключаемся к SMTP серверу
            if self.smtp_config.get('use_ssl'):
                server = smtplib.SMTP_SSL(self.smtp_config['host'], self.smtp_config['port'])
            else:
                server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            
            # Включаем TLS если нужно
            if self.smtp_config.get('use_tls'):
                server.starttls()

            # Логинимся (только если указаны username и password)
            if self.smtp_config.get('username') and self.smtp_config.get('password'):
                server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            # Отправляем письмо
            server.sendmail(from_email, to_email, msg.as_string())
            server.quit()
            
            return True, "Email отправлен успешно"
            
        except Exception as e:
            return False, f"Ошибка отправки email: {str(e)}"

# Глобальный экземпляр сервиса (можно будет настроить позже)
mail_service = MailService()
