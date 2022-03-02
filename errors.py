class IncorrectDataRecivedError(Exception):
    """Исключение - из сокета получены некорректные данные"""

    def __str__(self):
        return 'Принято некорректное сообщение с удалённого хоста'


class NonDictInputError(Exception):
    """Исключение - аргумент функции не является словарём"""

    def __str__(self):
        return 'Аргумент функции должен быть словарём'


class ReqFileMissingError(Exception):
    """Ошибка - отсутствует обязательное поле в приянтом словаре"""

    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.missing_field}'
