import os
import sys
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import json
import select
import hmac
import binascii
import threading
import logging

from common.metaclasses import ServerVerifier
from common.descriptors import Port
from common.variables import *
from common.utils import send_message, get_message
from common.decorators import login_required

sys.path.append('../')

logger = logging.getLogger('server')


class MessageProcessor(threading.Thread):
    """ Основной класс сервера
    Принимает соединения, словари-пакеты от клиентов, обрабатывает сообщения
    Работает в качестве отдельного потока
    """
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        super().__init__()
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.sock = None
        self.clients = []
        self.listen_sockets = None
        self.error_sockets = None
        self.running = True
        self.names = dict()

    def run(self):
        """ Основной цикл потока """
        self.init_socket()
        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError as e:
                print(e)
            else:
                logger.info(f'Установлено соединение с {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_list = []
            send_data_list = []
            err_list = []
            # проверка наличия ждущих сокетов
            try:
                if self.clients:
                    recv_data_list, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0
                    )
            except OSError as e:
                logger.error(f'Ошибка работы с сокетами: ', e.errno)
            # прием сообщения, если ошибка - исключение клиента
            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as e:
                        logger.debug(f'Getting data from client exception', exc_info=e)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        """ Метод-обработчик клиента, с которым прервана связь """
        logger.info(f'Клиент {client.getpeername()} отключился от сервера')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        """ Метод инициализации сокета """
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

    def process_message(self, message, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает сообщение-словарь,
        список зарегистрированных пользователей и слушающие сокеты. Ничего не возвращает
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            try:
                send_message(self.names[message[DESTINATION]], message)
                logger.info(
                    f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}')
            except OSError:
                self.remove_client(message[DESTINATION])
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            logger.error(f'Связь с клиентом {message[DESTINATION]} была потеряна. Соединение закрыто')
            self.remove_client(self.names[message[DESTINATION]])
        else:
            logger.error(f'Пользователь {message[DESTINATION]} не зарегистрирован, отправка сообщения невозможна')

    @login_required
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
            self.autorize_user(message, client)

            # # если такой пользователь не зарегистрирован, он регистрируется, иначе соединение завершается
            # if message[USER][ACCOUNT_NAME] not in self.names.keys():
            #     self.names[message[USER][ACCOUNT_NAME]] = client
            #     client_ip, client_port = client.getpeername()
            #     # регистрация пользователя в БД
            #     self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
            #     send_message(client, RESPONSE_200)
            #     with conflag_lock:
            #         new_connection = True
            # else:
            #     response = RESPONSE_400
            #     response[ERROR] = 'Имя пользователя уже занято'
            #     send_message(client, response)
            #     self.clients.remove(client)
            #     client.close()
            # return

        # если это сообщение, то отправляем получателю
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message \
                and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                # self.messages.append(message)
                self.database.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        # если клиент выходит
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)
            # self.database.user_logout(message[ACCOUNT_NAME])
            # logger.info(f'Клиент {message[ACCOUNT_NAME]} вежливо отключился')
            # self.clients.remove(self.names[message[ACCOUNT_NAME]])
            # self.names[message[ACCOUNT_NAME]].close()
            # del self.names[message[ACCOUNT_NAME]]
            # with conflag_lock:
            #     new_connection = True
            # return

        # если это запрос списка контактов клиента
        elif ACTION in message \
                and message[ACTION] == GET_CONTACTS \
                and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # если это добавление контакта
        elif ACTION in message \
                and message[ACTION] == ADD_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # если это удаление контакта
        elif ACTION in message \
                and message[ACTION] == REMOVE_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        # если это запрос от известных пользователей
        elif ACTION in message \
                and message[ACTION] == USERS_REQUEST \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # если жто запрос публичного ключа пользователя
        elif ACTION in message \
                and message[ACTION] == PUBLIC_KEY_REQUEST \
                and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])
            # может быть, что ключа ещё нет (пользователь никогда не логинился, тогда шлём 400)
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        # иначе Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        """ Метод реализации авторизации пользователей """
        logger.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято'
            try:
                logger.debug(f'Username busy, sending {response}')
                send_message(sock, reversed)
            except OSError:
                logger.error('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()

        # Проверяем что пользователь зарегистрирован на сервере
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован'
            try:
                logger.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()

        else:
            logger.debug('Correct username, starting passwd check')
            # Иначе отвечаем 511 и проводим процедуру авторизации
            # Словарь - заготовка
            message_auth = RESPONSE_511
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth[DATA] = random_str.decode('ascii')
            message_auth[DATA] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем серверную версию ключа
            hash = hmac.new(self.database.get_hach(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            logger.debug(f'Auth message = {message_auth}')
            try:
                # обмен с клиентом
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as e:
                logger.error('Error in auth, data:', exc_info=e)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            # Если ответ клиента корректный, то сохраняем его в список пользователей
            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                # добавляем пользователя в список активных и,
                # если у него изменился открытый ключ, то сохраняем новый
                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY]
                )
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        """ Метод реализации отправки сервисного общения 205 клиентам """
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
