import sys
import argparse
import json
import time
import logging
import threading
from socket import socket, AF_INET, SOCK_STREAM

import logs.config_client_log
from errors import ReqFileMissingError, ServerError, IncorrectDataRecivedError
from common.variables import *
from common.utils import get_message, send_message
from logs.utils_log_decorator import log
from metaclasses import ClientVerifier
from client_database import ClientDB

# инициализация клиентского логера
logger = logging.getLogger('client')

# блокировки
sock_lock = threading.Lock()
database_lock = threading.Lock()


# Класс формирования и отправки сообщений на сервер и взаимодействия с пользователем
class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        super().__init__()
        self.account_name = account_name
        self.sock = sock
        self.database = database

    def create_exit_message(self):
        """ Создаёт словарь с сообщением о выходе """
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        """ Запрашивает текст сообщения и возвращает его, по команде завершает работу """
        to_user = input('Введите имя получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        # проверка существования получателя
        with database_lock:
            if not self.database.check_user(to_user):
                logger.error(f'Попытка отправить сообщение незарегистрированному получателю: {to_user}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # сохранение сообщения в БД
        with database_lock:
            self.database.save_message(self.account_name, to_user, message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя {to_user}')
            except OSError as e:
                if e.errno:
                    logger.critical('Потеряно соединение с сервером')
                    exit(1)
                else:
                    logger.error('Не удалось передать сообщение. Таймаут соединения')

    def run(self):
        """ Функция взаимодействия с пользователем. Запрашивает команды, отправляет сообщения """
        self.print_help()
        while True:
            command = input('Введите команду: ')

            if command == 'message':
                self.create_message()

            elif command == 'help':
                self.print_help()

            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception as e:
                        print(e)
                        pass
                    print('Завершение соединения')
                    logger.info('Завершение работы по команде пользователя')
                time.sleep(0.5)  # Задержка необходима, чтобы успело уйти сообщение о выходе
                break

            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, help - вывести поддерживаемы команды')

    def print_help(self):
        """ Выводит справку по использованию """
        print('Поддерживаемые команды:\n'
              'message - отправить сообщение. Адресат и текст будут запрошены отдельно\n'
              'contacts - вывести список контактов\n'
              'edit - отредактировать список контактов\n'
              'history - вывести историю сообщений\n'
              'help - вывести поддерживаемые команды\n'
              'exit - выход из программы\n')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out,\n'
                    'чтобы показать все сообщения, оставьте поле пустым: ')
        with database_lock:

            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')

            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')

            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, '
                          f'пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')

        if ans == 'del':
            edit = input('Введите имя удаляемого контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта')

        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер')


# Класс приёма сообщений, принимает сообщения, выводит в консоль. Завершается при потере соединения
class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        super().__init__()
        self.account_name = account_name
        self.sock = sock
        self.database = database

    def run(self):
        """ Обрабатывает сообщения других пользователей, поступающих от сервера """
        while True:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # Если не сделать тут задержку,
            # то второй поток может достаточно долго ждать освобождения сокета
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    logger.error(f'Не удалось декодировать полученное сообщение')
                except OSError as e:
                    if e.errno:
                        logger.critical(f'Потеряно соединение с сервером')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером')
                    break
                else:
                    if ACTION in message \
                            and message[ACTION] == MESSAGE \
                            and SENDER in message \
                            and DESTINATION in message \
                            and MESSAGE_TEXT in message \
                            and message[DESTINATION] == self.account_name:
                        print(f'Получено сообщение от пользователя {message[SENDER]}: \n{message[MESSAGE_TEXT]}')

                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.account_name,
                                                           message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                logger.error('Ошибка взаимодействия с БД')
                        logger.info(f'Получено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Получено некорректное сообщение от сервера: {message}')


@log
def create_presence(account_name):
    """
    Генерирует запрос о присутствии клиента,
    формирует сообщение в виде словаря для отправки серверу и возвращает его
    """
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {ACCOUNT_NAME: account_name}
    }
    logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


@log
def process_response_anc(message):
    """
    Разбирает ответ сервера на сообщение о присутствии,
    возвращает 200 в случае успеха, исключение - в случае ошибки
    """
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400: {message[ERROR]}')
    raise ReqFileMissingError(RESPONSE)


def contacts_list_request(sock, name):
    """ Функция запроса списка контактов """
    logger.debug(f'Запрос списка контактов пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    logger.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    """ Функция добавления пользователя в список контактов """
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Контакт создан')


def user_list_request(sock, username):
    """ Запрос списка известных пользователей """
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def remove_contact(sock, username, contact):
    """ Удаление пользователя из списка контактов """
    logger.debug(f'Удаление контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления контакта')
    print('Контакт удалён')


def database_load(sock, database, username):
    """ Инициализатор БД.
    Загружает данные в БД c сервера
    """
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка известных пользователей')
    else:
        database.add_users(users_list)

    # загрузка списка контактов
    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка контактов')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


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


def main():
    """
    Загружает параметры командной строки,
    создаёт сокет, отправляет сообщение серверу и получает ответ
    """
    print(f'Консольный менеджер. Клиентский модуль')

    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    logger.info(f'Запущен клиент с параметрами: адрес сервера: {server_address}, '
                f'порт: {server_port}, имя пользователя: {client_name}')

    # инициализация сокета и обмен
    try:
        transport = socket(AF_INET, SOCK_STREAM)

        # Таймаут 1 секунда, необходим для освобождения сокета.
        transport.settimeout(1)

        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_anc(get_message(transport))
        logger.info(f'Установлено соединение с сервером. Принят ответ от сервера: {answer}')
        print('Установлено соединение с сервером')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную строку JSON')
        exit(1)
    except ServerError as e:
        logger.error(f'При установке соединения сервер вернул ошибку: {e.text}')
        exit(1)
    except ReqFileMissingError as missing_error:
        logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionRefusedError):
        logger.critical(f'Не удалось подключиться к северу {server_address}: {server_port}, '
                        f'конечный хост отверг запрос на подключение')
        exit(1)
    else:
        # Инициализация БД
        database = ClientDB(client_name)
        database_load(transport, database, client_name)

        # ОСНОВНОЙ ЦИКЛ
        # если соединение с сервером установлено корректно, запуск потока взаимодействия с пользователем
        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Поток в работе')

        # запуск потока приёма сообщений
        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()

        # Watchdog - если один из потоков завершён (по разрыву соединения иди по команде exit):
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
