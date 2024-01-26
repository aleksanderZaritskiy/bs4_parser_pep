import re
import logging
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm
from bs4 import BeautifulSoup

from constants import BASE_DIR, MAIN_DOC_URL, PYTHON_PEPS_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Не найден список c версиями Python')
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
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_tag = find_tag(soup, 'div', attrs={'role': 'main'})
    table_tag = find_tag(main_tag, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    peps_url = PYTHON_PEPS_URL
    response = get_response(session, peps_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    # Получаем часть страницы в тэге <section>
    section_tag = find_tag(soup, 'section', attrs={'id': 'index-by-category'})
    # Получаем все таблицы в тэге <tbody>
    tbody_tag = section_tag.find_all('tbody')
    results = [('Статус', 'Колличество')]
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
            response = get_response(session, current_pep_url)
            soup = BeautifulSoup(response.text, 'lxml')
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
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
