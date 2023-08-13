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
from parse_tululu import get_comments
from parse_tululu import get_genres
from parse_tululu import check_for_redirect

PAGE_URL = 'https://tululu.org/l55/'

if __name__ == '__main__':
    response = requests.get(PAGE_URL)
    response.raise_for_status()
    html_content = BeautifulSoup(response.text, 'lxml')
    last_page = int(html_content.select('.npage')[-1].text)

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
    parser.add_argument("--dest_folder", required=False, type=str,
                        help="Путь к каталогу с результатами парсинга:(по-умолчанию корень проекта)")
    parser.add_argument("--skip_imgs", help='Скачивать ли обложки книг', action="store_true")
    parser.add_argument("--skip_txt", help='Скачивать ли тексты книг', action="store_true")

    args = parser.parse_args()

    paths = {
        "books_path": Path(args.dest_folder).joinpath('books_text') if args.dest_folder else Path.cwd().joinpath(
            'books_text'),
        "images_path": Path(args.dest_folder).joinpath('book_images') if args.dest_folder else Path.cwd().joinpath(
            'book_images'),
    }

    for path in paths:
        Path(paths[path]).mkdir(parents=True, exist_ok=True)

    all_books = []

    for page in range(args.start_page, args.end_page + 1):
        try:
            response = requests.get(f'{PAGE_URL}{page}')
            response.raise_for_status()
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
                    response = requests.get(book_url, allow_redirects=False)
                    book_txt_response = requests.get(book_download_link, allow_redirects=False, params={"id": book_id})

                    book_txt_response.raise_for_status()
                    check_for_redirect(book_txt_response.is_redirect)
                    check_for_redirect(response.is_redirect)

                    html_content_book = response.text

                    parse_book = parse_book_page(html_content_book, book_url)
                    if not args.skip_imgs:
                        saves_image(
                            parse_book["cover"],
                            paths['images_path']
                        )

                except requests.exceptions.HTTPError:
                    logging.error(f'Книги по {book_id}-ому id не существует')
                except requests.exceptions.ConnectionError:
                    logging.error(f'Не установлено соединение с сервером')
                    time.sleep(10)
                else:
                    if not args.skip_txt:
                        saves_txt(
                            book_txt_response.content,
                            book_id,
                            parse_book['header'],
                            paths['books_path']
                        )

                    book_comments_path = get_comments(
                        parse_book["comments"],
                    )

                    book_genres_path = get_genres(
                        parse_book['genres'],
                    )

                    all_books.append(
                        {
                            'title': parse_book["header"],
                            'author': parse_book['author'],
                            'img_src': parse_book['cover'],
                            'book_path': str(
                                Path(paths['books_path']).joinpath(
                                    parse_book['header'])) if not args.skip_txt else None,
                            'comments': book_comments_path,
                            'genres': book_genres_path
                        }
                    )

    json_path = Path(args.dest_folder).joinpath('books.json') if args.dest_folder else Path.cwd().joinpath(
        'books.json')
    with open(json_path, 'w', encoding='utf8') as json_file:
        json.dump(all_books, json_file, ensure_ascii=False, indent=4)
