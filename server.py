import argparse
import select
import threading
import configparser
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from PyQt5.QtCore import QTimer

from common.variables import *
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import Port
from common.metaclasses import ServerVerifier
from server.server_database import ServerDB
from server_gui import *

# инициализация клиентского логера
logger = logging.getLogger('server')

# Флаг, что был подключён новый пользователь, нужен чтобы не мучить БД постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


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
        global new_connection
        self.init_socket()

        # основной цикл сервера
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
            except OSError as e:  # ошибка сокета
                logger.error(f'Ошибка работы с сокетами: {e}')
                print(e.errno)  # The error number returns None because it's just a timeout

            # если есть сообщения в ecv_data_list, то они добавляются в словарь, если нет, клиент исключается
            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except OSError:  # поиск и удаление клиента из словаря клиентов и из БД
                        logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
                        with conflag_lock:
                            new_connection = True

            # если есть сообщения, обрабатывается каждое
            for message in self.messages:
                try:
                    self.process_message(message, send_data_list)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError) as e:
                    logger.info(f'Связь с клиентом {message[DESTINATION]} потеряна, '
                                f'ошибка {e}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
                    del self.names[message[DESTINATION]]
                    with conflag_lock:
                        new_connection = True
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
        global new_connection
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
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        # если это сообщение, то добавляет в очередь сообщений, ответ теперь требуется
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message \
                and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.messages.append(message)
                self.database.process_message(message[SENDER], message[DESTINATION])
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере'
                send_message(client, response)
            return

        # если клиент выходит
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            logger.info(f'Клиент {message[ACCOUNT_NAME]} вежливо отключился')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return

        # если это запрос списка контактов клиента
        elif ACTION in message \
                and message[ACTION] == GET_CONTACTS \
                and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        # если это добавление контакта
        elif ACTION in message \
                and message[ACTION] == ADD_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # если это удаление контакта
        elif ACTION in message \
                and message[ACTION] == REMOVE_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # если это запрос от известных пользователей
        elif ACTION in message \
                and message[ACTION] == USERS_REQUEST \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_message(client, response)

        # иначе Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен'
            send_message(client, response)
            return


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
def arg_parser(default_port, default_address):
    """ Парсер аргументов командной строки """
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


def main():
    """ Основная функция работы сервера """
    # загрузка файла конфигурации сервера
    config = config_load()

    # загружает параметры командной строки
    listen_address, listen_port = arg_parser(
        config['SETTINGS']['default_port'],
        config['SETTINGS']['listen_address']
    )

    # инициализация БД
    database = ServerDB(os.path.join(
        config['SETTINGS']['database_path'],
        config['SETTINGS']['database_file']
    ))

    # создание  и запуск экземпляра класса Server
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # создание графического окружения сервера
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # настройка параметров окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        """ Функция, обновляющая список подключенных клиентов,
        проверяет флаг подключения
        и, если надо, обновляет список
        """
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        """ Функция, создающая окно со статистикой клиентов """
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        """ Функция, создающая окно с настройками сервера """
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['database_path'])
        config_window.db_file.insert(config['SETTINGS']['database_file'])
        config_window.port.insert(config['SETTINGS']['default_port'])
        config_window.ip.insert(config['SETTINGS']['listen_address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        """ Функция сохранения настроек """
        global config_window
        message = QMessageBox()
        config['SETTINGS']['database_path'] = config_window.db_path.text()
        config['SETTINGS']['database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['listen_address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['default_port'] = str(port)
                print(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    config.write(conf)
                    message.information(config_window, 'OK', 'Настройки успешно сохранены')
            else:
                message.warning(config_window, 'Ошибка', 'Несуществующий порт')

    # таймер, обновляющий список раз в указанное время
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # связывание кнопок
    main_window.refresh_btn.triggered.connect(list_update)
    main_window.show_history_btn.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # запуск GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
