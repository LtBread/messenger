from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer

from server_dist.server.server.stat_window import StatWindow
from server_dist.server.server.config_window import ConfigWindow
from server_dist.server.server.add_user import RegisterUserDialog
from server_dist.server.server.del_user import DelUserDialog


class MainWindow(QMainWindow):
    """ Класс основного окна """
    def __init__(self, database, server, config):
        super().__init__()
        self.database = database
        self.server_thread = server
        self.config = config

        # кнопка выхода
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('CTR+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # кнопки
        self.refresh_btn = QAction('Обновить список клиентов', self)
        self.show_history_btn = QAction('История клиентов', self)
        self.config_btn = QAction('Настройки сервера', self)
        self.register_btn = QAction('Регистрация', self)
        self.remove_btn = QAction('Удаление пользователя', self)

        # статусбар
        self.statusBar()
        self.statusBar().showMessage('Server Working')

        # тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_btn)
        self.toolbar.addAction(self.show_history_btn)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)

        # настройки геометрии основного окна
        self.setFixedSize(1200, 600)
        self.setWindowTitle('Messeger alpaca release')

        # надпись списка элементов
        self.label = QLabel('Список подключенных клиентов: ', self)
        self.label.setFixedSize(400, 20)
        self.label.move(10, 35)

        # окно со списком подключенных клиентов
        self.active_clients_table = QTableView(self)
        self.active_clients_table.setFixedSize(1180, 400)
        self.active_clients_table.move(10, 65)

        # таймер, обновляющий список раз в указанное время
        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        # связывание
        self.refresh_btn.triggered.connect(self.create_users_model)
        self.show_history_btn.triggered.connect(self.show_statistics)
        self.config_btn.triggered.connect(self.server_config)
        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.rem_user)

        # отображение окна
        self.show()

    def create_users_model(self):
        """ Метод заполнения таблицы активных пользователей """
        list_users = self.database.active_users_list()
        list_table = QStandardItemModel()
        list_table.setHorizontalHeaderLabels(['Имя клиента', 'IP адрес', 'Порт', 'Время подключения'])
        for row in list_users:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(port)
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))  # округление до секунд
            time.setEditable(False)
            list_table.appendRow([user, ip, port, time])
        self.active_clients_table.setModel(list_table)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        """ Метод создания окна со статистикой клиентов """
        global stat_window
        stat_window = StatWindow(self.database)
        stat_window.show()

    def server_config(self):
        """ Метод создания окна с настройками сервера """
        global config_window
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        """ Метод создания окна регистрации пользователя """
        global reg_window
        reg_window = RegisterUserDialog(self.database, self.server_thread)
        reg_window.show()

    def rem_user(self):
        """ Метод создания окна удаления пользователя """
        global rem_window
        rem_window = DelUserDialog(self.database, self.server_thread)
        rem_window.show()
