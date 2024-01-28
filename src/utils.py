from requests import RequestException
from bs4 import BeautifulSoup

from exceptions import ParserFindTagException, UrlException, EmptyResponse


# Отправляет запрос и формирует суп
def get_response_and_soup(session, url, features='lxml'):

    response = get_response(session, url)
    if response is None:
        raise EmptyResponse(f'Не удалось собрать данные с сайта {url}')

    soup = BeautifulSoup(response.text, features)
    return soup


# Перехват ошибки RequestException.
def get_response(session, url, encoding_type='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding_type
        return response
    except RequestException:
        raise UrlException(f'Возникла ошибка при загрузке страницы {url}')


# Перехват ошибки поиска тегов.
def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(f'Не найден тег {tag} {attrs}')
    return searched_tag
