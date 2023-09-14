from jinja2 import Environment, FileSystemLoader, select_autoescape
from more_itertools import chunked
from livereload import Server
from pathlib import Path
import json
import argparse

AMOUNT_BOOKS_ON_PAGE = 10


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", required=False, type=str, default="",
                        help="Путь к файлу books.json, который был создан в скрипте parse_tululu_category."
                             "Если путь раннее не был указан, то файл сохранился в корень проекта.")
    args = parser.parse_args()

    template = env.get_template('template.html')

    path = Path(args.json_path).joinpath('books.json')
    Path('pages').mkdir(parents=True, exist_ok=True)

    with open(path, 'r', encoding='utf8') as json_file:
        books = json.load(json_file)

    book_pages = list(chunked(books, AMOUNT_BOOKS_ON_PAGE))
    pages_count = len(book_pages)
    pages_range = range(1, len(book_pages) + 1)

    for page_number, page in enumerate(book_pages, 1):
        page_path = Path('pages').joinpath(f'index{page_number}.html')
        rendered_page = template.render(
            books=list(chunked(page, 2)),
            pages_range=pages_range,
            pages_count=pages_count,
            current_page=page_number,
        )
        with open(page_path, 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    on_reload()

    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')
