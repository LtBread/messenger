import sys
import json
import time
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT
from common.utils import get_message, send_message


def create_presence(account_name='Guest'):
    """
    формирует сообщение в виде словаря для отправки серверу и возвращает его
    :param account_name:
    :return:
    """
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return out


def process_anc(message):
    """
    получает ответ сервера и возвращает строку с результатом
    :param message:
    :return:
    """
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def main():
    """
    загружает параметры командной строки,
    создаёт сокет, отправляет сообщение серверу и получает ответ
    :return:
    """

    # считывание порта и адреса из командной строки

    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('Invalid port')
        sys.exit(1)

    # инициализация сокета и обмен

    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((server_address, server_port))
    message_to_server = create_presence()
    send_message(transport, message_to_server)
    try:
        answer = process_anc(get_message(transport))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('Failed to decode')


if __name__ == '__main__':
    main()
