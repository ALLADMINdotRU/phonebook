from flask_apscheduler import APScheduler
import logging

# Настройка логирования для этого модуля
# Создаем логгер с именем текущего модуля для удобства отслеживания
logger = logging.getLogger(__name__)

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
    1. Получение всех активных LDAP серверов из базы  данных 
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
        logger.info(f"Начинаем синхронизацию {len(active_servers)} активных серверов")
        
        # Проходим по каждому активному серверу и выполняем синхронизацию
        for server in active_servers:
            try:
                # Вызываем функцию синхронизации для конкретного сервера
                # Функция sync_ldap_contacts возвращает кортеж (success, message)
                success, message = sync_ldap_contacts(server.id)
                
                # Логируем результат синхронизации в зависимости от успешности
                if success:
                    logger.info(f"Сервер {server.name}: {message}")
                else:
                    logger.error(f"Сервер {server.name}: {message}")
                    
            except Exception as e:
                # Ловим любые исключения и логируем ошибку
                # Это предотвращает падение всей синхронизации из-за ошибки одного сервера
                logger.error(f"Ошибка сервера {server.name}: {e}")

def init_scheduler(app):
    """
    Инициализация и настройка планировщика APScheduler.
    
    Args:
        app: Экземпляр Flask приложения для конфигурации
        
    Returns:
        bool: True если планировщик успешно запущен, False в случае ошибки
    
    Функция выполняет:
    1. Настройку конфигурации планировщика
    2. Инициализацию планировщика с приложением
    3. Добавление задачи синхронизации
    4. Запуск планировщика
    """
    try:
        # Конфигурация планировщика APScheduler
        app.config['SCHEDULER_API_ENABLED'] = False  # Отключаем REST API для безопасности
        app.config['SCHEDULER_TIMEZONE'] = 'UTC'     # Устанавливаем часовой пояс UTC
        
        # Инициализируем планировщик с конфигурацией приложения
        # Это связывает планировщик с текущим Flask приложением
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
            logger.info("✅ Задача синхронизации LDAP добавлена в планировщик")
        else:
            logger.info("⚠️ Автоматическая синхронизация LDAP отключена в конфигурации")
            
        # Запускаем планировщик
        # Планировщик начинает выполнять задачи согласно расписанию
        scheduler.start()
        
        # Логируем успешный запуск
        logger.info("✅ Планировщик APScheduler запущен")
        return True
        
    except Exception as e:
        # Обрабатываем ошибки инициализации планировщика
        # Логируем ошибку и возвращаем False для индикации неудачи
        logger.error(f"❌ Ошибка инициализации планировщика: {e}")
        return False
