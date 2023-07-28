import pathlib
from pathvalidate import sanitize_filename
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

books_folder = "books"
images_folder = "images"
pathlib.Path(books_folder).mkdir(parents=True, exist_ok=True)
pathlib.Path(images_folder).mkdir(parents=True, exist_ok=True)


def check_for_redirect(response):
    if response != 200:
        raise requests.exceptions.HTTPError


def download_txt(book_link, book_id, folder):
    html_text = requests.get(book_link).text
    soup = BeautifulSoup(html_text, 'lxml')
    filename = soup.find(id="content").find("h1").text.split('::')[0].strip()
    book_name = sanitize_filename(filename)
    book_path = Path(folder).joinpath(f"{book_id}.{book_name}.txt")
    return book_path


def download_image(book_link, folder):
    html_text = requests.get(book_link).text
    soup = BeautifulSoup(html_text, 'lxml')
    img_path = soup.find(class_="bookimage").find("img")["src"]
    url_book_img_path = urljoin("https://tululu.org", img_path)
    image_download = requests.get(url_book_img_path)
    image_name = url_book_img_path.split('/')[-1]
    book_img_path = Path(folder).joinpath(f"{image_name}")
    with open(book_img_path, 'wb') as file:
        file.write(image_download.content)


def download_comment(book_link):
    html_text = requests.get(book_link).text
    soup = BeautifulSoup(html_text, 'lxml')
    book_comments = soup.find_all(class_="texts")
    for book_comment in book_comments:
        print(book_comment.find(class_="black").text, end=print())


for id in range(1, 11):
    book_download_link = f'https://tululu.org/txt.php?id={id}'
    response = requests.get(book_download_link, allow_redirects=False)
    try:
        check_for_redirect(response=response.status_code)
    except requests.exceptions.HTTPError:
        continue
    else:
        book_content_path = download_txt(
            book_link=f'https://tululu.org/b{id}/',
            book_id=id,
            folder=books_folder
        )

        download_image(
            book_link=f'https://tululu.org/b{id}/',
            folder=images_folder
        )

        download_comment(
            book_link=f'https://tululu.org/b{id}/'
        )

        with open(book_content_path, 'wb') as file:
            file.write(response.content)
