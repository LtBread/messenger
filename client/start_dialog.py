from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp
from PyQt5.QtCore import QEvent


class UserNamedDialog(QDialog):
    """ Стартовое диалоговое окно с выбором имени пользователя """

    def __init__(self):
        super().__init__()

        self.ok_pressed = False
        self.setWindowTitle('Привет!')
        self.setFixedSize(400, 280)

        self.label = QLabel('Введите имя пользователя: ', self)
        self.label.setFixedSize(250, 20)
        self.label.move(10, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(270, 40)
        self.client_name.move(10, 50)

        self.label_passwd = QLabel('Введите пароль: ', self)
        self.label_passwd.setFixedSize(250, 20)
        self.label_passwd.move(10, 110)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(270, 40)
        self.client_passwd.move(10, 150)

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(10, 210)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(150, 210)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        """ Обработчик кнопки ОК, если поле ввода не пустое, ставим флаг и завершаем приложение """
        if self.client_name.text() and self.client_passwd.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNamedDialog()
    app.exec_()
