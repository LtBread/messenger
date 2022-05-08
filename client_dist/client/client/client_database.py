import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker


class ClientDB:
    """ Класс - оболочка для работы с базой данных клиента
        Использует SQLite базу данных, реализован с помощью
        SQLAlchemy ORM и используется классический подход
        """
    class KnowUsers:
        """ Класс - отображение известных пользователей """
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageStat:
        """ Класс - отображение статистики сообщений """
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.now()

    class Contacts:
        """ Класс - отображение списка контактов """
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        """ Создаём движок базы данных, поскольку разрешено несколько клиентов одновременно,
        каждый должен иметь свою БД.
        Поскольку клиент мультипоточный, то необходимо отключить проверки на подключения с разных потоков,
        иначе sqlite3.ProgrammingError
        """
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'

        self.database_engine = create_engine(f'sqlite:///{os.path.join(path, filename)}',
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
                              Column('contact', String),
                              Column('direction', String),
                              Column('message', Text),
                              Column('date', DateTime)
                              )

        contacts_table = Table('Contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('name', String, unique=True)
                               )

        self.metadata.create_all(self.database_engine)

        mapper(self.KnowUsers, users_table)
        mapper(self.MessageStat, history_table)
        mapper(self.Contacts, contacts_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()

        # Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """ Добавление контакта """
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def contacts_clear(self):
        """ Очищение списка контактов """
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def del_contact(self, contact):
        """ Удаление контакта """
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    def add_users(self, users_list):
        """ Добавление известных пользователей """
        self.session.query(self.KnowUsers).delete()
        for user in users_list:
            user_row = self.KnowUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, contact, direction, message):
        """ Сохранение сообщений """
        message_row = self.MessageStat(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        """ Возвращает список контактов """
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        """ Возвращает список известных пользователей """
        return [user[0] for user in self.session.query(self.KnowUsers.username).all()]

    def check_contact(self, contact):
        """ Проверяет наличие пользователя в таблице контактов """
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        return False

    def check_user(self, user):
        """ Проверяет наличие пользователя в таблице известных пользователей """
        if self.session.query(self.KnowUsers).filter_by(username=user).count():
            return True
        return False

    def get_history(self, contact):
        """ Возвращает историю переписки """
        query = self.session.query(self.MessageStat).filter_by(contact=contact)
        return [(history_row.contact, history_row.direction, history_row.message, history_row.date)
                for history_row in query.all()]
