from http.server import HTTPServer, SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import json

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)

template = env.get_template('index.html')
path = Path.cwd().joinpath('books.json')

with open(path, 'r', encoding='utf8') as json_file:
    books = json.load(json_file)

rendered_page = template.render(
    books=books
)

with open('template.html', 'w', encoding="utf8") as file:
    file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
server.serve_forever()
