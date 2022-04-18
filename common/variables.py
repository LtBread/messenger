import logging

""" константы """
DEFAULT_PORT = 7777  # порт сервера по умолчанию
DEFAULT_IP_ADDRESS = '127.0.0.1'  # IP-адрес сервера по умолчанию
MAX_CONNECTIONS = 5  # максимальная очередь подключения
MAX_PACKAGE_LENGTH = 1024  # максимальный размер сообщения в байтах
ENCODING = 'utf-8'  # кодировка проекта
LOGGING_LEVEL = logging.DEBUG  # текущий уровень логирования
SERVER_DATABASE = 'sqlite:///server_database.db3'

""" основные ключи протокола JIM """
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

""" прочие ключи """
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
# RESPONDEFAULT_IP_ADDRESSSE = 'respondefault_ip_addressse'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'

""" словари - ответы """
RESPONSE_200 = {RESPONSE: 200}
RESPONSE_202 = {RESPONSE: 202, LIST_INFO: None}
RESPONSE_400 = {RESPONSE: 400, ERROR: None}
