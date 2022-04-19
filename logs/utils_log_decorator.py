import sys
import logging
import logs.config_server_log
import logs.config_client_log

if sys.argv[0].find('client.py') == -1:
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
