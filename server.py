import sys
import argparse
import time
import json
import select
import logging
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

import logs.config_server_log
from errors import IncorrectDataRecivedError
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE, MESSAGE, MESSAGE_TEXT, SENDER, RESPONSE_200, RESPONSE_400, DESTINATION, \
    EXIT
from common.utils import get_message, send_message
from logs.utils_log_decorator import log

# инициализация клиентского логера
LOGGER = logging.getLogger('server')


@log
def process_client_message(message, message_list, client, clients, names):
    """
    Обрабатывает сообщения от клиентов, принимает словарь, проверяет,
    отправляет словарь-ответ в случае необходимости
    """
    LOGGER.debug(f'Разбор сообщения от клиента: {message}')
    # если это сообщение о присутствии, принимает и отвечает
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
        # Если такой пользователь не зарегистрирован, он регистрируется, иначе соединение завершается
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    # если это сообщение, то добавляет в очередь сообщений, ответ не требуется
    elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
            and SENDER in message and MESSAGE_TEXT in message:
        message_list.append(message)
        return
    # если клиент выходит
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    # иначе Bad request
    else:
        response = RESPONSE_400
        response[ERROR] = 'Запрос некорректен'
        send_message(client, response)
        # send_message(client, {RESPONSE: 400, ERROR: 'Bad request'})
        # # send_message(client, {RESPONDEFAULT_IP_ADDRESSSE: 400, ERROR: 'Bad request'})
        return


@log
def process_message(message, names, listen_socks):
    """
    Функция адресной отправки сообщения определённому клиенту. Принимает сообщение-словарь,
    список зарегистрированных пользователей и слушающие сокеты. Ничего не возвращает
    """
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}')
    elif message[DESTINATION] in names and names[DESTINATION] not in listen_socks:
        raise ConnectionError
    else:
        LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован, отправка сообщения невозможна')


@log
def arg_parser():
    """ Парсер аргументов командной строки """
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    if not 1023 < listen_port < 65536:
        LOGGER.critical(f'Попытка запуска сервера с недопустимым портом: {listen_port}. Сервер завершается')
        sys.exit(1)
    return listen_address, listen_port


def main():
    """ Загружает параметры командной строки """
    listen_address, listen_port = arg_parser()

    LOGGER.info(
        f'Сервер в работе, порт для подключений {listen_port}, '
        f'адрес, с которого принимаются подключения {listen_address}, '
        f'если адрес не указан, принимаются соединения с любых адресов.'
    )

    # инициализация сокета
    transport = socket(AF_INET, SOCK_STREAM)
    transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # это чтобы не ждать 3 минуты, пока освободиться порт
    transport.bind((listen_address, listen_port))
    transport.settimeout(1)  # ВАЖНО! это нужно для обслуживания более одного клиента

    clients = []  # клиенты
    messages = []  # сообщения клиентов

    names = dict()  # {client_name: client_socket}

    # прослушивание порта
    transport.listen(MAX_CONNECTIONS)

    # ОСНОВНОЙ ЦИКЛ, обмен сообщениями с клиентом
    while True:
        # ожидание подключения, если таймаут вышел, срабатывает исключение
        try:
            client, client_address = transport.accept()
        except OSError as e:
            print(e.errno)  # The error number returns None because it's just a timeout
            """ ТУТ ДОПИЛИТЬ """
            pass
        else:
            LOGGER.info(f'Установлено соединение с {client_address}')
            clients.append(client)

        recv_data_list = []
        send_data_list = []
        err_list = []
        # проверка наличия ждущих клиентов
        try:
            if clients:
                recv_data_list, send_data_list, err_list = select.select(clients, clients, [], 0)
        except OSError as e:
            print(e.errno)  # The error number returns None because it's just a timeout
            """ ТУТ ДОПИЛИТЬ """
            pass

        # если есть сообщения в ecv_data_list, то они добавляются в словарь, если нет, клиент исключается
        if recv_data_list:
            for client_with_message in recv_data_list:
                try:
                    process_client_message(
                        get_message(client_with_message), messages, client_with_message, clients, names
                    )
                except Exception:  # Слишком широкое исключение
                    LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера')
                    clients.remove(client_with_message)

                # если есть сообщения, обрабатывается каждое
                for mes in messages:
                    try:
                        process_message(mes, names, send_data_list)
                    except Exception:  # Слишком широкое исключение
                        LOGGER.info(f'Связь с клиентом {mes[DESTINATION]} потеряна')
                        clients.remove(names[DESTINATION])
                        del names[DESTINATION]
                    messages.clear()

                # message = {
                #     ACTION: MESSAGE,
                #     SENDER: messages[0][0],
                #     TIME: time.time(),
                #     MESSAGE_TEXT: messages[0][1]
                # }
                # del messages[0]
                # for waiting_client in send_data_list:
                #     try:
                #         send_message(waiting_client, message)
                #     except:  # Слишком широкое исключение
                #         LOGGER.info(f'Клиент {waiting_client.getpeername()} отключился от сервера')
                #         waiting_client.close()
                #         clients.remove(waiting_client)


if __name__ == '__main__':
    main()
