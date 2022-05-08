from PyQt5 import QtCore, QtWidgets


class Ui_MainClientWindow(object):
    """ Класс-конфигуратор основного окна клиента """
    def setupUi(self, MainClientWindow):
        MainClientWindow.setObjectName('MainClientWindow')
        MainClientWindow.resize(800, 1000)
        MainClientWindow.setMinimumSize(QtCore.QSize(800, 1000))

        # centralwidget
        self.centralwidget = QtWidgets.QWidget(MainClientWindow)
        self.centralwidget.setObjectName('centralwidget')

        self.label_contacts = QtWidgets.QLabel(self.centralwidget)
        self.label_contacts.setGeometry(QtCore.QRect(10, 10, 170, 20))
        self.label_contacts.setObjectName('label_contacts')

        self.btn_add_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_contact.setGeometry(QtCore.QRect(10, 500, 180, 40))
        self.btn_add_contact.setObjectName('btn_add_contact')

        self.btn_remove_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_remove_contact.setGeometry(QtCore.QRect(10, 560, 180, 40))
        self.btn_remove_contact.setObjectName('btn_remove_contact')

        self.label_history = QtWidgets.QLabel(self.centralwidget)
        self.label_history.setGeometry(QtCore.QRect(280, 10, 391, 20))
        self.label_history.setObjectName('label_history')

        self.label_new_message = QtWidgets.QLabel(self.centralwidget)
        self.label_new_message.setGeometry(QtCore.QRect(280, 600, 450, 50))
        self.label_new_message.setObjectName('label_new_message')

        self.text_message = QtWidgets.QTextEdit(self.centralwidget)
        self.text_message.setGeometry(QtCore.QRect(280, 670, 500, 100))
        self.text_message.setObjectName('text_message')

        self.list_contacts = QtWidgets.QListView(self.centralwidget)
        self.list_contacts.setGeometry(QtCore.QRect(10, 40, 250, 400))
        self.list_contacts.setObjectName('list_contacts')

        self.list_messages = QtWidgets.QListView(self.centralwidget)
        self.list_messages.setGeometry(QtCore.QRect(280, 40, 500, 540))
        self.list_messages.setObjectName('list_messages')

        self.btn_clear = QtWidgets.QPushButton(self.centralwidget)
        self.btn_clear.setGeometry(QtCore.QRect(280, 800, 180, 40))
        self.btn_clear.setObjectName('btn_clear')

        self.btn_send = QtWidgets.QPushButton(self.centralwidget)
        self.btn_send.setGeometry(QtCore.QRect(280, 860, 220, 60))
        self.btn_send.setObjectName('btn_send')

        MainClientWindow.setCentralWidget(self.centralwidget)

        # menubar
        self.menubar = QtWidgets.QMenuBar(MainClientWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 756, 21))
        self.menubar.setObjectName('menubar')

        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName('menu')

        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName('menu_2')

        MainClientWindow.setMenuBar(self.menubar)

        # statusbar
        self.statusbar = QtWidgets.QStatusBar(MainClientWindow)
        self.statusbar.setObjectName('statusbar')
        MainClientWindow.setStatusBar(self.statusbar)

        #
        self.menu_exit = QtWidgets.QAction(MainClientWindow)
        self.menu_exit.setObjectName('menu_exit')

        self.menu_add_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_add_contact.setObjectName('menu_add_contact')

        self.menu_del_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_del_contact.setObjectName('menu_del_contact')

        self.menu.addAction(self.menu_exit)
        self.menu_2.addAction(self.menu_add_contact)
        self.menu_2.addAction(self.menu_del_contact)
        self.menu_2.addSeparator()
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslateUI(MainClientWindow)
        self.btn_clear.clicked.connect(self.text_message.clear)
        QtCore.QMetaObject.connectSlotsByName(MainClientWindow)

    def retranslateUI(self, MainClientWindow):
        _translate = QtCore.QCoreApplication.translate
        MainClientWindow.setWindowTitle(_translate('MainClientWindow', 'Чат alpaca release'))
        self.label_contacts.setText(_translate('MainClientWindow', 'Список контактов: '))
        self.btn_add_contact.setText(_translate('MainClientWindow', 'Добавить контакт'))
        self.btn_remove_contact.setText(_translate('MainClientWindow', 'Удалить контакт'))
        self.label_history.setText(_translate('MainClientWindow', 'История сообщений: '))
        self.label_new_message.setText(_translate('MainClientWindow', 'Введите новое сообщение: '))
        self.btn_send.setText(_translate('MainClientWindow', 'Отправить сообщение'))
        self.btn_clear.setText(_translate('MainClientWindow', 'Очистить поле'))
        self.menu.setTitle(_translate('MainClientWindow', 'Файл'))
        self.menu_2.setTitle(_translate('MainClientWindow', 'Контакты'))
        self.menu_exit.setText(_translate('MainClientWindow', 'Выход'))
        self.menu_add_contact.setText(_translate('MainClientWindow', 'Добавить контакт'))
        self.menu_del_contact.setText(_translate('MainClientWindow', 'Удалить контакт'))
