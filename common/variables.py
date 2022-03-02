import logging

""" CONSTANTS """

# порт сервера по умолчанию
DEFAULT_PORT = 7777
# IP-адрес сервера по умолчанию
DEFAULT_IP_ADDRESS = '127.0.0.1'
# максимальная очередь подключения
MAX_CONNECTIONS = 5
# максимальный размер сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# кодировка проекта
ENCODING = 'utf-8'
# текущий уровень логирования
LOGGING_LEVEL = logging.DEBUG

""" JIM KEYS """

ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'

""" OTHERS KEYS """

PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
RESPONDEFAULT_IP_ADDRESSSE = 'respondefault_ip_addressse'
