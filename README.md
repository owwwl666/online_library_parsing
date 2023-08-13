# Описание
Парсинг онлайн-библиотеки [https://tululu.org/](https://tululu.org/). Проект состоит из двух скриптов

## Установка зависимостей
Введите в терминале команду для установки необходимых пакетов и зависимостей:
```
pip install -r requirements.txt
```

## parse_tululu


#### Переменные окружения
В скрипте используются три переменных окружения в качестве желаемого пути сохранения файлов:
- BOOKS=ПУТЬ_СОХРАНЕНИЯ_КНИГИ
- IMAGES=ПУТЬ_СОХРАНЕНИЯ_ОБЛОЖКИ_КНИГИ
- COMMENTS=ПУТЬ_СОХРАНЕНИЯ_КОММЕНТАРИЕВ_И_ОТЗЫВОВО_О_КНИГЕ

#### Запуск скрипта
Скрипт обрабатывает выбранные пользователям по id книги и скачивает с сайта всю необходимую информацию о ней: название, автора, обложку, жанр и т.д.

Для запуска скрипта выполните в терминале команду, передав необходимые аргументы:

```
python parse_tululu.py -start 11 -end 20
```

Где аргументы:
- -start - начальный id книги
- -end - конечный id книги

По-умолчанию, `-start=1` `-end=10`. Если не хотите передавать аргументы, то достаточно выполнить команду и она скачает и выведет всю необходимую информацию о книгах с 1 по 10 id:
```
python parse_tululu.py
```

### Результаты
![](https://github.com/owwwl666/online_library_parsing/assets/131767856/3ebddc31-6236-4983-b4a9-1a2bce771ea0)
![](https://github.com/owwwl666/online_library_parsing/assets/131767856/b1393094-4b7a-4199-a1fd-6d36d842dd46)

## parse_tululu_category

#### Запуск скрипта
Скрипт обрабатывает заданные пользователем страницы с книгами,скачивает всю имеющуюся на этих страницах литературу и сохраняет локально запрошенную пользователем информацию о каждой книге.

Для запуска скрипта последовательно передайте необходимые аргументы:

- --star_page - номер начальной страницы. По умолчанию равен 1
- --end_page - номер конечной страницы. По умолчанию равен последеней странице на сайте
- --dest_folder - Путь к каталогу с результатами парсинга. По-умолчанию корень проекта
- --skip_imgs - Не скачивать обложки книги
- --skip_txt - Не скачивать текст книги

Пример запуска , при котором скрипт скачивает все книги:
```
python parse_tululu_category.py
```

Пример запуска , при котором скрипт скачивает от 500 до 600 книги:
```
python parse_tululu_category.py --start_page 500 --end_page 600
```

Пример запуска , при котором скрипт скачивает от 500 до последней книги:
```
python parse_tululu_category.py --start_page 500
```

#### Результаты
Ниже представлен скриншот работы скрипта, в котором он скачивает обложки и текст , а также собирает в json файл всю информацию о каждой книге со всех страниц сайта, которые задал пользователь:
![image](https://github.com/owwwl666/online_library_parsing/assets/131767856/64fcce58-4d81-4155-aba2-8eada6d1dd67)


