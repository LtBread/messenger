import sys
import socket
import logging
import logs.config_server_log
import logs.config_client_log

sys.path.append('../')

if sys.argv[0].find('__init__.py') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(func_to_log):
    """Декоратор - фиксирует в лог цепочку вызова функций для скрипта, который эту цепочку построил"""

    def log_saver(*args, **kwargs):
        func = func_to_log(*args, **kwargs)
        logger.debug(f'Функция {func_to_log.__name__} с параметрами {args} , {kwargs}, '
                     # f'вызвана из функции {sys._getframe().f_back.f_code.co_name} '
                     f'вызвана из модуля {func_to_log.__module__}')
        return func

    return log_saver


def login_required(func):
    """ Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в списке авторизованных клиентов.
    За исключением передачи словаря-запроса на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    """

    def checker(*args, **kwargs):
        # проверяем, что первый аргумент - экземпляр MessageProcessor
        # импортить необходимо тут, иначе ошибка рекурсивного импорта.
        from server.core import MessageProcessor
        from common.variables import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
            # Теперь надо проверить, что передаваемые аргументы не presence сообщение
            # Если presence, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то вызываем исключение
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
