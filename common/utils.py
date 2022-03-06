import json

from errors import NonDictInputError
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from logs.utils_log_decorator import log


@log
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
        raise NonDictInputError
    raise ValueError


@log
def send_message(sock, message):
    """
    отправляет сообщение в виде байтов
    :param sock:
    :param message:
    """
    if not isinstance(message, dict):
        raise TypeError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
