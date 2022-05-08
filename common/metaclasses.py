import dis


class ServerVerifier(type):
    """ Метакласс, проверяющий что в результирующем классе нет клиентских
    вызовов таких как: connect. Также проверяется, что серверный
    сокет является TCP и работает по IPv4 протоколу
    """
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
    """ Метакласс, проверяющий что в результирующем классе нет серверных
    вызовов таких как: accept, listen. Также проверяется, что сокет не
    создаётся внутри конструктора класса
    """
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
