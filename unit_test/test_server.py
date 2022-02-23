import os
import sys
import unittest

from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR
from server import process_client_message

sys.path.append((os.path.join(os.getcwd(), '..')))


class TestServer(unittest.TestCase):

    ok_dict = {RESPONSE: 200}
    err_dict = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_ok_check(self):
        """Корректный запрос"""
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.ok_dict)

    def test_no_action(self):
        """Ошибка - нет действия"""
        self.assertNotEqual(process_client_message(
            {TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    def test_wrong_action(self):
        """Ошибка - неизвестное действие"""
        self.assertNotEqual(process_client_message(
            {ACTION: 'Wrong', TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    def test_no_time(self):
        """Ошибка - нет поля времени"""
        self.assertNotEqual(process_client_message(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    def test_no_user(self):
        """Ошибка - нет пользователя"""
        self.assertNotEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1}), self.err_dict)

    def test_unknown_user(self):
        """Ошибка - неизвестный пользователь"""
        self.assertNotEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Spy'}}), self.err_dict)


if __name__ == '__main__':
    unittest.main()
