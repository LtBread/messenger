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

# инициализация клиентского логера
logger = logging.getLogger('client')


class ClientSender(threading.Thread):
    """ Класс формирования и отправки сообщений на сервер и взаимодействия с пользователем """

    def __init__(self, account_name, sock):
        super().__init__()
        self.account_name = account_name
        self.sock = sock

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

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            logger.info(f'Отправлено сообщение для пользователя {to_user}')
        except Exception as e:
            print(e)
            logger.critical('Что-то пошло не так. Соединение с сервером разорвано.')
            exit(1)

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
                send_message(self.sock, self.create_exit_message())
                print('Завершение соединения')
                logger.info('Завершение работы по команде пользователя')
                time.sleep(0.5)  # Задержка необходима, чтобы успело уйти сообщение о выходе
                break
            else:
                print('Команда не распознана, help - вывести поддерживаемы команды')

    def print_help(self):
        """ Выводит справку по использованию """
        print('Поддерживаемые команды:\n'
              'message - отправить сообщение. Адресат и текст будут запрошены отдельно\n'
              'help - вывести поддерживаемые команды\n'
              'exit - выход из программы\n')


class ClientReader(threading.Thread):
    """
    Класс приёма сообщений, принимает сообщения, выводит в консоль.
    Завершается при потере соединения
    """
    def __init__(self, account_name, sock):
        super().__init__()
        self.account_name = account_name
        self.sock = sock

    def run(self):
        """ Обрабатывает сообщения других пользователей, поступающих от сервера """
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message \
                        and message[ACTION] == MESSAGE \
                        and SENDER in message \
                        and DESTINATION in message \
                        and MESSAGE_TEXT in message \
                        and message[DESTINATION] == self.account_name:
                    # print(f'Получено сообщение от пользователя {message[SENDER]}: \n{message[MESSAGE_TEXT]}')
                    logger.info(f'Получено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Получено некорректное сообщение от сервера: {message}')
            except IncorrectDataRecivedError:
                logger.error(f'Не удалось декодировать полученное сообщение')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical(f'Потеряно соединение с сервером')
                break


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
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_anc(get_message(transport))
        logger.info(f'Установлено соединение с сервером. Принят ответ от сервера: {answer}')
        # print('Установлено соединение с сервером')
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
        # ОСНОВНОЙ ЦИКЛ
        # если соединение с сервером установлено корректно, запуск клиентского потока приёма сообщений
        module_receiver = ClientReader(client_name, transport)
        module_receiver.daemon = True
        module_receiver.start()

        # затем запуск потока отправки сообщений и взаимодействия с пользователем
        module_sender = ClientSender(client_name, transport)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Потоки в работе')

        # Watchdog - если один из потоков завершён (по разрыву соединения иди по команде exit):
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
