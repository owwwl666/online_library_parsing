import logging
import time
import requests
import argparse
import json
from pathvalidate import sanitize_filename
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from environs import Env


def check_for_redirect(response):
    """Проверяет ответ http запроса."""
    if response:
        raise requests.exceptions.HTTPError


def parse_book_page(html_content, book_link):
    """Обрабатывает html-контент страницы с книгой.

    Возвращает словарь с основной информацией о книге.
    """
    soup = BeautifulSoup(html_content, "lxml")
    book_parse = soup.select_one('div[id="content"] h1').text.split('::')
    book_name, book_author = book_parse[0].strip(), book_parse[1].strip()
    book_image = urljoin(
        book_link,
        soup.select_one('.bookimage img')['src']
    )
    book_comments = soup.select('.texts')
    book_genres = soup.select_one('span.d_book').select('a')
    return {
        "header": book_name,
        "author": book_author,
        "cover": book_image,
        "comments": book_comments,
        "genres": book_genres
    }


def saves_txt(response, book_id, book_name, folder):
    """Задает путь сохранения текста книги."""
    name = sanitize_filename(book_name)
    book_path = Path(folder).joinpath(f'{book_id}.{name}.txt')
    with open(book_path, 'wb') as file:
        file.write(response)


def saves_image(book_image, folder):
    """Скачивает обложку книги."""
    image_download = requests.get(book_image)
    image_download.raise_for_status()
    image_name = book_image.split("/")[-1]
    book_image_path = Path(folder).joinpath(f'{image_name}')
    with open(book_image_path, 'wb') as file:
        file.write(image_download.content)


def get_comments(book_comments):
    """Получает отзывы и комментарии о книге."""
    comments = [book_comment.select_one('.black').text for book_comment in book_comments]
    return comments


def get_genres(book_genres):
    """Получает все жанры книги."""
    genres = [book_genre.text for book_genre in book_genres]
    return genres


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Парсинг онлайн-библиотеки https://tululu.org/. "
                    "Скрипт обрабатывает выбранные пользователям по id книги и "
                    "скачивает с сайта всю необходимую информацию о ней: "
                    "название, автора, обложку, жанр и т.д.")
    parser.add_argument("-start", "--start_id", type=int, required=False, default=1,
                        help="Целочисленный аргумент (начальный id книги)")
    parser.add_argument("-end", "--end_id", type=int, required=False, default=10,
                        help="Целочисленный аргумент (конечный id книги)")

    args = parser.parse_args()

    env = Env()
    env.read_env()

    paths = {
        "books_path": env.str("BOOKS"),
        "images_path": env.str("IMAGES"),
    }

    comments_genres = []

    for path in paths:
        Path(paths[path]).mkdir(parents=True, exist_ok=True)

    for book_id in range(args.start_id, args.end_id + 1):
        book_download_link = f'https://tululu.org/txt.php'
        book_link = f'https://tululu.org/b{book_id}/'
        try:
            response = requests.get(book_download_link, allow_redirects=False, params={"id": book_id})
            book_link__response = requests.get(book_link, allow_redirects=False)

            response.raise_for_status()
            book_link__response.raise_for_status()
            check_for_redirect(response=book_link__response.is_redirect)
            check_for_redirect(response=response.is_redirect)

            html_content = book_link__response.text
            book = parse_book_page(
                html_content=html_content,
                book_link=book_link
            )
            saves_image(
                book_image=book["cover"],
                folder=paths["images_path"]
            )

        except requests.exceptions.HTTPError:
            logging.error(f'Книги по {book_id}-ому id не существует')
        except requests.exceptions.ConnectionError:
            logging.error(f'Не установлено соединение с сервером')
            time.sleep(5)
        else:
            saves_txt(
                response=response.content,
                book_id=book_id,
                book_name=book["header"],
                folder=paths["books_path"]
            )
            comments_genres.append({
                'title': book["header"],
                'comments': get_comments(book_comments=book["comments"]),
                'genres': get_genres(book_genres=book["genres"])

            })

    json_path = Path.cwd().joinpath('book_comments_genres.json')
    with open(json_path, 'w', encoding='utf8') as json_file:
        json.dump(comments_genres, json_file, ensure_ascii=False, indent=4)
