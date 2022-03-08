import sys
import logging

if sys.argv[0].find('client.py') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func_to_log):
    def log_saver(*args, **kwargs):
        func = func_to_log(*args, **kwargs)
        LOGGER.debug(f'Функция {func_to_log.__name__} '
                     f'вызвана из функции {sys._getframe().f_back.f_code.co_name} '
                     f'модуля {sys._getframe().f_back.f_code.co_filename}')
        return func

    return log_saver
