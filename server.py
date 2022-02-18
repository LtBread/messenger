import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE
from common.utils import get_message, send_message


def process_client_message(message):
    """
    формирует ответ клиенту в виде строки с "кодом ответа сервера"
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


if __name__ == '__main__':
    pass

# SERV_SOCK = socket(AF_INET, SOCK_STREAM)
# SERV_SOCK.bind(('', 8888))
# SERV_SOCK.listen(5)
# 
# try:
#     while True:
#         CLIENT_SOCK, ADDR = SERV_SOCK.accept()
#         print(f'Connect from')
#         CLIENT_SOCK.send('get low'.encode('utf-8'))
#         CLIENT_SOCK.close()
# finally:
#     SERV_SOCK.close()
