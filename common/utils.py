""" UTILS """

import json
from common.variables import MAX_PACKAGE_LENGTH, ENCODING


def get_message(client):
    """
    получает ответ в виде байтов и возвращает в виде словаря
    :param client:
    :return: response
    """
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


def send_message(sock, message):
    """
    отправляет сообщение в виде байтов
    :param sock:
    :param message:
    """
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
