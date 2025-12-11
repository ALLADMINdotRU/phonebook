import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy                             # для работы с ORM
from flask_migrate import Migrate                                   # Обеспечивает систему миграций для SQLAlchemy и Автоматически отслеживает изменения в моделях
from app.create_db import create_database_if_not_exists
from flask_wtf.csrf import CSRFProtect                              # Импорт CSRF защиты
from flask_caching import Cache                                     # Кэшь реализация flask
from flask_session import Session                                   # cерверного хранения сессий

csrf = CSRFProtect()                                                # Создаем экземпляр CSRF защиты
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()                                                     # Глобальная переменная КЭША

def create_app(config_class='app.config.Config'):                   # запускаем прогу передавая конфигурацию
    app = Flask(__name__, template_folder='templates', static_folder='static')                                           # иницилизируем 
    app.config.from_object(config_class)                            # загружаем конфигурацию
    
    app.logger.setLevel(logging.INFO)                   # указываем уровено логирования


    Session(app)

    # Инициализация CSRF защиты
    csrf.init_app(app)

    # Инициализация кеша
    cache.init_app(app)  

    # Инициализация БД
    db.init_app(app)
    migrate.init_app(app, db)

    # Создаем БД 
    try:
        create_database_if_not_exists()
    except Exception as e:
        app.logger.warning(f"Could not create database: {e}")

    # Создаем таблицы в БД
    with app.app_context():                                         # в этой части кода создаем таблицы для бд
        from sqlalchemy import inspect
        from app.models import User                                 # тут импортируем модели которые мы хотим реализовать в виде таблиц в БД
        from app.modules.ldap_mod.models import LDAPServer          # импортируем модель БД LDAP
        inspector = inspect(db.engine)

        if not inspector.has_table('alembic_version'):              # Если нет таблицы версий, 
            try:
                if os.path.exists('migrations'):                    # но есть папка миграций  проверяем существование папки migraitons
                    from flask_migrate import stamp                 #
                    db.create_all()                                 # создаем все таблицы из модели 
                    stamp()                                         # добавляем таблицу alembic_version
                else:
                    from flask_migrate import init as migrate_init  # .к. у нас уже есть выше  migrate то тут называем ее migrate_init
                    migrate_init()                                  # инициализируем миграцию т.е. создается папка migraitons
                    print(f"Инициализации миграции")
            except Exception as e:
                print(f"Ошибка миграции БД {e}")
            else:                                                   # если есть таблица alembic_version то мы предполагем что есть и папка migrations поэтому просто пробуем обновить БД
                try:
                    from flask_migrate import upgrade as migrate_upgrade
                    from flask_migrate import migrate as generate_migration
                    generate_migration(message='Авто миграция')
                    migrate_upgrade()  
                except:
                    print(f"Ошибка обновления БД {e}")

    from app.route import main_bp
    app.register_blueprint(main_bp)

    # Модуль для работы с LDAP
    from app.modules.ldap_mod import bp as ldap_bp
    app.register_blueprint(ldap_bp)

    # Модуль для работы с mail
    from app.modules.mail_mod import bp as mail_bp
    app.register_blueprint(mail_bp)
    
    # Модуль телефонной книги для пользователей
    from app.modules.phonebook_mod import bp as phonebook_bp
    app.register_blueprint(phonebook_bp)

    # Модуль карты пользователей на предприятии
    from app.modules.map_mod import bp as map_bp
    app.register_blueprint(map_bp)

    # Модуль авторизации
    from app.modules.auth_mod  import bp as auth_bp
    app.register_blueprint(auth_bp)

    # Инициализация планировщика
    from app.scheduler import init_scheduler
    init_scheduler(app)

    return app
