import pathlib
import requests
import argparse
from pathvalidate import sanitize_filename
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from environs import Env


def check_for_redirect(response):
    """Проверяет ответ http запроса."""
    if response != 200:
        raise requests.exceptions.HTTPError


def parse_book_page(book_link):
    """Обрабатывает html-контент страницы с книгой.

    Возвращает словарь с основной информацией о книге.
    """
    html_text = requests.get(book_link).text
    soup = BeautifulSoup(html_text, 'lxml')
    book = soup.find(id="content").find("h1").text.split('::')
    book_name, book_author = book[0].strip(), book[1].strip()
    book_image = urljoin(
        "https://tululu.org",
        soup.find(class_="bookimage").find("img")["src"]
    )
    book_comments = soup.find_all(class_="texts")
    book_genres = soup.find("span", class_="d_book").find_all("a")
    return {
        "Заголовок": book_name,
        "Автор": book_author,
        "Обложка": book_image,
        "Комментарии": book_comments,
        "Жанры": book_genres
    }


def download_txt(book_id, book_name, folder):
    """Скачивает текст книги."""
    name = sanitize_filename(book_name)
    book_path = Path(folder).joinpath(f"{book_id}.{name}.txt")
    return book_path


def download_image(book_image, folder):
    """Скачивает обложку книги."""
    image_download = requests.get(book_image)
    image_name = book_image.split('/')[-1]
    book_image_path = Path(folder).joinpath(f"{image_name}")
    with open(book_image_path, 'wb') as file:
        file.write(image_download.content)


def download_comment(book_id, book_name, book_comments, folder):
    """Скачивает отзывы и комментарии о книге."""
    book_comments_path = Path(folder).joinpath(f"{book_id}.{book_name}.txt")
    for book_comment in book_comments:
        with open(book_comments_path, 'a') as file:
            file.write(f'{book_comment.find(class_="black").text}\n')


def download_genre(book_name, book_genres):
    """Возвращает кортеж в виде заголовка и жанра книги."""
    genres = [book_genre.text for book_genre in book_genres]
    return (
        f'Заголовок: {book_name}',
        genres
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-start", "--start_id", type=int, required=False, default=1)
    parser.add_argument("-end", "--end_id", type=int, required=False, default=10)

    args = parser.parse_args()

    env = Env()
    env.read_env()

    paths = {
        "books": env.str("BOOKS"),
        "images": env.str("IMAGES"),
        "comments": env.str("COMMENTS")
    }

    for path in paths:
        pathlib.Path(paths[path]).mkdir(parents=True, exist_ok=True)

    for id in range(args.start_id, args.end_id + 1):
        book_download_link = f'https://tululu.org/txt.php?id={id}'
        response = requests.get(book_download_link, allow_redirects=False)
        try:
            check_for_redirect(response=response.status_code)
        except requests.exceptions.HTTPError:
            continue
        else:
            book_data = parse_book_page(book_link=f'https://tululu.org/b{id}/')

            book_content_path = download_txt(
                book_id=id,
                book_name=book_data["Заголовок"],
                folder=paths["books"]
            )

            with open(book_content_path, 'wb') as file:
                file.write(response.content)

            download_image(
                book_image=book_data["Обложка"],
                folder=paths["images"]
            )

            download_comment(
                book_id=id,
                book_name=book_data["Заголовок"],
                book_comments=book_data["Комментарии"],
                folder=paths["comments"]
            )

            name, genres = download_genre(
                book_name=book_data["Заголовок"],
                book_genres=book_data["Жанры"]
            )

            print(name, '\n', genres, end=print())


if __name__ == '__main__':
    main()
