import logging
import time
import requests
import argparse
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
    book_parse = soup.find(id="content").find("h1").text.split("::")
    book_name, book_author = book_parse[0].strip(), book_parse[1].strip()
    book_image = urljoin(
        book_link,
        soup.find(class_="bookimage").find("img")["src"]
    )
    book_comments = soup.find_all(class_="texts")
    book_genres = soup.find("span", class_="d_book").find_all("a")
    return {
        "header": book_name,
        "author": book_author,
        "cover": book_image,
        "comments": book_comments,
        "genres": book_genres
    }


def download_txt(response, book_id, book_name, folder):
    """Задает путь сохранения текста книги."""
    name = sanitize_filename(book_name)
    book_path = Path(folder).joinpath(f'{book_id}.{name}.txt')
    with open(book_path, 'wb') as file:
        file.write(response)


def download_image(book_image, folder):
    """Скачивает обложку книги."""
    image_download = requests.get(book_image)
    image_download.raise_for_status()
    image_name = book_image.split("/")[-1]
    book_image_path = Path(folder).joinpath(f'{image_name}')
    with open(book_image_path, 'wb') as file:
        file.write(image_download.content)


def download_comments(book_id, book_name, book_comments, folder):
    """Скачивает отзывы и комментарии о книге."""
    book_comments_path = Path(folder).joinpath(f'{book_id}.{book_name}.txt')
    comments = [book_comment.find(class_="black").text for book_comment in book_comments]

    with open(book_comments_path, 'w') as file:
        file.writelines(f'{comment}\n' for comment in comments)


def download_genres(book_genres, book_name):
    """Скачивает и сохраняет в файл genres.txt название и все жанры книги."""
    genres = [book_genre.text for book_genre in book_genres]
    with open('genres.txt', 'a') as file:
        file.writelines(f'{book_name}\n{genres}\n')


def main():
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
        "comments_path": env.str("COMMENTS"),
    }

    for path in paths:
        Path(paths[path]).mkdir(parents=True, exist_ok=True)

    for book_id in range(args.start_id, args.end_id + 1):
        book_download_link = f'https://tululu.org/txt.php'
        book_link = f'https://tululu.org/b{book_id}/'
        try:
            response = requests.get(book_download_link, params={"id": book_id})
            book_link__response = requests.get(book_link)

            response.raise_for_status()
            book_link__response.raise_for_status()
            check_for_redirect(response=response.history)

            html_content = book_link__response.text
            book = parse_book_page(
                html_content=html_content,
                book_link=book_link
            )
            download_image(
                book_image=book["cover"],
                folder=paths["images_path"]
            )

        except requests.exceptions.HTTPError:
            logging.error(f'Книги по {book_id}-ому id не существует')
        except requests.exceptions.ConnectionError:
            logging.error(f'Не установлено соединение с сервером')
            time.sleep(5)
        else:
            download_txt(
                response=response.content,
                book_id=book_id,
                book_name=book["header"],
                folder=paths["books_path"]
            )

            download_comments(
                book_id=book_id,
                book_name=book["header"],
                book_comments=book["comments"],
                folder=paths["comments_path"]
            )

            download_genres(
                book_name=book["header"],
                book_genres=book["genres"],
            )


if __name__ == '__main__':
    main()
