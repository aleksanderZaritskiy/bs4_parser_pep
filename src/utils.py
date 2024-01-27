from requests import RequestException

from exceptions import ParserFindTagException


# Перехват ошибки RequestException.
def get_response(session, url, encoding_type='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding_type
    except RequestException:
        raise RequestException(f'Возникла ошибка при загрузке страницы {url}')
    else:
        return response


# Перехват ошибки поиска тегов.
def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(f'Не найден тег {tag} {attrs}')
    return searched_tag
