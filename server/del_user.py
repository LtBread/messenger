from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class DelUserDialog(QDialog):
    """ Класс диалогового окна удаления пользователя на сервере """
    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setWindowTitle('Удаление пользователя')
        self.setFixedSize(400, 200)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выбирайте пользователя для удаления:', self)
        self.selector_label.setFixedSize(380, 40)
        self.selector_label.move(10, 10)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(280, 40)
        self.selector.move(10, 50)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(90, 40)
        self.btn_ok.move(300, 50)
        self.btn_ok.clicked.connect(self.del_user)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(90, 40)
        self.btn_cancel.move(300, 100)
        self.btn_cancel.clicked.connect(self.close)

        self.all_users_fill()

    def all_users_fill(self):
        """ Метод заполнения списка пользователей """
        self.selector.addItems([item[0] for item in self.database.users_list()])

    def del_user(self):
        """ Метод-обработчик удаления пользователя """
        self.database.remove_user(self.selector.currentText())
        if self.selector.currentText() in self.server.names:
            sock = self.server.names[self.selector.currentText()]
            del self.server.names[self.selector.currentText()]
            self.server.remove_client(sock)
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
    dial = DelUserDialog(database, server)
    dial.show()
    app.exec_()
