import requests
import json
import logging
import time
import argparse
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
from parse_tululu import parse_book_page
from parse_tululu import saves_txt
from parse_tululu import saves_image
from parse_tululu import get_comments
from parse_tululu import get_genres
from parse_tululu import check_for_redirect

PAGE_URL = 'https://tululu.org/l55/'


def get_last_page_number(url):
    """Получает последний номер страницы."""
    response = requests.get(url)
    response.raise_for_status()
    html_content = BeautifulSoup(response.text, 'lxml')
    return int(html_content.select('.npage')[-1].text)


def save_information_books(path, filename, books):
    """Сохраняет информацию о книгах в json файл."""
    json_path = Path(path).joinpath(filename)
    with open(json_path, 'w', encoding='utf8') as json_file:
        json.dump(books, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    last_page = get_last_page_number(PAGE_URL)

    parser = argparse.ArgumentParser(
        description="Парсинг онлайн-библиотеки https://tululu.org/. "
                    "Скрипт обрабатывает заданные пользователем страницы с книгами"
                    "Скачивает всю имеющуюся на этих страницах литературу"
                    "и сохраняет локально запрошенную пользователем информацию о каждой книге:"
                    "название, автора, обложку, жанр, текст книги и т.д.")
    parser.add_argument("--start_page", type=int, required=False, default=1,
                        help="Целочисленный аргумент (начальная страница)")
    parser.add_argument("--end_page", type=int, required=False, default=last_page,
                        help="Целочисленный аргумент (конечная страница)")
    parser.add_argument("--dest_folder", required=False, type=str, default="",
                        help="Путь к каталогу с результатами парсинга:(по-умолчанию корень проекта)")
    parser.add_argument("--skip_imgs", help='Не скачивать обложки книги', action="store_true")
    parser.add_argument("--skip_txt", help='Не скачивать текст книги', action="store_true")

    args = parser.parse_args()

    paths = {
        "books_path": Path(args.dest_folder).joinpath('books_text'),
        "images_path": Path(args.dest_folder).joinpath('book_images'),
    }
    all_books = []

    for path in paths:
        Path(paths[path]).mkdir(parents=True, exist_ok=True)

    for page in range(args.start_page, args.end_page + 1):
        try:
            response = requests.get(f'{PAGE_URL}{page}', allow_redirects=False)
            response.raise_for_status()
            check_for_redirect(response.is_redirect)
        except requests.exceptions.HTTPError:
            logging.error(f'{page}-ой страницы не существует')
        except requests.exceptions.ConnectionError:
            logging.error(f'Не установлено соединение с сервером')
            time.sleep(10)
        else:
            soup = BeautifulSoup(response.text, 'lxml')
            books = soup.select('.d_book')
            for book in books:
                book_id = urlparse(book.select_one('a')['href']).path[2:-1]
                book_url = f'https://tululu.org/b{book_id}/'

                book_download_link = f'https://tululu.org/txt.php'
                try:
                    response = requests.get(book_url, allow_redirects=False)
                    response.raise_for_status()
                    check_for_redirect(response.is_redirect)

                    html_content_book = response.text

                    book_ = parse_book_page(
                        html_content_book,
                        book_url
                    )

                    if not args.skip_txt:
                        book_txt_response = requests.get(book_download_link, allow_redirects=False,
                                                         params={"id": book_id})
                        book_txt_response.raise_for_status()
                        check_for_redirect(book_txt_response.is_redirect)
                        book_text = saves_txt(
                            book_txt_response.content,
                            book_id,
                            book_['header'],
                            paths['books_path']
                        )

                    if not args.skip_imgs:
                        book_img = saves_image(
                            book_['cover'],
                            paths['images_path']
                        )

                    all_books.append(
                        {
                            'title': book_['header'],
                            'author': book_['author'],
                            'img_path': str(paths['images_path'].joinpath(book_img)),
                            'book_path': str(paths['books_path'].joinpath(book_text)),
                            'comments': get_comments(book_['comments']),
                            'genres': get_genres(book_['genres'])
                        }
                    )

                except requests.exceptions.HTTPError:
                    logging.error(f'Книги по {book_id}-ому id не существует')
                except requests.exceptions.ConnectionError:
                    logging.error(f'Не установлено соединение с сервером')
                    time.sleep(10)

    save_information_books(
        args.dest_folder,
        'books.json',
        all_books
    )
