import sys
import json

from client_dist.client.common.variables import MAX_PACKAGE_LENGTH, ENCODING
from client_dist.client.common.decorators import log


@log
def get_message(client):
    """ Получает сообщение в виде байтов и возвращает словарь,
    если получено что-то другое, поднимает ошибку значения
    """
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    json_response = encoded_response.decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@log
def send_message(sock, message):
    """ Принимает словарь, кодирует и отправляет сообщение в виде байтов """
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
