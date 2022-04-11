import dis
from pprint import pprint


class ServerVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        load_global = []
        load_method = []
        load_attr = []
        # pprint(clsdict)
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in load_global:
                            load_global.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in load_method:
                            load_method.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in load_attr:
                            load_attr.append(i.argval)

        print(20 * '-', 'load_global', 20 * '-')
        pprint(load_global)
        print(20 * '-', 'load_method', 20 * '-')
        pprint(load_method)
        print(20 * '-', 'load_attr', 20 * '-')
        pprint(load_attr)
        print(50 * '-')
        if 'connect' in load_global:
            raise TypeError('Использование метода connect недопустимо в классе Server')
        if not ('SOCK_STREAM' in load_global and 'AF_INET' in load_global):
            raise TypeError('некорректная инициализация сокета')
        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    def __init__(cls, clsname, bases, clsdict):

        load_global = []
        load_method = []
        load_attr = []
        # pprint(clsdict)

        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in load_global:
                            load_global.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in load_method:
                            load_method.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in load_attr:
                            load_attr.append(i.argval)

        print(20 * '-', 'load_global', 20 * '-')
        pprint(load_global)
        print(20 * '-', 'load_method', 20 * '-')
        pprint(load_method)
        print(20 * '-', 'load_attr', 20 * '-')
        pprint(load_attr)
        print(50 * '-')

        if 'accept' in load_global and 'listen' in load_global:
            raise TypeError(f'В классе {clsname} обнаружено использование запрещённого приёма')
        if not ('get_message' in load_global or 'send_message' in load_global):
            raise TypeError('Отсутствует вызов функции, работающей с сокетами')
        super().__init__(clsname, bases, clsdict)
