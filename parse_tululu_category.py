import requests
import json
import logging
import time
import argparse
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse
from parse_tululu import parse_book_page
from parse_tululu import saves_txt
from parse_tululu import saves_image
from parse_tululu import saves_comments
from parse_tululu import saves_genres
from parse_tululu import check_for_redirect
from environs import Env

env = Env()
env.read_env()

PAGE_URL = 'https://tululu.org/l55/'
response = requests.get(PAGE_URL)
html_content = BeautifulSoup(response.text, 'lxml')
last_page = int(html_content.select('.npage')[-1].text)

parser = argparse.ArgumentParser(
    description="Парсинг онлайн-библиотеки https://tululu.org/. "
                "Скрипт обрабатывает заданные пользователем страницы с книгами"
                "Скачивает всю имеющуюся на этих страницах литературу"
                "и сохраняет локально запрошенную пользователем информацию о кажжой книге:"
                "название, автора, обложку, жанр, текст книги и т.д.")
parser.add_argument("--start_page", type=int, required=False, default=1,
                    help="Целочисленный аргумент (начальная страница)")
parser.add_argument("--end_page", type=int, required=False, default=last_page,
                    help="Целочисленный аргумент (конечная страница)")

args = parser.parse_args()

paths = {
    "books_path": env.str("BOOKS"),
    "images_path": env.str("IMAGES"),
    "comments_path": env.str("COMMENTS"),
}

for path in paths:
    Path(paths[path]).mkdir(parents=True, exist_ok=True)
books_all_pages = []

for page in range(args.start_page, args.end_page + 1):
    try:
        response = requests.get(f'{PAGE_URL}{page}')
    except requests.exceptions.HTTPError:
        logging.error(f'{page}-ой страницы не существует')
    except requests.exceptions.ConnectionError:
        logging.error(f'Не установлено соединение с сервером')
        time.sleep(10)
    else:
        soup = BeautifulSoup(response.text, 'lxml')
        books = soup.select('.d_book')
        for book in books:
            book_url = urljoin(
                'https://tululu.org',
                book.select_one('a')['href']
            )
            book_id = urlparse(book_url).path[2:-1]
            book_download_link = f'https://tululu.org/txt.php'
            try:
                book_response = requests.get(book_url, allow_redirects=False)
                book_txt_response = requests.get(book_download_link, allow_redirects=False, params={"id": book_id})

                check_for_redirect(book_txt_response.is_redirect)
                check_for_redirect(book_response.is_redirect)

                html_content_book = book_response.text

                parse_book = parse_book_page(html_content_book, book_url)
                saves_image(
                    parse_book["cover"],
                    paths["images_path"]
                )

            except requests.exceptions.HTTPError:
                logging.error(f'Книги по {book_id}-ому id не существует')
            except requests.exceptions.ConnectionError:
                logging.error(f'Не установлено соединение с сервером')
                time.sleep(10)
            else:
                saves_txt(
                    book_txt_response.content,
                    book_id,
                    parse_book['header'],
                    paths['books_path']
                )

                book_comments_path = saves_comments(
                    book_id,
                    parse_book["header"],
                    parse_book["comments"],
                    paths["comments_path"]
                )

                book_genres_path = saves_genres(
                    parse_book['genres'],
                    parse_book['header']
                )

                books_all_pages.append(
                    {
                        'title': parse_book["header"],
                        'author': parse_book['author'],
                        'img_src': parse_book['cover'],
                        'book_path': str(Path(paths['books_path']).joinpath(parse_book['header'])),
                        'comments': book_comments_path,
                        'genres': book_genres_path
                    }
                )

with open('books.json', 'w', encoding='utf8') as json_file:
    json.dump(books_all_pages, json_file, ensure_ascii=False, indent=4)
