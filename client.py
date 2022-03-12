import sys
import json
import time
import logging
from socket import socket, AF_INET, SOCK_STREAM

import logs.config_client_log
from errors import ReqFileMissingError
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT
from common.utils import get_message, send_message

# инициализация клиентского логера
CLIENT_LOGGER = logging.getLogger('client')


def create_presence(account_name='Guest'):
    """
    Генерирует запрос о присутствии клиента,
    формирует сообщение в виде словаря для отправки серверу и возвращает его
    :param account_name:
    :return:
    """
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


def process_anc(message):
    """
    Разбирает ответ сервера:
    получает ответ сервера и возвращает строку с результатом
    :param message:
    :return:
    """
    CLIENT_LOGGER.debug(f'Разбор сообщение от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ReqFileMissingError(RESPONSE)


def main():
    """
    Загружает параметры командной строки,
    создаёт сокет, отправляет сообщение серверу и получает ответ
    :return:
    """

    # считывание порта и адреса из командной строки
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if not 1023 < server_port < 65536:
            raise ValueError(server_port)
        CLIENT_LOGGER.info(f'Запущен клиент с параметрами: адрес сервера: {server_address}, порт: {server_port}')
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
        CLIENT_LOGGER.info(f'Скрипт запущен без одного или нескольких аргументов, '
                           f'некоторые параметры заданы по умолчанию: {server_address} : {server_port}')
    except ValueError as e:
        CLIENT_LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: {e.args[0]}. Клиент завершается')
        sys.exit(1)

    # инициализация сокета и обмен
    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((server_address, server_port))
    message_to_server = create_presence()
    send_message(transport, message_to_server)
    try:
        answer = process_anc(get_message(transport))
        CLIENT_LOGGER.info(f'Принят ответ от сервера: {answer}')
        print(answer)
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удалось декодировать полученную строку JSON')
    except ReqFileMissingError as missing_error:
        CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(f'Не удалось подключиться к северу {server_address}: {server_port}, '
                               f'конечный хост отверг запрос на подключение')


if __name__ == '__main__':
    main()
