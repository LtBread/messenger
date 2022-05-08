from PyQt5.QtWidgets import QDialog, QPushButton, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class StatWindow(QDialog):
    """ Класс со статистикой пользователей """

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.initUI()

    def initUI(self):
        """ Настройки окна """
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(900, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # кнопка закрытия окна
        self.close_btn = QPushButton('Закрыть', self)
        self.close_btn.move(250, 650)
        self.close_btn.clicked.connect(self.close)

        # собственно история
        self.stat_table = QTableView(self)
        self.stat_table.setFixedSize(880, 520)
        self.stat_table.move(10, 10)

        self.create_stat_model()

    def create_stat_model(self):
        """ Метод заполнения таблицы """
        # список записей из БД
        stat_list = self.database.message_history()

        # объект модели данных
        data_list = QStandardItemModel()
        data_list.setHorizontalHeaderLabels(
            ['Имя клиента', 'Последний вход', 'Сообщений отправлено', 'Сообщений получено']
        )

        for row in stat_list:
            user, last_seen, sent, recvd = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            recvd = QStandardItem(str(recvd))
            recvd.setEditable(False)
            data_list.appendRow([user, last_seen, sent, recvd])
        self.stat_table.setModel(data_list)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()
