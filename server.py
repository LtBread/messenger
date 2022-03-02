import sys
import json
import logging
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import logs.server_log_config
from errors import IncorrectDataRecivedError
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE
from common.utils import get_message, send_message

# инициализация клиентского логера
SERVER_LOGGER = logging.getLogger('server')


def process_client_message(message):
    """
    Обрабатывает сообщения от клиентов, принимает словарь, проверяет,
    Формирует ответ клиенту в виде строки с "кодом ответа сервера"
    :param message:
    :return:
    """
    # SERVER_LOGGER.debug(f'Разбор сообщения от клиента: {message}')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONDEFAULT_IP_ADDRESSSE: 400,
        ERROR: 'Bad Request',
    }


def main():
    """
    Загружает параметры командной строки
    :return:
    """

    # считывание порта из командной строки
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if not 1023 < listen_port < 65536:
            raise ValueError(listen_port)
        SERVER_LOGGER.info(f'Сервер в работе, порт: {listen_port}')
    except IndexError:
        # print("You didn't specify a port in the parameter field '-p'")
        SERVER_LOGGER.error(f'После параметра "-p" не указан порт. Сервер завершается')
        sys.exit(1)
    except ValueError as e:
        SERVER_LOGGER.critical(f'Попытка запуска сервера с недопустимым портом: {e.args[0]}. Сервер завершается')
        sys.exit(1)

    # считывание адреса из командной строки
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
            SERVER_LOGGER.info(f'Сервер в работе, адрес: {listen_address}')
        else:
            listen_address = ''
            SERVER_LOGGER.info(f'Сервер в работе, слушает всех')
    except IndexError:
        # print("You didn't specify a ip-address in the parameter field '-a'")
        SERVER_LOGGER.error(f'После параметра "-a" не указан адрес. Сервер завершается')
        sys.exit(1)

    # инициализация сокета
    transport = socket(AF_INET, SOCK_STREAM)
    transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # это чтобы не ждать 3 минуты, пока освободиться порт
    transport.bind((listen_address, listen_port))

    # прослушивание порта
    transport.listen(MAX_CONNECTIONS)

    # обмен сообщениями с клиентом
    while True:
        client, client_address = transport.accept()
        SERVER_LOGGER.info(f'Установлено соединение с {client_address}')
        try:
            message_from_client = get_message(client)
            SERVER_LOGGER.debug(f'Получено сообщение {message_from_client}')
            # print(message_from_client)
            response = process_client_message(message_from_client)
            SERVER_LOGGER.info(f'Сформирован ответ клиенту {response}')
            send_message(client, response)
            SERVER_LOGGER.debug(f'Соединение с клиентом {client_address} закрывается')
            client.close()
        except json.JSONDecodeError:
            SERVER_LOGGER.error(f'Не удалось декодировать полученную строку JSON, полученную от'
                                f'{client_address}. Соединение закрывается')
        except IncorrectDataRecivedError:
            SERVER_LOGGER.error(f'От клиента {client_address} приняты некорректные данные. Соединение закрывается')


if __name__ == '__main__':
    main()
