import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Базовые настройки приложения"""

    # Смещение часового пояса в часах (для Новосибирска UTC+7)
    TIME_ZONE_OFFSET = int(os.environ.get('TIME_ZONE_OFFSET'))
    # Время синхронизации LDAP серверов
    LDAP_SYNC_ENABLED = os.environ.get('LDAP_SYNC_ENABLED', 'true').lower() == 'true'
    LDAP_SYNC_INTERVAL_MINUTES = int(os.environ.get('LDAP_SYNC_INTERVAL_MINUTES', 1))

    # базоый урл для формирования сслыки в письмах
    APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:5050')

    # Настройки авторизации
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
class Config(BaseConfig):
    """Конфигурация Flask приложения"""
    SECRET_KEY = os.environ.get('SECRET_KEY')                                               # секретный ключ для формы
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')                                # строка подключения  к бд
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # параметры для flask_caching 
    CACHE_TYPE = 'SimpleCache'                                                              # Для начала используем встроенный кеш
    CACHE_DEFAULT_TIMEOUT = 300                                                             # Время жизни кеша в секундах

    

    # Конфигурация Flask-Session
    SESSION_TYPE = 'filesystem'                                                             # Или 'redis', 'memcached'
    SESSION_FILE_DIR = '/tmp/flask_session'
    SESSION_PERMANENT = True                                                                #сессии не истекают при закрытии браузера
    SESSION_USE_SID = True                                                                  # генерирует уникальный ID сессии (session.sid)


class DBCreationConfig(BaseConfig):
    """Конфигурация для создания БД"""
    POSTGRES_ADMIN_URI = os.environ.get('POSTGRES_ADMIN_URI')
    DB_NAME = os.environ.get('POSTGRES_DB')
