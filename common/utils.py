import sys
import json

from errors import IncorrectDataRecivedError, NonDictInputError
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from logs.utils_log_decorator import log

sys.path.append('../')


@log
def get_message(client):
    """
    Получает сообщение в виде байтов и возвращает словарь,
    если получено что-то другое, поднимает ошибку значения
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
    raise IncorrectDataRecivedError


@log
def send_message(sock, message):
    """
    Принимает словарь, кодирует и отправляет сообщение в виде байтов
    :param sock:
    :param message:
    """
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
