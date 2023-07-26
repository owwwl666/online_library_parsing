import pathlib

import requests
from pathlib import Path

folder = "books"
pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

for id in range(1, 11):
    url = f'https://tululu.org/txt.php?id={id}'
    response = requests.get(url)

    book = Path(folder).joinpath(f"id{id}")

    with open(book, 'wb') as file:
        file.write(response.content)
