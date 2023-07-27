import pathlib
from pathvalidate import sanitize_filename
import requests
from pathlib import Path
from bs4 import BeautifulSoup

books_folder = "books"
pathlib.Path(books_folder).mkdir(parents=True, exist_ok=True)


def check_for_redirect(response):
    if response != 200:
        raise requests.exceptions.HTTPError


def download_txt(book_link, book_id, folder):
    soup = BeautifulSoup(requests.get(book_link).text, 'lxml')
    filename = soup.find(id="content").find("h1").text.split('::')[0].strip()
    book_name = sanitize_filename(filename)
    book = Path(folder).joinpath(f"{book_id}.{book_name}.txt")
    return book


for id in range(1, 11):
    book_download_link = f'https://tululu.org/txt.php?id={id}'
    response = requests.get(book_download_link, allow_redirects=False)
    try:
        check_for_redirect(response=response.status_code)
    except requests.exceptions.HTTPError:
        continue
    else:
        book = download_txt(
            book_link=f'https://tululu.org/b{id}/',
            book_id=id,
            folder=books_folder
        )

        with open(book, 'wb') as file:
            file.write(response.content)
