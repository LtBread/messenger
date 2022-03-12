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
    DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE, MESSAGE, MESSAGE_TEXT, SENDER
from common.utils import get_message, send_message
from logs.utils_log_decorator import log

# инициализация клиентского логера
LOGGER = logging.getLogger('server')


@log
def process_client_message(message, message_list, client):
    """
    Обрабатывает сообщения от клиентов, принимает словарь, проверяет,
    формирует ответ клиенту в виде строки с "кодом ответа сервера"
    :param message:
    :param message_list
    :return:
    """
    LOGGER.debug(f'Разбор сообщения от клиента: {message}')
    # если это сообщение о присутствии, принимает и отвечает
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        send_message(client, {RESPONSE: 200})
        return
    # если это сообщение, то добавляет в очередь сообщений, ответ не требуется
    elif ACTION in message and message[ACTION] == MESSAGE and TIME in message \
            and MESSAGE_TEXT in message:
        message_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
        return
    # иначе Bad request
    else:
        send_message(client, {RESPONSE: 400, ERROR: 'Bad request'})
        # send_message(client, {RESPONDEFAULT_IP_ADDRESSSE: 400, ERROR: 'Bad request'})
        return


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

    # # считывание порта из командной строки
    # try:
    #     if '-p' in sys.argv:
    #         listen_port = int(sys.argv[sys.argv.index('-p') + 1])
    #     else:
    #         listen_port = DEFAULT_PORT
    #     if not 1023 < listen_port < 65536:
    #         raise ValueError(listen_port)
    #     LOGGER.info(f'Сервер в работе, порт: {listen_port}')
    # except IndexError:
    #     # print("You didn't specify a port in the parameter field '-p'")
    #     LOGGER.error(f'После параметра "-p" не указан порт. Сервер завершается')
    #     sys.exit(1)
    # except ValueError as e:
    #     LOGGER.critical(f'Попытка запуска сервера с недопустимым портом: {e.args[0]}. Сервер завершается')
    #     sys.exit(1)
    #
    # # считывание адреса из командной строки
    # try:
    #     if '-a' in sys.argv:
    #         listen_address = sys.argv[sys.argv.index('-a') + 1]
    #         LOGGER.info(f'Сервер в работе, адрес: {listen_address}')
    #     else:
    #         listen_address = ''
    #         LOGGER.info(f'Сервер в работе, слушает всех')
    # except IndexError:
    #     # print("You didn't specify a ip-address in the parameter field '-a'")
    #     LOGGER.error(f'После параметра "-a" не указан адрес. Сервер завершается')
    #     sys.exit(1)

    # инициализация сокета
    transport = socket(AF_INET, SOCK_STREAM)
    transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # это чтобы не ждать 3 минуты, пока освободиться порт
    transport.bind((listen_address, listen_port))
    transport.settimeout(1)  # ВАЖНО! это нужно для обслуживания более одного клиента

    clients = []  # клиенты
    messages = []  # сообщения клиентов

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
        except OSError:
            """ ТУТ ДОПИЛИТЬ """
            pass

        # если есть сообщения в ecv_data_list, то они добавляются в словарь, если нет, клиент исключается
        if recv_data_list:
            for client_with_message in recv_data_list:
                try:
                    process_client_message(get_message(client_with_message), messages, client_with_message)
                except:  # Слишком широкое исключение
                    LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера')
                    clients.remove(client_with_message)

            # если есть сообщения для отправки и ожидающие клиенты, то им отправляются эти сообщения
            if messages and send_data_list:
                message = {
                    ACTION: MESSAGE,
                    SENDER: messages[0][0],
                    TIME: time.time(),
                    MESSAGE_TEXT: messages[0][1]
                }
                del message[0]
                for waiting_client in send_data_list:
                    try:
                        send_message(waiting_client, message)
                    except:  # Слишком широкое исключение
                        LOGGER.info(f'Клиент {waiting_client.getpeername()} отключился от сервера')
                        waiting_client.close()
                        clients.remove(waiting_client)

    #         message_from_client = get_message(client)
    #         LOGGER.debug(f'Получено сообщение {message_from_client}')
    #         # print(message_from_client)
    #         response = process_client_message(message_from_client)
    #         LOGGER.info(f'Сформирован ответ клиенту {response}')
    #         send_message(client, response)
    #         LOGGER.debug(f'Соединение с клиентом {client_address} закрывается')
    #         client.close()
    #     except json.JSONDecodeError:
    #     LOGGER.error(f'Не удалось декодировать полученную строку JSON, полученную от'
    #                  f'{client_address}. Соединение закрывается')
    # except IncorrectDataRecivedError:
    # LOGGER.error(f'От клиента {client_address} приняты некорректные данные. Соединение закрывается')


if __name__ == '__main__':
    main()
