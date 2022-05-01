import sys
import json
import logging
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt

from client.main_window_conv import Ui_MainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from client.client_database import ClientDB
from client.client_transport import ClientTransport
from client.start_dialog import UserNamedDialog
from common.errors import ServerError

logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport):
        super().__init__()
        self.database = database
        self.transport = transport

        # загрузка конфигурации окна из дизайнера
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.menu_exit.triggered.connect(qApp.exit)  # кнопка "Выход"

        self.ui.btn_send.clicked.connect(self.send_message)  # кнопка "Отправить сообщение"

        # добавить контакт
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # дополнительные атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None  # текущий контакт
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # двойной клик по списку контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        """ Деактивация поля ввода """
        self.ui.label_new_message.setText('Для выбора получателя дважды кликните\n по нему в окне контактов')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # поле ввода и кнопка отправки неактивны до выбора получателя
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    def history_list_update(self):
        """ Заполнение истории сообщений """
        list_messages = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()

        # берем не более MESSAGES_NUMBER последних записей
        MESSAGES_NUMBER = 20
        length = len(list_messages)
        start_index = 0
        if length > MESSAGES_NUMBER:
            start_index = length - MESSAGES_NUMBER

        # Заполнение модели записями, так же стоит разделить входящие и исходящие
        # сообщения выравниванием и разным фоном.
        # Записи в обратном порядке, поэтому выбираем их с конца и не более 20
        for i in range(start_index, length):
            item = list_messages[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                mess.setTextAlignment(Qt.AlignRight)
                self.history_model.appendRow(mess)
            self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        """ Функция-обработчик двойного клика поп контакту """
        # выбранный пользователем контакт находится в выделенном элементе в QListView
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()  # вызов основной функции

    def set_active_user(self):
        """ Функция, устанавливающая активного собеседника """
        self.ui.label_new_message.setText(f'Введите сообщение для {self.current_chat}: ')
        self.ui.btn_send.setDisabled(False)
        self.ui.btn_clear.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        self.history_list_update()  # заполнение окна истории сообщений

    def clients_list_update(self):
        """ Функция, обновляющая список контактов """
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        """ Функция добавления контакта """
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """ Функция-обработчик добавления контакта,
        сообщает серверу, обновляет таблицу и список контактов
        """
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """ Функция добавления контакта в БД """
        try:
            self.transport.add_contact(new_contact)
        except ServerError as e:
            self.messages.critical(self, 'Ошибка сервера', e.text)
        except OSError as e:
            if e.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Контакт {new_contact} добавлен')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен')

    def delete_contact_window(self):
        """ Функция удаления контакта """
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """ Функция-обработчик удаления контакта,
        сообщает на сервер, обновляет таблицу контактов
        """
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as e:
            self.messages.critical(self, 'Ошибка сервера', e.text)
        except OSError as e:
            if e.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            logger.info(f'Контакт {selected} удалён')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён')
            item.close()
            # если удалён пользователь, деактивируем поле ввода
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def send_message(self):
        """ Функция отправки сообщения пользователю """
        # Текст в поле, проверяем что поле не пустое затем забирается сообщение и поле очищается
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            self.transport.send_message(self.current_chat, message_text)
        except ServerError as e:
            self.messages.critical(self, 'Ошибка', e.text)
        except OSError as e:
            if e.errno:
                self.messages.critical(self, 'Ошибка', 'потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'потеряно соединение с сервером')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            logger.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    @pyqtSlot(str)
    def message(self, sender):
        """ Слот приёма нового сообщения """
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # проверка пользователя на наличие в списке контактов
            if self.database.check_contact(sender):
                # если он есть, спрашиваем о желании открыть с ним чат и открываем при желании
                if self.messages.question(self, 'Новое сообщение',
                                          f'получено новое сообщение от {sender}, '
                                          f'открыть чат с ним?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                # если нет, спрашиваем хотим ли добавить юзера в контакты
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}\n '
                                          f'Данного пользователя нет в ваших контактах\n'
                                          f'Добавить его в контакты и открыть чат с ним?',
                                          QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """ Слот потери соединения
        Выдаёт сообщение об ошибке и завершает работу приложения
        """
        self.messages.warning(self, 'Сбой соединения', 'потеряно соединение с сервером')
        self.close()

    def make_connection(self, trans_obj):
        """ Функция уставонления связи """
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from client_database import ClientDB
    database = ClientDB('test1')
    from client_transport import ClientTransport
    transport = ClientTransport(7777, '127.0.0.1', database, 'test1')
    window = ClientMainWindow(database, transport)
    exit(app.exec_())
