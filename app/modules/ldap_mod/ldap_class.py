from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPBindError
import base64 
from datetime import datetime, timezone


class LDAPManager:
    def __init__(self, server_url, user, password, base_dn, use_ssl=False):      #создаем класс
        self.server_url = server_url
        self.user = user
        self.password = password
        self.base_dn = base_dn
        self.use_ssl = use_ssl  # Сохраняем настройку SSL
        self.connection = None

    """Установить соединение с сервером LDAP."""
    def connect(self):
        try:
            # Определяем схему подключения в зависимости от SSL
            if self.use_ssl:
                scheme = "ldaps://"
            else:
                scheme = "ldap://"

            server = Server(scheme +  self.server_url, get_info=ALL)
            self.connection = Connection(server, user=self.user, password=self.password, auto_bind=True)
            success_message = "Соединение с LDAP установлено успешно! 😊"
            print(success_message)
            return True, success_message
        except LDAPBindError:
            error_message = "Ошибка привязки к серверу LDAP. Проверьте учетные данные. 🔍"
            print(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Произошла ошибка: {str(e)} ⚠️"
            print(error_message)
            return False, error_message

    """Добавить нового пользователя в LDAP."""
    def add_user(self, user_dn, attributes):
        if not self.connection:
            print("Сначала нужно установить соединение! ❌")
            return
        self.connection.add(user_dn, attributes=attributes)
        if self.connection.result['result'] == 0:
            print("Пользователь успешно добавлен! 🎉")
        else:
            print(f"Ошибка добавления пользователя: {self.connection.result['description']} ❌")


    """Поиск пользователя в LDAP"""
    def get_uid_for_authenticated_user(self):
        if not self.connection:
            print("Сначала нужно установить соединение! ❌")
            return None
        search_filter = f"(userPrincipalName={self.user})"
        self.connection.search(self.base_dn, search_filter, attributes=['objectGUID'])


        if self.connection.entries:
            entry = self.connection.entries[0]
            #guid = entry.objectGUID.value if 'objectGUID' in entry else None
            print(f"objectGUID найден: {entry} 👍")
            return entry

        print("Пользователь не найден. ❌")
        return None

    """Получить всех пользователей с указанными атрибутами"""
    def get_all_users(self, attributes=['cn', 'mail', 'telephoneNumber', 'mobile', 'title', 'department', 'thumbnailPhoto', 'objectGUID', 'whenCreated', 'whenChanged'], search_filter="(objectClass=person)"):
    
        if not self.connection:
            print("Сначала нужно установить соединение! ❌")
            return []
        
        self.connection.search(self.base_dn, search_filter, attributes=attributes)
        
        users = []
        for entry in self.connection.entries:
            # Получаем фото в base64 если оно есть
            photo_base64 = None
            if 'thumbnailPhoto' in entry and entry.thumbnailPhoto.value:
                photo_base64 = base64.b64encode(entry.thumbnailPhoto.value).decode('utf-8')

            # Конвертируем GUID из бинарного в строковый формат
            guid_str = None
            if 'objectGUID' in entry and entry.objectGUID.value:
                guid_str = entry.objectGUID.value

            # Получаем и преобразуем временные метки к naive datetime
            when_created = None
            when_changed = None
            
            if 'whenCreated' in entry and entry.whenCreated.value:                  # Проверяем, существует ли атрибут `whenCreated` в записи и оно не пустое
                when_created = entry.whenCreated.value                              # Получаем значение временной метки из LDAP
                if when_created.tzinfo is not None:                                 # Проверяем, имеет ли datetime временную зону
                    when_created = when_created.astimezone(timezone.utc).replace(tzinfo=None)               # Преобразуем к naive удаляет информацию о временной зоне
            
            if 'whenChanged' in entry and entry.whenChanged.value:                  # Проверяем, существует ли атрибут `whenChanged` в записи и оно не пустое
                when_changed = entry.whenChanged.value                              # Получаем значение временной метки из LDAP
                if when_changed.tzinfo is not None:                                 # Проверяем, имеет ли datetime временную зону
                    when_changed = when_changed.astimezone(timezone.utc).replace(tzinfo=None)                # Преобразуем к naive удаляет информацию о временной зоне

            user_data = {
                'guid': guid_str,  # Добавляем GUID
                'cn': entry.cn.value if 'cn' in entry else None,
                'mail': entry.mail.value if 'mail' in entry else None,
                'telephone': entry.telephoneNumber.value if 'telephoneNumber' in entry else None,
                'mobile': entry.mobile.value if 'mobile' in entry else None,
                'title': entry.title.value if 'title' in entry else None,  # Должность
                'department': entry.department.value if 'department' in entry else None,  # Отдел
                'photo': photo_base64,  # Фото в base64
                'when_created': when_created,
                'when_changed': when_changed
            }
            users.append(user_data)
        return users


    """Находит пользователя по GUID"""
    def get_user_by_guid(self, guid):        
        search_filter = f"(objectGUID={guid})"
        users = self.get_all_users(search_filter)
        return users[0] if users else None


    """Закрыть соединение с сервером LDAP."""
    def disconnect(self):
        if self.connection:
            self.connection.unbind()
            print("Соединение с LDAP закрыто. 👋")