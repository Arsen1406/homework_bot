class NotForSendingError(Exception):
    """Не отправляем сообщение в телеграм."""
    pass


class ForSendingError(Exception):
    """Отправляем сообщение в телеграм."""
    pass


class StatusHomeworkNameIsNone(Exception):
    """Исключение при ошибке ключей в ответе."""


class EcxeptSendMessage(Exception):
    """Исключение при ошибке отправки сообщения."""


class TelegramError(NotForSendingError):
    """Вылетает когда не получилось выслать в телегу. НЕ ШЛЁМ в телегу."""
    pass


class EmptyAPIResponseError(NotForSendingError):
    """Вылетает когда нет домашек или timestamp. НЕ ШЛЁМ в телегу."""
    pass


class WrongAPIResponseCodeError(ForSendingError):
    """Вылетает когда код ответа сервера != 200. Шлём в телегу."""
    pass
