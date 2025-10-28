from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from threading import Lock
import logging

# Настройка логирования для этого модуля
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()                   
sync_lock = Lock()

def sync_all_servers(app):

    
    if not sync_lock.acquire(blocking=False):
        logger.info("Синхронизация уже выполняется, пропускаем")
        return
    
    try:
        with app.app_context():
            from app.modules.ldap_mod.models import LDAPServer
            from app.modules.ldap_mod.views import sync_ldap_contacts
            
            active_servers = LDAPServer.query.filter_by(is_active=True).all()
            logger.info(f"Активных серверов: {len(active_servers)}")
            
            for server in active_servers:
                try:
                    sync_ldap_contacts(server.id)
                except Exception as e:
                    logger.error(f"Ошибка сервера {server.name}: {e}")
    
    finally:
        sync_lock.release()

def init_scheduler(app):
    """Инициализация простого планировщика"""
    try:
        scheduler.add_job(
            sync_all_servers(app),
            IntervalTrigger(minutes=1),
            id='ldap_sync'
        )
        scheduler.start()
        logger.info("✅ Планировщик запущен")
        return scheduler
    except Exception as e:
        logger.error(f"❌ Ошибка планировщика: {e}")
        return None
