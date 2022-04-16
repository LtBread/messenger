import sys
import argparse
import time
import select
import logging
import threading
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

import logs.config_server_log
from errors import IncorrectDataRecivedError
from common.variables import *
from common.utils import get_message, send_message
from logs.utils_log_decorator import log
from descriptors import Port
from metaclasses import ServerVerifier
from server_database import ServerDB

# инициализация клиентского логера
logger = logging.getLogger('server')


class Server(threading.Thread, metaclass=ServerVerifier):
    """Основной_класс_сервера"""
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        super().__init__()
        self.addr = listen_address
        self.port = listen_port
        self.clients = []
        self.messages = []
        self.names = dict()  # Словарь для сопоставленных имён и соответствующих им сокетов
        self.database = database

    def init_socket(self):
        logger.info(
            f'Сервер в работе, порт для подключений {self.port}, '
            f'адрес, с которого принимаются подключения {self.addr}, '
            f'если адрес не указан, принимаются соединения с любых адресов.'
        )

        # подготовка сокета
        transport = socket(AF_INET, SOCK_STREAM)
        transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # это чтобы не ждать 3 минуты, пока освободиться порт
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)  # ВАЖНО! это нужно для обслуживания более одного клиента

        # прослушивание сокета
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def run(self):
        # инициализация сокета
        self.init_socket()

        while True:
            # ожидание подключения, если таймаут вышел, срабатывает исключение
            try:
                client, client_address = self.sock.accept()
            except OSError as e:
                # print(e.errno)  # The error number returns None because it's just a timeout
                """ ТУТ ДОПИЛИТЬ """
                pass
            else:
                logger.info(f'Установлено соединение с {client_address}')
                self.clients.append(client)

            recv_data_list = []
            send_data_list = []
            err_list = []
            # проверка наличия ждущих клиентов
            try:
                if self.clients:
                    recv_data_list, send_data_list, err_list = select.select(self.clients, self.clients, [], 0)
            except OSError as e:
                print(e.errno)  # The error number returns None because it's just a timeout
                """ ТУТ ДОПИЛИТЬ """
                pass

            # если есть сообщения в ecv_data_list, то они добавляются в словарь, если нет, клиент исключается
            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except Exception:  # Слишком широкое исключение
                        logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера')
                        self.clients.remove(client_with_message)

            # если есть сообщения, обрабатывается каждое
            for message in self.messages:
                try:
                    self.process_message(message, send_data_list)
                except Exception as e:  # Слишком широкое исключение
                    logger.info(f'Связь с клиентом {message[DESTINATION]} потеряна, '
                                f'ошибка {e}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает сообщение-словарь,
        список зарегистрированных пользователей и слушающие сокеты. Ничего не возвращает
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}')
        elif message[DESTINATION] in self.names and self.names[DESTINATION] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(f'Пользователь {message[DESTINATION]} не зарегистрирован, отправка сообщения невозможна')

    def process_client_message(self, message, client):
        """
        Обрабатывает сообщения от клиентов, принимает словарь, проверяет,
        отправляет словарь-ответ в случае необходимости
        """
        logger.debug(f'Разбор сообщения от клиента: {message}')
        # если это сообщение о присутствии, принимает и отвечает
        if ACTION in message \
                and message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message:
            # если такой пользователь не зарегистрирован, он регистрируется, иначе соединение завершается
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()

                # регистрация пользователя в БД
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)

                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # если это сообщение, то добавляет в очередь сообщений, ответ не требуется
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # если клиент выходит
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        # иначе Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен'
            send_message(client, response)
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
    return listen_address, listen_port


def print_help():
    print('Поддерживаемые команды:\n'
          'users - список всех пользователей\n'
          'connected - список подключенных пользователей\n'
          'loghist - история входов пользователя\n'
          'exit - завершение работы сервера\n'
          'help - вызов справки по поддерживаемым командам')


def main():
    """ Основная функция работы сервера """
    listen_address, listen_port = arg_parser()  # загружает параметры командной строки

    # инициализация БД
    database = ServerDB()

    # создание экземпляра класса Server
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    print_help()

    # основной цикл сервера
    while True:
        command = input('Введите команду: ')
        if command == 'help':
            print_help()
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            if not database.active_users_list():
                print('Список пуст!')
            for user in sorted(database.active_users_list()):
                print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, '
                      f'время установки соединения: {user[3]}')
        elif command == 'loghist':
            name = input('Введите имя пользователя для просмотра истории.'
                         'Для вывода всей истории оставьте поле пустым: ')
            if not database.login_history(name):
                print('Пользователь не зарегистрирован!')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]}, вход с: {user[1]}:{user[2]}, '
                      f'время входа: {user[3]}')
        elif command == 'exit':
            break
        else:
            print('Команда не распознана!')
            print_help()


if __name__ == '__main__':
    main()
