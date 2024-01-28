import re
import logging
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from constants import (
    BASE_DIR,
    MAIN_DOC_URL,
    PYTHON_PEPS_URL,
    EXPECTED_STATUS,
    DOWNLOAD_DIR_PATH,
)
from configs import configure_argument_parser, configure_logging
from exceptions import ParserFindTagException, DataDoesNotExists, EmptyResponse
from outputs import control_output
from utils import find_tag, get_response_and_soup


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_response_and_soup(session, whats_new_url)
    div_with_ul = find_tag(soup, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        try:
            soup = get_response_and_soup(session, version_link)
        except EmptyResponse:
            continue
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    soup = get_response_and_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise DataDoesNotExists('Не найден список c версиями Python')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_response_and_soup(session, downloads_url)
    pdf_a4_tag = find_tag(
        soup, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / DOWNLOAD_DIR_PATH
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    peps_url = PYTHON_PEPS_URL
    soup = get_response_and_soup(session, peps_url)
    # Получаем часть страницы в тэге <section>
    section_tag = find_tag(soup, 'section', attrs={'id': 'index-by-category'})
    # Получаем все таблицы в тэге <tbody>
    tbody_tag = section_tag.find_all('tbody')
    results = [('Status', 'Count')]
    status_counter = defaultdict(int)
    for col in tqdm(tbody_tag):
        abbr_tag = col.find_all('abbr')
        a_tag = [
            data
            for data in col.find_all(
                'a', attrs={'class': 'pep reference internal'}
            )
            if data.text.isdigit()
        ]
        for status_col, ref_col in zip(abbr_tag, a_tag):
            # Статус pep в общей таблице
            status_on_table = status_col.text[1:]
            # Парсим страницу каждого pep
            current_pep_url = urljoin(PYTHON_PEPS_URL, ref_col['href'])
            try:
                soup = get_response_and_soup(session, current_pep_url)
            except EmptyResponse:
                continue
            status_in_page = find_tag(
                soup, 'abbr', attrs={'title': re.compile(r'\w+')}
            ).text
            # Формирование данных для выгрузки в файл и логирование
            if status_in_page not in EXPECTED_STATUS.get(status_on_table):
                logging.info(
                    f"""
                    Несовпадающие статусы:
                    {current_pep_url}
                    Статус в карточке: {status_in_page}
                    Ожидаемые статусы: {EXPECTED_STATUS.get(status_on_table)}
                    """
                )
            status_counter[status_in_page] += 1
    total_pep = 0
    for iteration in status_counter.items():
        results.append(iteration)
        total_pep += iteration[1]
    results.append(('Total', total_pep))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    try:
        results = MODE_TO_FUNCTION[parser_mode](session)
    except (EmptyResponse, DataDoesNotExists, ParserFindTagException) as error:
        logging.error(f'{error.__class__.__name__} : {error.args}')
        return
    else:
        if results is not None and len(results) > 1:
            control_output(results, args)
    finally:
        logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
