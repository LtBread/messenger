import os
from PyQt5.QtWidgets import QLabel, QDialog, QPushButton, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt


class ConfigWindow(QDialog):
    """ Класс окна настроек сервера """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()

    def initUI(self):
        """ Настройки окна """
        self.setFixedSize(800, 600)
        self.setWindowTitle('Настройки сервера')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

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

        self.db_path_select.clicked.connect(self.open_file_dialog)

        self.show()

        self.db_path.insert(self.config['SETTINGS']['database_path'])
        self.db_file.insert(self.config['SETTINGS']['database_file'])
        self.port.insert(self.config['SETTINGS']['default_port'])
        self.ip.insert(self.config['SETTINGS']['listen_address'])
        self.save_btn.clicked.connect(self.save_server_config)

    def open_file_dialog(self):
        """ Обработчик открытия окна выбора папки """
        global dialog
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace('/', '\\')
        self.db_path.clear()
        self.db_path.insert(path)

    def save_server_config(self):
        """ Сохраняет настройки
        Проверяет правильность введённых данных и если всё правильно сохраняет ini файл
        """
        global config_window
        message = QMessageBox()
        self.config['SETTINGS']['database_path'] = self.db_path.text()
        self.config['SETTINGS']['database_file'] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, 'Ошибка', 'Порт должен быть числом')
        else:
            self.config['SETTINGS']['listen_address'] = self.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['default_port'] = str(port)
                print(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                dir_path = os.path.join(dir_path, '../../..')
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    self.config.write(conf)
                    message.information(self, 'OK', 'Настройки успешно сохранены')
            else:
                message.warning(self, 'Ошибка', 'Несуществующий порт')
