from flask_wtf import FlaskForm                                                                                     # Базовый класс для форм Flask
from wtforms import StringField, IntegerField, BooleanField, PasswordField, SubmitField                                          # Типы полей формы
from wtforms.validators import DataRequired, Optional, NumberRange                                                  # Валидаторы для проверки ввода
from wtforms import DateTimeField
from flask_wtf.file import FileField, FileAllowed, FileRequired

class LDAPServerForm(FlaskForm):
    name = StringField('Название сервера', validators=[DataRequired()])                                             # Поле названия сервера (необязательное)
    host = StringField('Адрес сервера', validators=[Optional()])                                                    # Поле хоста (необязательное)
    port = IntegerField('Порт', validators=[Optional(), NumberRange(min=1, max=65535)], default=389)                # Поле порта (значение по умолчанию 389)
    base_dn = StringField('Base DN', validators=[Optional()])                                                       # Поле базового DN (необязательное)
    bind_login = StringField('Логин', validators=[Optional()])                                                      # Поле учетной записи (необязательное)
    bind_password = PasswordField('Пароль', validators=[Optional()])                                                # Поле пароля (необязательное, скрытый ввод)
    use_ssl = BooleanField('Использовать SSL')                                                                      # Чекбокс использования SSL
    description = StringField('Описание подключения', validators=[Optional()])
    search_filter = StringField('Фильтр поиска', validators=[Optional()], default="(objectClass=person)")
    last_sync = DateTimeField('Время последней синхронизации', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    is_active = BooleanField('Включить синхронизацию', default=False)

    # поля SMTP
    smtp_host = StringField('SMTP Хост')
    smtp_port = IntegerField('SMTP Порт', default=25)
    smtp_username = StringField('SMTP Пользователь')
    smtp_password = PasswordField('SMTP Пароль')
    smtp_use_tls = BooleanField('SMTP Использовать TLS', default=False)
    smtp_use_ssl = BooleanField('SMTP Использовать SSL')
    smtp_from_email = StringField('Email отправителя')
    smtp_to_email = StringField('Email получателя')
    smtp_is_active = BooleanField('Активировать SMTP')
    notify_on_add = BooleanField('Уведомлять о новых контактах', default=False)
    notify_on_update = BooleanField('Уведомлять об изменениях контактов', default=False)


        # НОВОЕ ПОЛЕ: файл плана здания
    building_plan = FileField('План здания', validators=[
        FileAllowed(['svg', 'png', 'jpg', 'jpeg'], 'Только SVG и изображения!')
    ])
    
    submit = SubmitField('Сохранить')