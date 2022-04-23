import os
import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, \
    QDialog, QPushButton, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


def gui_create_model(database):
    """ GUI - создание таблицы QModel для отображения в окне программы """
    list_users = database.active_users_list()
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
    return list_table


def create_stat_model(database):
    """ GUI - реализует заполнение таблицы истории сообщений """
    hist_list = database.message_history()

    # объект модели данных:
    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(
        ['Имя клиента', 'Последний вход', 'Сообщений отправлено', 'Сообщений получено']
    )
    for row in hist_list:
        user, last_seen, sent, recvd = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(sent))
        sent.setEditable(False)
        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)
        list_table.appendRow([user, last_seen, sent, recvd])
    return list_table


class MainWindow(QMainWindow):
    """ Класс основного окна """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # кнопка выхода
        # exitAction = QAction('Выход', self)
        # exitAction.setShortcut('CTR+Q')
        # exitAction.triggered.connect(qApp.quit)
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('CTR+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # кнопки
        self.refresh_btn = QAction('Обновить список клиентов', self)
        self.show_history_btn = QAction('История клиентов', self)
        self.config_btn = QAction('Настройки сервера', self)

        # статусбар
        self.statusBar()

        # тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_btn)
        self.toolbar.addAction(self.show_history_btn)
        self.toolbar.addAction(self.config_btn)

        # настройки геометрии основного окна
        self.setFixedSize(800, 600)
        self.setWindowTitle('Messeger alpaca release')

        # надпись списка клментов
        self.label = QLabel('Список подключенных клиентов: ', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        # окно со списком подключенных клиентов
        self.active_clients_table = QTableView(self)
        self.active_clients_table.setFixedSize(780, 400)
        self.active_clients_table.move(10, 55)

        # отображение окна
        self.show()


class HistoryWindow(QDialog):
    """ Класс с историей пользователей """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # настройки окна
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(900, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # кнопка закрытия окна
        self.close_btn = QPushButton('Закрыть', self)
        self.close_btn.move(250, 650)
        self.close_btn.clicked.connect(self.close)

        # собственно история
        self.history_table = QTableView(self)
        self.history_table.setFixedSize(880, 520)
        self.history_table.move(10, 10)

        self.show()


class ConfigWindow(QDialog):
    """ Класс окна настроек сервера """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # настройки окна
        self.setFixedSize(800, 600)
        self.setWindowTitle('Настройки сервера')

        # надпись о файле БД
        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.setFixedSize(260, 20)
        self.db_path_label.move(10, 10)

        # путь до БД
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(260, 40)
        self.db_path.move(10, 40)
        self.db_path.setReadOnly(True)

        # кнопка выбора пути
        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(280, 40)

        # функция обработки октрытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.clear()
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # надпись с именем поля файла БД
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.setFixedSize(260, 20)
        self.db_file_label.move(10, 100)

        # поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.setFixedSize(300, 40)
        self.db_file.move(280, 100)

        # надпись с номером порта
        self.port_label = QLabel('Номер порта: ', self)
        self.port_label.setFixedSize(260, 20)
        self.port_label.move(10, 150)

        # поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.setFixedSize(300, 40)
        self.port.move(280, 150)

        # надпись с адресом
        self.ip_label = QLabel('IP-адрес: ', self)
        self.ip_label.setFixedSize(260, 20)
        self.ip_label.move(10, 200)

        # надпись с напоминанием о пустом поле
        self.ip_label_note = QLabel('(оставьте пустым, чтобы \nпринимать соединения с \nлюбых адресов)', self)
        self.ip_label_note.setFixedSize(260, 100)
        self.ip_label_note.move(10, 220)

        # поле для ввода адреса
        self.ip = QLineEdit(self)
        self.ip.setFixedSize(300, 40)
        self.ip.move(280, 200)

        # кнопка сохранения настроек
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(280, 300)

        # кнопка закрытия окна
        self.close_btn = QPushButton('Закрыть', self)
        self.close_btn.move(450, 300)
        self.close_btn.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':

    # app = QApplication(sys.argv)
    # main_window = MainWindow()
    # main_window.statusBar().showMessage('Test Statusbar Message')
    # test_list = QStandardItemModel(main_window)
    #
    # test_list.setHorizontalHeaderLabels(['Имя клиента',
    #                                      'IP адрес',
    #                                      'Порт',
    #                                      'Время подключения'])
    #
    # test_list.appendRow([QStandardItem('test1'),
    #                      QStandardItem('192.168.0.5'),
    #                      QStandardItem('23544'),
    #                      QStandardItem('14:55:00')])
    #
    # test_list.appendRow([QStandardItem('test2'),
    #                      QStandardItem('192.168.0.6'),
    #                      QStandardItem('23545'),
    #                      QStandardItem('14:56:00')])
    #
    # main_window.active_clients_table.setModel(test_list)
    # main_window.active_clients_table.resizeColumnsToContents()
    # app.exec_()

    app = QApplication(sys.argv)
    history_window = HistoryWindow()
    test_list = QStandardItemModel(history_window)

    test_list.setHorizontalHeaderLabels(['Имя клиента',
                                         'Последний вход',
                                         'Сообщений отправлено',
                                         'Сообщений получено'])

    test_list.appendRow([QStandardItem('test1'),
                         QStandardItem('San Apr 17 14:55:00 2022'),
                         QStandardItem('2'),
                         QStandardItem('3')])

    test_list.appendRow([QStandardItem('test2'),
                         QStandardItem('San Apr 17 14:56:00 2022'),
                         QStandardItem('1'),
                         QStandardItem('2')])

    history_window.history_table.setModel(test_list)
    history_window.history_table.resizeColumnsToContents()
    app.exec_()

    # app = QApplication(sys.argv)
    # config_window = ConfigWindow()
    # app.exec_()
