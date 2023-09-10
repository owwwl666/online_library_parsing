from http.server import HTTPServer, SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server, shell
from pathlib import Path
import json


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')
    path = Path.cwd().joinpath('books.json')

    with open(path, 'r', encoding='utf8') as json_file:
        books = json.load(json_file)

    rendered_page = template.render(
        books=books
    )
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


on_reload()

server = Server()
server.watch('template.html', on_reload)
server.serve(root='.')
