class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""

    pass


class UrlException(Exception):
    """Вызывается, когда не удалось установить связь с Url"""

    pass


class DataDoesNotExists(Exception):
    """Вызывается, когда не найден список c версиями Python"""

    pass


class EmptyResponse(Exception):
    """Вызывается, когда парсер вернул пустой ответ от сайта"""

    pass
