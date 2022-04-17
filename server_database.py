import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker

import server
from common.variables import *
from datetime import datetime
from pprint import pprint


class ServerDB:
    class AllUsers:
        def __init__(self, username):
            self.id = None
            self.username = username
            self.last_login = datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.id = None
            self.user_id = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time

    class LoginHistory:
        def __init__(self, user_id, ip_address, port, date_time):
            self.id = None
            self.user_id = user_id
            self.ip_address = ip_address
            self.port = port
            self.date_time = date_time

    class UsersContacts:
        def __init__(self, user_id, contact):
            self.id = None
            self.user_id = user_id
            self.contact = contact

    class UsersHistory:
        def __init__(self, user_id):
            self.id = None
            self.user_id = user_id
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        """ Движок базы данных SERVER_DATABASE - sqlite3:///server_database.db3
        echo = False - отключает вывод на экран sql-запросов
        poll_recycle - устанавливает время простоя БД в секундах

        """
        print(path)
        self.database_engine = sqlalchemy.create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                                        connect_args={'check_same_thread': False})
        self.metadata = sqlalchemy.MetaData()

        all_users_table = Table('Users', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('username', String, unique=True),
                                Column('last_login', DateTime)
                                )
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )
        login_history_table = Table('Login_history', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user_id', ForeignKey('Users.id')),
                                    Column('ip_address', String),
                                    Column('port', Integer),
                                    Column('date_time', DateTime)
                                    )

        users_contacts = Table('Users_contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('user_id', ForeignKey('Users.id')),
                               Column('contact', ForeignKey('Users.id'))
                               )

        users_history_table = Table('Users_history', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user_id', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        # создание таблиц
        self.metadata.create_all(self.database_engine)

        # создание отображений. Связывание классов в ORM с таблицами
        mapper(self.AllUsers, all_users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history_table)
        mapper(self.UsersContacts, users_contacts)
        mapper(self.UsersHistory, users_history_table)

        # создание сессии
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # перед установкой соединения необходимо очистить таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        """ Функция записи в базу факта входа пользователя """
        print(username, ip_address, port)

        # запрос в базу на наличие пользователя с таким именем
        rez = self.session.query(self.AllUsers).filter_by(username=username)

        # если есть совпадение, обновляется время входа
        if rez.count():
            user = rez.first()
            user.last_login = datetime.now()
        # иначе создаётся новый пользователь
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

        # добавление пользователя в ActiveUsers
        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.now())
        self.session.add(new_active_user)

        # добавление пользователя в LoginHistory
        history = self.LoginHistory(user.id, ip_address, port, datetime.now())
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        """ Функция записи в базу факта выхода пользователя """

        user = self.session.query(self.AllUsers).filter_by(username=username).first()  # запрос
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()  # удаление
        self.session.commit()

    def process_massage(self, sender, recipient):
        """ Функция фиксации передачи сообщения в БД """
        sender = self.session.query(self.AllUsers).filter_by(username=sender).first().id  # id отправителя
        recipient = self.session.query(self.AllUsers).filter_by(username=recipient).first().id  # id получателя

        sender_row = self.session.query(self.UsersHistory).filter_by(user_id=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user_id=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        """ Функция добавления контакта для пользователя """
        user = self.session.query(self.AllUsers).filter_by(username=user).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.UsersContacts).filter_by(user_id=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        """ Функция удаления контакта из БД """
        user = self.session.query(self.AllUsers).filter_by(username=user).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            return

        # удаление
        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user_id == user.id, self.UsersContacts.contact == contact.id
        ).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login
        )
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        """ Запрос истории входа пользователя """
        query = self.session.query(
            self.AllUsers.username,
            self.LoginHistory.ip_address,
            self.LoginHistory.port,
            self.LoginHistory.date_time
        ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.username == username)
        return query.all()

    def get_contacts(self, username):
        """ Функция, возвращающая список контактов пользователя """
        # Запрашиваем указанного пользователя
        user = self.session.query(self.AllUsers).filter_by(username=username).one()
        # Запрашиваем его список контактов
        query = (self.session.query(
            self.UsersContacts, self.AllUsers.username).filter_by(user_id=user.id).
                 join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)
                 )
        # Выбираем только имена пользователей и возвращаем их
        return [contact[1] for contact in query.all()]

    def message_history(self):
        """ Функция, возвращающая количество переданных и полученных сообщений """
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        return query.all()


# Отладка
if __name__ == '__main__':
    test_db = ServerDB('server_database.db3')
    test_db.user_login('client1', '192.168.1.4', 7777)
    test_db.user_login('client2', '192.168.1.5', 7778)

    print('---------список всех пользователей----------------')
    pprint(test_db.users_list())

    print('---------список активных пользователей------------')
    pprint(test_db.active_users_list())

    print('Клиент выходит...')
    test_db.user_logout('client1')

    print('---------список активных пользователей------------')
    pprint(test_db.active_users_list())

    print('-----------история входов пользователя-------------')
    pprint(test_db.login_history('client1'))

    print('---------------------------------------------------')
    test_db.add_contact('client2', 'client1')
    test_db.add_contact('client2', 'client3')
    test_db.add_contact('client2', 'abrakadabra')
    # test_db.add_contact('abrakadabra', 'client2')
    pprint(test_db.get_contacts('client2'))
    test_db.remove_contact('client2', 'client3')
    pprint(test_db.get_contacts('client2'))
    test_db.user_login('client1', '192.168.1.4', 7776)
    print('---------список активных пользователей------------')
    pprint(test_db.active_users_list())
    # test_db.process_massage('client1', 'client2')
    print(test_db.message_history())
