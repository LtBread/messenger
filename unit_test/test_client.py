import os
import sys
import unittest

from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR
from client import create_presence, process_anc

sys.path.append((os.path.join(os.getcwd(), '..')))


class TestClient(unittest.TestCase):

    def test_def_presence(self):
        """Тест корректного запроса"""
        test = create_presence()
        test[TIME] = 1.1  # время необходимо приравнять принудительно, чтобы пройти тест

        self.assertEqual(test, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_200_ans(self):
        """Тест корректного разбора ответа 200"""
        self.assertEqual(process_anc({RESPONSE: 200}), '200 : OK')

    def test_400_ans(self):
        """Тест корректного разбора 400"""
        self.assertEqual(process_anc({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        """Тест исключения без поля RESPONSE"""
        self.assertRaises(ValueError, process_anc, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
