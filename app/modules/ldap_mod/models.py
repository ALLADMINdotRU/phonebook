from app import db  # Импорт экземпляра SQLAlchemy

# Модель для хранения параметров LDAP серверов
class LDAPServer(db.Model):
    __tablename__ = 'ldap_server'

    id = db.Column(db.Integer, primary_key=True)                                    # Первичный ключ
    name = db.Column(db.String(64), unique=True)                                    # Уникальное название сервера (макс. 64 символа)
    host = db.Column(db.String(128))                                                # Хост сервера (макс. 128 символов)
    port = db.Column(db.Integer, default=389)                                       # Порт подключения (по умолчанию 389)
    base_dn = db.Column(db.String(128))                                             # Базовый DN для поиска (макс. 128 символов)
    bind_login = db.Column(db.String(128))                                          # Учетная запись для подключения (макс. 128 символов)
    bind_password = db.Column(db.String(128))                                       # Пароль для подключения (макс. 128 символов)
    last_sync = db.Column(db.DateTime)                                              # Время последней синхронизации
    use_ssl = db.Column(db.Boolean, default=False)                                  # Флаг использования SSL
    description = db.Column(db.String(256))                                         # Описание подключения
    search_filter = db.Column(db.String(256), default="(objectClass=person)")       # Фильтр поиска пользователей
    is_active = db.Column(db.Boolean, default=False)                                # Активируем синхронизацию
    # Поля для почтового 
    smtp_host = db.Column(db.String(100))                                           # SMTP хост
    smtp_port = db.Column(db.Integer, default=25)                                   # SMTP порт
    smtp_username = db.Column(db.String(100))                                       # Имя пользователя SMTP
    smtp_password = db.Column(db.String(100))                                       # Пароль SMTP
    smtp_use_tls = db.Column(db.Boolean, default=True)                              # Использовать TLS
    smtp_use_ssl = db.Column(db.Boolean, default=False)                             # Использовать SSL
    smtp_from_email = db.Column(db.String(100))                                     # Email отправителя по умолчанию
    smtp_to_email = db.Column(db.String(100))                                       # Email получателя по умолчанию
    smtp_is_active = db.Column(db.Boolean, default=False)                           # Активны ли SMTP настройки
    notify_on_add = db.Column(db.Boolean, default=False)                            # Уведомлять о новых контактах
    notify_on_update = db.Column(db.Boolean, default=False)                         # Уведомлять об изменениях контактов

    # НОВЫЕ ПОЛЯ ДЛЯ ПЛАНА ЗДАНИЯ В БД
    building_plan_data = db.Column(db.LargeBinary)                                  # Данные файла
    building_plan_filename = db.Column(db.String(255))                              # Оригинальное имя файла
    building_plan_mimetype = db.Column(db.String(100))                              # MIME-type (image/svg+xml, image/png, etc.)

    

    def __repr__(self):
        return f'<LDAPServer {self.name}>'

    def get_smtp_config(self):
        """Возвращает конфигурацию SMTP в виде словаря"""
        if not self.smtp_is_active:
            return None
            
        return {
            'host': self.smtp_host,
            'port': self.smtp_port,
            'username': self.smtp_username,
            'password': self.smtp_password,
            'use_tls': self.smtp_use_tls,
            'use_ssl': self.smtp_use_ssl,
            'from_email': self.smtp_from_email or self.smtp_username,
        }


class LDAPUsers(db.Model):
    """Модель для хранения пользователей, импортированных из LDAP"""
    __tablename__ = 'ldap_users'                                                    # Указываем имя таблицы в БД (необязательно, но рекомендуется)

    id = db.Column(db.Integer, primary_key=True)                                    # ID записи - первичный ключ (автоинкремент)
    guid = db.Column(db.String(64), unique=True)                                    # Уникальный идентификатор пользователя в LDAP (GUID) Хранится как строка
    server_id = db.Column(db.Integer, db.ForeignKey('ldap_server.id'), nullable=False) # Связь с сервером LDAP (внешний ключ) # Хранит ID сервера, из которого импортирован пользователь
    cn = db.Column(db.String(128), nullable=False)                                  # Полное имя пользователя (Common Name)
    mail = db.Column(db.String(128))                                                # Электронная почта пользователя
    telephone = db.Column(db.String(32))                                            # Рабочий телефон пользователя
    mobile = db.Column(db.String(32))                                               # Мобильный телефон пользователя
    title = db.Column(db.String(128))                                               # Должность пользователя
    department = db.Column(db.String(128))                                          # Отдел/подразделение пользователя
    photo = db.Column(db.Text)                                                      # Фотография пользователя в формате base64
    server = db.relationship('LDAPServer', backref=db.backref('users', lazy=True))  # Связь с моделью LDAPServer (один ко многим) # backref создает свойство 'users' в LDAPServer для доступа к связанным пользователям
    
    # НОВЫЕ ПОЛЯ ДЛЯ КАРТЫ
    coordinates = db.Column(db.String(100))                                         # Формат: "x,y" например "120,45"
    is_on_map = db.Column(db.Boolean, default=False)                                # Отображать на карте


    def __repr__(self):
        """Строковое представление объекта (для отладки)"""
        return f'<LDAPUser {self.cn} (ID: {self.id})>'

