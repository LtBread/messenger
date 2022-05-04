import sys
import argparse
import json
import time
import threading
from socket import socket, AF_INET, SOCK_STREAM
from PyQt5.QtWidgets import QApplication

from common.errors import ReqFileMissingError, ServerError, IncorrectDataRecivedError
from common.variables import *
from common.utils import get_message, send_message
from logs.utils_log_decorator import log
from metaclasses import ClientVerifier
from client.client_database import ClientDB
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNamedDialog

# инициализация клиентского логера
logger = logging.getLogger('client')


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
        logger.critical(f'Попытка запуска клиента с недопустимым портом: {server_port}. Сервер завершается')
        exit(1)

    return server_address, server_port, client_name


if __name__ == '__main__':
    server_address, server_port, client_name = arg_parser()

    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке, то запросим его
    if not client_name:
        start_dialog = UserNamedDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект.
        # Иначе - выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    # Записываем логи
    logger.info(f'Запущен клиент с параметрами: адрес сервера: {server_address}, '
                f'порт: {server_port}, имя пользователя: {client_name}')

    # Инициализация БД
    database = ClientDB(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as e:
        print(e.text)
        exit(1)
    # transport.setDaemon(True)  # setDaemon() is deprecated, set the daemon attribute instead
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат alpaca release - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()
