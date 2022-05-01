import binascii
import sys
import json
import time
import threading
import hmac
from socket import socket, AF_INET, SOCK_STREAM

import hashlib
from PyQt5.QtCore import pyqtSignal, QObject

from common.errors import ServerError
from common.variables import *
from common.utils import get_message, send_message

sys.path.append('../')

logger = logging.getLogger('client')
sock_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    """ Этот класс отвечает за взаимодействие с сервером """
    # сигнал - новое сообщение
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    # сигнал - потеря соединения
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database  # работа с БД
        self.username = username  # имя пользователя
        self.transport = None  # сокет для работы с сервером
        self.connection_init(port, ip_address)  # установка соединения
        self.passwd = passwd
        self.keys = keys

        # обновление списка известных пользователей и контактов
        try:
            self.users_list_update()
            self.contacts_list_update()
        except OSError as e:
            if e.errno:
                logger.critical('Потеряно соединение с сервером')
                raise ServerError('Потеряно соединение с сервером')
            logger.error('Таймаут соединения при обновлении списков пользователей')
        except json.JSONDecodeError:
            logger.critical('Потеряно соединение с сервером')
            raise ServerError('Потеряно соединение с сервером')
        self.running = True  # флаг продолжения работы сервера

    def connection_init(self, port, ip_address):
        """ Функция инициализации соединения с сервером """
        # инициализация сокета и сообщение серверу о присутствии
        self.transport = socket(AF_INET, SOCK_STREAM)

        # таймаут необходим для освобождения сокета
        self.transport.settimeout(5)

        # пять стуков в дверь сервера
        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения № {i + 1}')
            try:
                self.transport.connect((ip_address, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                logger.debug('Connection established')
                break
            time.sleep(1)

        # если не достучались - исключение
        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')
        logger.debug('Соединение с сервером установлено')

        # Запускаем процедуру авторизации
        # Получаем хэш пароля
        passwd_bytes = self.passwd.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        logger.debug(f'Passwd hash ready: {passwd_hash_string}')

        # Получаем публичный ключ и декодируем его из байтов
        pubkey = self.keys.publickey().export_key().decode('ascii')

        # Авторизируемся на сервере
        with sock_lock:
            presence = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pubkey
                }
            }
            logger.debug(f'Presence message = {presence}')
            # привет серверу
            try:
                send_message(self.transport, presence)
                ans = get_message(self.transport)
                logger.debug(f'Server response = {ans}')
                # Если сервер вернул ошибку, бросаем исключение
                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        # Если всё нормально, то продолжаем процедуру авторизации
                        ans_data = ans[DATA]
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = RESPONSE_511
                        my_ans[DATA] = binascii.b2a_base64(digest).decode('ascii')
                        send_message(self.transport, my_ans)
                        self.process_server_ans(get_message(self.transport))
            except (OSError, json.JSONDecodeError):
                logger.critical('Потеряно соединение с сервером')
                raise ServerError('Потеряно соединение с сервером')
            # logger.info('Сервер принял сообщение о присутствии. Соединение установлено')

    # def create_presence(self):
    #     """
    #     Генерирует запрос о присутствии клиента,
    #     формирует сообщение в виде словаря для отправки серверу и возвращает его
    #     """
    #     out = {
    #         ACTION: PRESENCE,
    #         TIME: time.time(),
    #         USER: {ACCOUNT_NAME: self.username}
    #     }
    #     logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.username}')
    #     return out

    def process_server_ans(self, message):
        """ Функция, обрабатывающая сообщение от сервера """
        logger.debug(f'Разбор сообщения: {message}')

        # если это подтверждение
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            elif message[RESPONSE] == 205:
                self.users_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                logger.debug(f'Принят неизвестный код ответа: {message[RESPONSE]}')

        # если это сообщение от пользователя, то оно добавляется в БД и подаётся сигнал о новом сообщении
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and SENDER in message \
                and DESTINATION in message \
                and MESSAGE_TEXT in message \
                and message[DESTINATION] == self.username:
            logger.debug(f'Получено сообщение от пользователя {message[SENDER]}: '
                         f'{message[MESSAGE_TEXT]}')
            # self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message)

    def contacts_list_update(self):
        """ Функция, обновляющая список контактов с сервера """
        self.database.contacts_clear()
        logger.debug(f'Запрос списка контактов для пользователя {self.username}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        logger.debug(f'Сформирован запрос {req}')
        with sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        logger.debug(f'получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов')

    def users_list_update(self):
        """ Функция обновления таблицы известных пользователей """
        logger.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            logger.error('Не удалось обновить список известных пользователей')

    def key_request(self, user):
        """ Метод, запрашивающий с сервера публичный ключ пользователя """
        logger.debug(f'Запрос публичного ключа для {user}')
        req = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: user
        }
        with sock_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 511:
            return ans[DATA]
        else:
            logger.error(f'Не удалось получить ключ собеседника {user}')

    def add_contact(self, contact):
        """ Функция, сообщающая серверу о добавлении контакта """
        logger.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with sock_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def remove_contact(self, contact):
        """ Функция удаления контакта на сервере """
        logger.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with sock_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def transport_shutdown(self):
        """ Функция закрытия соединения """
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with sock_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
            logger.debug('Сокет завершает работу')
            time.sleep(0.5)

    def send_message(self, to, message):
        """ Функция отправки сообщения на сервер """
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        # необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        """ Метод, содержащий основной цикл работы транспортного потока """
        logger.debug('Запущен процесс приёма сообщений с сервера')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет. Если не сделать тут задержку,
            # то отправка может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            message = None
            with sock_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as e:
                    if e.errno:
                        # выход по таймауту вернёт номер ошибки err.errno равный None
                        # поэтому, при выходе по таймауту мы сюда попросту не попадём
                        logger.critical(f'Потеряно соединение с сервером')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.error(f'Потеряно соединение с сервером')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.transport.settimeout(5)

            # если сообщение получено, то вызываем функцию-обработчик
            if message:
                logger.debug(f'Принято сообщение с сервера {message}')
                self.process_server_ans(message)
