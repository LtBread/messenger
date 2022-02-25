import os
import sys
import logging
from common.variables import LOGGING_LEVEL, ENCODING

sys.path.append('../')

# создание формирователя логов (formatter)
CLIENT_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

# подготовка имени файла для логирования
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client.log')

# создание потоков вывода логов
STREAM_HANDLER = logging.StreamHandler()  # (по умолчанию sys.stderr)
STREAM_HANDLER.setFormatter(CLIENT_FORMATTER)
STREAM_HANDLER.setLevel(logging.DEBUG)
LOG_FILE = logging.FileHandler(PATH, encoding=ENCODING)
LOG_FILE.setFormatter(CLIENT_FORMATTER)

# создание и настройка регистратора
LOGGER = logging.getLogger('client')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOGGING_LEVEL)

# отладка
if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
