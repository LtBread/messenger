import dis
from pprint import pprint


class ServerVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        load_global = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in load_global:
                            load_global.append(i.argval)

        if 'connect' in load_global:
            raise TypeError('Использование метода connect недопустимо в классе Server')
        if not ('SOCK_STREAM' in load_global and 'AF_INET' in load_global):
            raise TypeError('некорректная инициализация сокета')
        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        load_global = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in load_global:
                            load_global.append(i.argval)

        if 'accept' in load_global and 'listen' in load_global:
            raise TypeError(f'В классе {clsname} обнаружено использование запрещённого приёма')
        if not ('get_message' in load_global or 'send_message' in load_global):
            raise TypeError('Отсутствует вызов функции, работающей с сокетами')
        super().__init__(clsname, bases, clsdict)
