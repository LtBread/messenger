from _datetime import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from pprint import pprint

from common.variables import *


class ClientDB:
    class KnowUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.now()

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        """ Создаём движок базы данных, поскольку разрешено несколько клиентов одновременно,
        каждый должен иметь свою БД.
        Поскольку клиент мультипоточный, то необходимо отключить проверки на подключения с разных потоков,
        иначе sqlite3.ProgrammingError
        """
        self.database_engine = create_engine(f'sqlite:///client_{name}.db3',
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users_table = Table('Know_users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('username', String)
                            )

        history_table = Table('Message_history', self.metadata,
                              Column('id', Integer, primary_key=True),
                              Column('from_user', String),
                              Column('to_user', String),
                              Column('message', Text),
                              Column('date', DateTime)
                              )

        contacts_table = Table('Contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('name', String, unique=True)
                               )

        self.metadata.create_all(self.database_engine)

        mapper(self.KnowUsers, users_table)
        mapper(self.MessageHistory, history_table)
        mapper(self.Contacts, contacts_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()

        # Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contacts(self, contact):
        """ Добавление контакта """
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        """ Удаление контакта """
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    def add_users(self, users_list):
        """ Функция добавления известных пользователей """
        self.session.query(self.KnowUsers).delete()
        for user in users_list:
            user_row = self.KnowUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        """ Функция сохранения сообщений """
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        """ Возвращает список контактов """
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        """ Возвращает список известных пользователей """
        return [user[0] for user in self.session.query(self.KnowUsers.username).all()]

    def check_contact(self, contact):
        """ Функция проверяет наличие пользователя в таблице контактов """
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        return False

    def check_user(self, user):
        """ Функция проверяет наличие пользователя в таблице известных пользователей """
        if self.session.query(self.KnowUsers).filter_by(username=user).count():
            return True
        return False

    def get_history(self, from_who=None, to_who=None):
        """ Функция возвращает историю переписки """
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]


if __name__ == '__main__':
    test_bd = ClientDB('test1')
    for item in ['test3', 'test3', 'test5']:
        test_bd.add_contacts(item)
    test_bd.add_contacts('test2')
    test_bd.add_users(['test2', 'test3', 'test4', 'test5', 'test10'])
    test_bd.save_message('test1', 'test2',
                         f'Проверка... Тестовое сообщение от {datetime.now().strftime("%m-%d-%Y, %H:%M")}')
    test_bd.save_message('test2', 'test1',
                         f'Проверка № 2... Тестовое сообщение от {datetime.now().strftime("%m-%d-%Y, %H:%M")}')

    print(test_bd.get_contacts())
    print(test_bd.get_users())
    print(test_bd.check_user('шпион'))
    print(test_bd.check_user('test2'))
    print('--------------------------------')
    pprint(test_bd.get_history('test1', 'test2'))
    pprint(test_bd.get_history('test2'))
    pprint(test_bd.get_history(to_who='test2'))
    pprint(test_bd.get_history('test3'))
    test_bd.del_contact('test3')
    print(test_bd.get_contacts())
