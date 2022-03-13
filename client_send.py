import sys
import argparse
import json
import time
import logging
from socket import socket, AF_INET, SOCK_STREAM

import logs.config_client_log
from errors import ReqFileMissingError, ServerError
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, MESSAGE, SENDER, MESSAGE_TEXT
from common.utils import get_message, send_message
from logs.utils_log_decorator import log

# инициализация клиентского логера
LOGGER = logging.getLogger('client')


@log
def message_from_server(message):
    """ Обрабатывает сообщения других пользователей, поступающих от сервера """
    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message \
            and MESSAGE_TEXT in message:
        # print(f'Получено сообщение от пользователя {message[SENDER]}: \n{message[MESSAGE_TEXT]}')
        LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]}')
    else:
        LOGGER.error(f'Получено некорректное сообщение от сервера: {message}')


@log
def create_message(sock, account_name='Guest'):
    """ Запрашивает текст сообщения и возвращает его, по команде завершает работу """
    message = input('Введите сообщение для отправки или введите q для завершения заботы: ')
    if message == 'q':
        sock.close()
        LOGGER.info('Завершение работы по команде пользователя')
        sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
        MESSAGE_TEXT: message
    }
    LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
    return message_dict


@log
def create_presence(account_name='Guest'):
    """
    Генерирует запрос о присутствии клиента,
    формирует сообщение в виде словаря для отправки серверу и возвращает его
    """
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


@log
def process_response_anc(message):
    """
    Разбирает ответ сервера на сообщение о присутствии,
    возвращает 200 в случае успеха, исключение - в случае ошибки
    """
    LOGGER.debug(f'Разбор сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400: {message[ERROR]}')
    raise ReqFileMissingError(RESPONSE)


@log
def arg_parser():
    """ Парсер аргументов командной строки """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='listen', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode
    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Попытка запуска клиента с недопустимым портом: {server_port}. Сервер завершается')
        sys.exit(1)
    if client_mode not in ('listen', 'send'):
        LOGGER.critical(f'Указан недопустимый режим работы клиента {client_mode}, '
                        f'допустимые режимы: listen, send')
        sys.exit(1)
    return server_address, server_port, client_mode


def main():
    """
    Загружает параметры командной строки,
    создаёт сокет, отправляет сообщение серверу и получает ответ
    """
    server_address, server_port, client_mode = arg_parser()
    LOGGER.info(f'Запущен клиент с параметрами: адрес сервера: {server_address}, '
                f'порт: {server_port}, режим работы: {client_mode}')

    # инициализация сокета и обмен
    try:
        transport = socket(AF_INET, SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence())
        answer = process_response_anc(get_message(transport))
        LOGGER.info(f'Установлено соединение с сервером. Принят ответ от сервера: {answer}')
        # print(answer)
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную строку JSON')
        sys.exit(1)
    except ServerError as e:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {e.text}')
        sys.exit(1)
    except ReqFileMissingError as missing_error:
        LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except ConnectionRefusedError:
        LOGGER.critical(f'Не удалось подключиться к северу {server_address}: {server_port}, '
                        f'конечный хост отверг запрос на подключение')
        sys.exit(1)
    else:
        # ОСНОВНОЙ ЦИКЛ, если соединение с сервером установлено, происходит обмен согласно режиму
        if client_mode == 'send':
            print('Отправка сообщения')
        else:
            print('Прием сообщения')
        while True:
            if client_mode == 'send':
                try:
                    send_message(transport, create_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {server_address} неожиданно разорвано')
                    sys.exit(1)
            if client_mode == 'listen':
                try:
                    message_from_server(get_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {server_address} неожиданно разорвано')
                    sys.exit(1)


if __name__ == '__main__':
    main()
