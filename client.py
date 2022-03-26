import sys
import argparse
import json
import time
import logging
import threading
from socket import socket, AF_INET, SOCK_STREAM

import logs.config_client_log
from errors import ReqFileMissingError, ServerError, IncorrectDataRecivedError
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, MESSAGE, SENDER, MESSAGE_TEXT, EXIT, DESTINATION
from common.utils import get_message, send_message
from logs.utils_log_decorator import log

# инициализация клиентского логера
LOGGER = logging.getLogger('client')


@log
def create_exit_message(account_name):
    """ Создаёт словарь с сообщением о выходе """
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }


@log
def message_from_server(sock, my_username):
    """ Обрабатывает сообщения других пользователей, поступающих от сервера """
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message and \
                    MESSAGE_TEXT in message and message[DESTINATION] == my_username:
                # print(f'Получено сообщение от пользователя {message[SENDER]}: \n{message[MESSAGE_TEXT]}')
                LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]}')
            else:
                LOGGER.error(f'Получено некорректное сообщение от сервера: {message}')
        except IncorrectDataRecivedError:
            LOGGER.error(f'Не удалось декодировать полученное сообщение')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            LOGGER.critical(f'Потеряно соединение с сервером')
            break


@log
def create_message(sock, account_name='Guest'):
    """ Запрашивает текст сообщения и возвращает его, по команде завершает работу """
    to_user = input('Введите имя получателя сообщения: ')
    message = input('Введите сообщение для отправки: ')
    # if message == 'q':
    #     sock.close()
    #     LOGGER.info('Завершение работы по команде пользователя')
    #     sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
    try:
        send_message(sock, message_dict)
        LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
    except Exception as e:
        print(e)
        LOGGER.critical('Что-то пошло не так. Соединение с сервером разорвано.')
        sys.exit(1)


def print_help():
    """ Выводит справку по использованию """
    print('Поддерживаемые команды:\n'
          'message - отправить сообщение. Адресат и текст будут запрошены отдельно\n'
          'help - вывести поддерживаемые команды\n'
          'exit - выход из программы')


@log
def user_interactive(sock, username):
    """ Функция взаимодействия с пользователем. Запрашивает команды, отправляет сообщения """
    print_help()
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_message(sock, create_message(username))
            print('Завершение соединения')
            LOGGER.info('Завершение работы по команде пользователя')
            time.sleep(0.5)  # Задержка необходима, чтобы успело уйти сообщение о выходе
            break
        else:
            print('Команда не распознана, help - вывести поддерживаемы команды')


@log
def create_presence(account_name):
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
    LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
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
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Попытка запуска клиента с недопустимым портом: {server_port}. Сервер завершается')
        sys.exit(1)
    # if client_name not in ('listen', 'send'):
    #     LOGGER.critical(f'Указан недопустимый режим работы клиента {client_name}, '
    #                     f'допустимые режимы: listen, send')
    #     sys.exit(1)
    return server_address, server_port, client_name


def main():
    """
    Загружает параметры командной строки,
    создаёт сокет, отправляет сообщение серверу и получает ответ
    """
    server_address, server_port, client_name = arg_parser()
    print(f'Консольный менеджер. Клиентский модуль. Имя пользователя: {client_name}')
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    LOGGER.info(f'Запущен клиент с параметрами: адрес сервера: {server_address}, '
                f'порт: {server_port}, имя пользователя: {client_name}')

    # # считывание порта и адреса из командной строки
    # try:
    #     server_address = sys.argv[1]
    #     server_port = int(sys.argv[2])
    #     if not 1023 < server_port < 65536:
    #         raise ValueError(server_port)
    #     LOGGER.info(f'Запущен клиент с параметрами: адрес сервера: {server_address}, порт: {server_port}')
    # except IndexError:
    #     server_address = DEFAULT_IP_ADDRESS
    #     server_port = DEFAULT_PORT
    #     LOGGER.info(f'Скрипт запущен без одного или нескольких аргументов, '
    #                 f'некоторые параметры заданы по умолчанию: {server_address} : {server_port}')
    # except ValueError as e:
    #     LOGGER.critical(f'Попытка запуска клиента с неподходящим номером порта: {e.args[0]}. Клиент завершается')
    #     sys.exit(1)

    # инициализация сокета и обмен
    try:
        transport = socket(AF_INET, SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_anc(get_message(transport))
        LOGGER.info(f'Установлено соединение с сервером. Принят ответ от сервера: {answer}')
        # print('Установлено соединение с сервером')
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную строку JSON')
        sys.exit(1)
    except ServerError as e:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {e.text}')
        sys.exit(1)
    except ReqFileMissingError as missing_error:
        LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionRefusedError):
        LOGGER.critical(f'Не удалось подключиться к северу {server_address}: {server_port}, '
                        f'конечный хост отверг запрос на подключение')
        sys.exit(1)
    else:
        # ОСНОВНОЙ ЦИКЛ
        # если соединение с сервером установлено корректно, запуск клиентского потока приёма сообщений
        receiver = threading.Thread(target=message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        # затем запуск потока отправки сообщений и взаимодействия с пользователем
        user_interface = threading.Thread(target=user_interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()
        LOGGER.debug('Потоки в работе')

        # Watchdog - если один из потоков завершён (по разрыву соединения иди по команде exit):
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break

        # if client_name == 'send':
        #     print('Отправка сообщения')
        # else:
        #     print('Прием сообщения')
        # while True:
        #     if client_name == 'send':
        #         try:
        #             send_message(transport, create_message(transport))
        #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
        #             LOGGER.error(f'Соединение с сервером {server_address} неожиданно разорвано')
        #             sys.exit(1)
        #     if client_name == 'listen':
        #         try:
        #             message_from_server(get_message(transport))
        #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
        #             LOGGER.error(f'Соединение с сервером {server_address} неожиданно разорвано')
        #             sys.exit(1)


if __name__ == '__main__':
    main()
