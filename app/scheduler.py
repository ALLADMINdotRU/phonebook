from flask_apscheduler import APScheduler
import os
import fcntl

# Создаем глобальный экземпляр планировщика APScheduler
# APScheduler предоставляет расширенные возможности планирования задач
# Глобальная переменная позволяет обращаться к планировщику из других модулей
scheduler = APScheduler()

def sync_all_servers(app):
    """
    Основная функция синхронизации всех активных LDAP серверов.
    
    Args:
        app: Экземпляр Flask приложения, необходим для доступа к контексту и БД
    
    Функция выполняет:
    1. Получение всех активных LDAP серверов из базы данных 
    2. Последовательную синхронизацию каждого сервера
    3. Логирование результатов синхронизации
    """
    # Создаем контекст Flask приложения для работы с БД и другими компонентами
    # Контекст необходим для доступа к моделям SQLAlchemy и конфигурации
    with app.app_context():
        # Импортируем модели и функции внутри функции для избежания циклических импортов
        # Это стандартная практика в Flask для предотвращения проблем с импортами
        from app.modules.ldap_mod.models import LDAPServer
        from app.modules.ldap_mod.views import sync_ldap_contacts
        
        # Получаем все активные серверы из базы данных
        # Фильтруем только те серверы, у которых is_active=True
        active_servers = LDAPServer.query.filter_by(is_active=True).all()
        
        # Логируем начало процесса синхронизации
        app.logger.info(f"Начинаем синхронизацию {len(active_servers)} активных серверов")
        
        # Проходим по каждому активному серверу и выполняем синхронизацию
        for server in active_servers:
            try:
                # Вызываем функцию синхронизации для конкретного сервера
                # Функция sync_ldap_contacts возвращает кортеж (success, message)
                success, message = sync_ldap_contacts(server.id)
                
                # Логируем результат синхронизации в зависимости от успешности
                if success:
                    app.logger.info(f"Сервер {server.name}: {message}")
                else:
                    app.logger.error(f"Сервер {server.name}: {message}")
                    
            except Exception as e:
                # Ловим любые исключения и логируем ошибку
                # Это предотвращает падение всей синхронизации из-за ошибки одного сервера
                app.logger.error(f"Ошибка сервера {server.name}: {e}")

def init_scheduler(app):
    """
    Инициализация и настройка планировщика APScheduler.
    
    Args:
        app: Экземпляр Flask приложения для конфигурации
        
    Returns:
        bool: True если планировщик успешно запущен или пропущен, False в случае ошибки
    
    Функция выполняет:
    1. Проверку блокировки для запуска только в одном процессе
    2. Настройку конфигурации планировщика
    3. Инициализацию планировщика с приложением
    4. Добавление задачи синхронизации
    5. Запуск планировщика
    """
    # Файл для блокировки (используем /tmp, так как это стандартно для Linux)
    lock_file = '/tmp/scheduler.lock'
    
    try:
        # Пытаемся захватить эксклюзивную блокировку файла
        fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        # Блокировка уже захвачена другим процессом
        app.logger.info(f"Планировщик уже запущен в другом процессе (PID: {os.getpid()}), пропускаем")
        return True
    except Exception as e:
        # Неожиданная ошибка при работе с блокировкой
        app.logger.warning(f"Ошибка блокировки: {e}. Продолжаем запуск планировщика")
    
    # Этот процесс захватил блокировку - запускаем планировщик
    app.logger.info(f"Запуск планировщика в процессе с PID: {os.getpid()}")
    
    try:
        # Конфигурация планировщика APScheduler
        app.config['SCHEDULER_API_ENABLED'] = False  # Отключаем REST API для безопасности
        app.config['SCHEDULER_TIMEZONE'] = 'UTC'     # Устанавливаем часовой пояс UTC
        
        # Инициализируем планировщик с конфигурацией приложения
        scheduler.init_app(app)
        
        # Добавляем задачу синхронизации в планировщик только если синхронизация включена
        if app.config.get('LDAP_SYNC_ENABLED', True):
            scheduler.add_job(
                id='ldap_sync',                   # Уникальный идентификатор задачи
                func=sync_all_servers,            # Функция для выполнения
                args=[app],                       # Аргументы для функции - передаем app
                trigger='interval',               # Тип триггера - интервальный
                minutes=app.config['LDAP_SYNC_INTERVAL_MINUTES'],  # Интервал в минутах из конфига
                replace_existing=True             # Заменяем существующую задачу с таким же ID
            )
            app.logger.info("✅ Задача синхронизации LDAP добавлена в планировщик")
        else:
            app.logger.info("⚠️ Автоматическая синхронизация LDAP отключена в конфигурации")
            
        # Запускаем планировщик
        scheduler.start()
        app.logger.info("✅ Планировщик APScheduler запущен")
        return True
        
    except Exception as e:
        app.logger.error(f"❌ Ошибка инициализации планировщика: {e}")
        # Освобождаем блокировку при ошибке
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except:
            pass
        return False
    
    # Файловый дескриптор не закрываем, чтобы блокировка сохранялась
    # Он будет автоматически закрыт при завершении процесса
