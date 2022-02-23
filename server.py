import sys
import json
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE
from common.utils import get_message, send_message


def process_client_message(message):
    """
    Формирует ответ клиенту в виде строки с "кодом ответа сервера"
    :param message:
    :return:
    """
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
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print("You didn't specify a port in the parameter field '-p'")
        sys.exit(1)
    except ValueError:
        print('Invalid port')
        sys.exit(1)

    # считывание адреса из командной строки

    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        print("You didn't specify a ip-address in the parameter field '-a'")
        sys.exit(1)

    # инициализация сокета

    transport = socket(AF_INET, SOCK_STREAM)
    transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   # это чтобы не ждать 3 минуты, пока освободиться порт
    transport.bind((listen_address, listen_port))

    # прослушивание порта

    transport.listen(MAX_CONNECTIONS)

    # обмен сообщениями с клиентом

    while True:
        client, client_address = transport.accept()
        try:
            message_from_client = get_message(client)
            print(message_from_client)
            response = process_client_message(message_from_client)
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Incorrect message from client')
            client.close()


if __name__ == '__main__':
    main()
