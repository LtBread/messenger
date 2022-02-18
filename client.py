import time
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR
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


if __name__ == '__main__':
    pass

# CLIENT_SOCK = socket(AF_INET, SOCK_STREAM)
# CLIENT_SOCK.connect(('localhost', 8888))
# MESSAGE = CLIENT_SOCK.recv(1024)
# print(MESSAGE.decode('utf-8'))
# CLIENT_SOCK.close()
