import os
import sys
import argparse
import configparser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from common.variables import *
from common.decorators import log
from server.core import MessageProcessor
from server.server_database import ServerDB
from server.main_window import MainWindow

# инициализация клиентского логера
logger = logging.getLogger('server')


@log
def arg_parser(default_port, default_address):
    """ Парсер аргументов командной строки """
    logger.debug(f'Инициализация парсера аргументов командной строки: {sys.argv}')

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    logger.debug('Аргументы успешно загружены')
    return listen_address, listen_port, gui_flag


@log
def config_load():
    """ Загрузка файла конфигурации сервера """
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # если конфиг загружен правильно - запуск, иначе конфиг по умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'listen_address', '')
        config.set('SETTINGS', 'database_path', '')
        config.set('SETTINGS', 'database_file', 'server_database.db3')
        return config


@log
def main():
    """ Основная функция работы сервера """
    # загрузка файла конфигурации сервера
    config = config_load()

    # загружает параметры командной строки
    listen_address, listen_port, gui_flag = arg_parser(
        config['SETTINGS']['default_port'],
        config['SETTINGS']['listen_address']
    )

    # инициализация БД
    database = ServerDB(os.path.join(
        config['SETTINGS']['database_path'],
        config['SETTINGS']['database_file']
    ))

    # создание  и запуск экземпляра класса Server
    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Если  указан параметр без GUI то запускаем простенький обработчик консольного ввода
    if gui_flag:
        while True:
            command = input('введите exit для завершения работы сервера')
            if command == 'exit':
                server.running = False
                server.join()
                break
    else:
        # создание графического окружения сервера
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)
        # запуск GUI
        server_app.exec_()
        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()
