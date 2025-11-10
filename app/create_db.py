import psycopg2
from app.config import DBCreationConfig

def create_database_if_not_exists():
    try:
        conn = psycopg2.connect(DBCreationConfig.POSTGRES_ADMIN_URI)                                 # URI подключения  одно и то же . так что испльзуем его
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Проверяем существование БД
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{DBCreationConfig.DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DBCreationConfig.DB_NAME}")
            print(f"База данных {DBCreationConfig.DB_NAME} создана")
        else:
            print(f"База данных {DBCreationConfig.DB_NAME} уже существует")
            
    except psycopg2.Error as e:
        print(f"Ошибка: {e}")
    finally:
        if conn:
            conn.close()
