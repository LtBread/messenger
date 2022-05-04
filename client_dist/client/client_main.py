import os
import sys
import argparse
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from Cryptodome.PublicKey import RSA

from client_dist.client.common.variables import *
from client_dist.client.common.errors import ServerError
from client_dist.client.common.decorators import log
from client_dist.client.client.client_database import ClientDB
from client_dist.client.client.client_transport import ClientTransport
from client_dist.client.client.main_window import ClientMainWindow
from client_dist.client.client.start_dialog import UserNamedDialog

# инициализация клиентского логера
logger = logging.getLogger('client')


@log
def arg_parser():
    """ Парсер аргументов командной строки """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        logger.critical(f'Попытка запуска клиента с недопустимым портом: {server_port}. Сервер завершается')
        exit(1)

    return server_address, server_port, client_name, client_passwd


@log
def main():
    """ Основная функция работы клиента """
    server_address, server_port, client_name, client_passwd = arg_parser()

    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке, то запросим его
    start_dialog = UserNamedDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект.
        # Иначе - выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            logger.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}')
        else:
            exit(0)

    # Записываем логи
    logger.info(f'Запущен клиент с параметрами: адрес сервера: {server_address}, '
                f'порт: {server_port}, имя пользователя: {client_name}')

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    logger.debug('Keys successfully loaded')

    # Инициализация БД
    database = ClientDB(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(
            server_port,
            server_address,
            database,
            client_name,
            client_passwd,
            keys)
        logger.debug('Transport ready')
    except ServerError as e:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', e.text)
        exit(1)
    # transport.setDaemon(True)  # setDaemon() is deprecated, set the daemon attribute instead
    transport.start()

    del start_dialog

    # Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат alpaca release - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
