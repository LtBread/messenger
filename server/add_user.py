from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, QMessageBox
from PyQt5.QtCore import Qt
import hashlib
import binascii


class RegisterUserDialog(QDialog):
    """ Класс диалогового окна регистрации пользователя на сервере """
    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setWindowTitle('Регистрация')
        self.setFixedSize(400, 400)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label_username = QLabel('Введите имя пользователя: ', self)
        self.label_username.setFixedSize(250, 20)
        self.label_username.move(10, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(250, 40)
        self.client_name.move(10, 50)

        self.label_passwd = QLabel('Введите пароль: ', self)
        self.label_passwd.setFixedSize(250, 20)
        self.label_passwd.move(10, 110)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(250, 40)
        self.client_passwd.move(10, 150)

        self.label_conf = QLabel('Подтвердите пароль: ', self)
        self.label_conf.setFixedSize(250, 20)
        self.label_conf.move(10, 210)

        self.client_conf = QLineEdit(self)
        self.client_conf.setFixedSize(250, 40)
        self.client_conf.move(10, 260)

        self.btn_ok = QPushButton('Сохранить', self)
        self.btn_ok.setFixedSize(110, 40)
        self.btn_ok.move(10, 320)
        self.btn_ok.clicked.connect(self.save_data)

        self.btn_cancel = QPushButton('Отменить', self)
        self.btn_cancel.setFixedSize(110, 40)
        self.btn_cancel.move(150, 320)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        """ Метод проверки правильности ввода и сохранения в БД нового пользователя """
        if not self.client_name.text():
            self.messages.critical(self, 'Ошибка', 'Не указано имя пользователя')
            return
        elif self.client_passwd.text() != self.client_conf.text():
            self.messages.critical(self,  'Ошибка', 'Введённые пароли не совпадают')
            return
        elif self.database.check_user(self.client_name.text()):
            self.messages.critical(self, 'Ошибка', 'Пользователь уже существует')
            return
        else:
            # Генерируем хэш пароля, в качестве соли будем использовать логин в нижнем регистре
            passwd_bytes = self.client_passwd.text().encode('utf-8')
            salt = self.client_name.text().lower().encode('utf-8')
            passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
            self.database.add_user(self.client_name.text(), binascii.hexlify(passwd_hash))
            self.messages.information(self, 'Успех', 'Пользователь зарегистрирован')
            # Рассылаем клиентам сообщение о необходимости обновить справочники
            self.server.service_update_lists()
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    from server_database import ServerDB
    database = ServerDB('../server_database.db3')
    import os
    import sys
    path = os.path.join(os.getcwd(), '..')
    sys.path.insert(0, path)
    from core import MessageProcessor
    server = MessageProcessor('127.0.0.1', 7777, database)
    dial = RegisterUserDialog(database, server)
    app.exec_()
