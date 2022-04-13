import logging

logger = logging.getLogger('server')


class Port:
    """ Описывает поведение дескриптора для атрибута listen_port класса Server """

    def __set_name__(self, owner, port):
        self.port = port

    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(f'Попытка запуска сервера с недопустимым портом: {value}. Сервер завершается')
            exit(1)
        instance.__dict__[self.port] = value
