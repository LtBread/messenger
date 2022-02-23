import os
import sys
import json
import unittest

# sys.path.append((os.path.join(os.getcwd(), '..')))
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, ENCODING
from common.utils import get_message, send_message


class TestSocket:
    """
    Тестовый класс для тестирования отправки и получения,
    при создании требует словарь, который будет прогоняться
    через тестовую функцию
    """

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encode_message = None
        self.received_message = None

    def send(self, message_to_send):
        """
        Тестовая функция для отправки, кодирует сообщение,
        сохраняет то, что должно быть отправлено в сокет.
        message_to_send отправляется в сокет
        :param message_to_send
        :return
        """
        json_test_message = json.dumps(self.test_dict)
        # кодирует сообщение
        self.encode_message = json_test_message.encode(ENCODING)
        # сохраняет то, что должно быть отправлено в сокет
        self.received_message = message_to_send

    def recv(self, max_len):
        """
        Получение данных из сокета
        :param max_len:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 111111.111111,
        USER: {
            ACCOUNT_NAME: 'test_account_name'
        }
    }

    test_dict_recv_ok = {RESPONSE: 200}
    test_dict_recv_err = {
        RESPONSE: 400,
        ERROR: 'Bad Request',
    }

    def test_send_message(self):
        """
        Тест функции отправки, создаётся тестовый сокет,
        производится проверка корректной отправки словаря
        """
        # экземпляр тестового словаря
        test_socket = TestSocket(self.test_dict_send)
        # вызов тестируемой функции, результат будет сохранён в тестовом сокете
        send_message(test_socket, self.test_dict_send)
        # проверка кодирования словаря
        self.assertEqual(test_socket.encode_message, test_socket.received_message)

    def test_wrong_dict(self):
        """Тест генерации исключения при отправке сообщения с кривым словарём"""
        test_socket = TestSocket(self.test_dict_send)
        send_message(test_socket, self.test_dict_send)
        self.assertRaises(TypeError, send_message, test_socket, 'wrong_dictionary')

    def test_get_message(self):
        """Тест функции приёма сообщения с нормальным словарём"""
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        self.assertEqual((get_message(test_sock_ok)), self.test_dict_recv_ok)

    def test_wrong_message(self):
        """Тест функции приёма сообщения с кривым словарём"""
        test_sock_err = TestSocket(self.test_dict_recv_err)
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)


if __name__ == '__main__':
    unittest.main()
