# Примитивная база данных

Консольная СУБД на Python: таблицы со схемой (`int`, `str`, `bool`), CRUD-операции
с условиями `where`/`set`, хранение в JSON-файлах (`db_meta.json` — схема,
`data/<таблица>.json` — записи), подтверждение опасных действий, замер времени
и кэширование `select` через декораторы и замыкание.

## Установка

Требуется [uv](https://docs.astral.sh/uv/) и Python 3.12+.

```bash
git clone <url-репозитория>
cd <папка-репозитория>
make install        # или: uv sync
```

Установка как глобальной команды:

```bash
make build          # или: uv build
uv tool install dist/*.whl
```

## Запуск

```bash
make run            # или: uv run database
database            # после uv tool install
```

Проверка стиля: `make lint` (или `uv run ruff check .`).

## Управление таблицами

- `create_table <имя> <столбец:тип> ...` — создать таблицу (типы: `int`, `str`, `bool`); столбец `ID:int` добавляется автоматически
- `list_tables` — список таблиц
- `drop_table <имя>` — удалить таблицу (с подтверждением)
- `help` — справка
- `exit` — выход

```text
>>>Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool
>>>Введите команду: list_tables
- users
>>>Введите команду: drop_table users
Вы уверены, что хотите выполнить "удаление таблицы"? [y/n]: y
Таблица "users" успешно удалена.
```

## CRUD-операции

- `insert into <таблица> values (<v1>, <v2>, ...)` — добавить запись (ID генерируется автоматически, все поля обязательны)
- `select from <таблица>` — показать все записи
- `select from <таблица> where <столбец> = <значение>` — фильтр
- `update <таблица> set <столбец> = <значение> where <столбец> = <значение>` — обновить
- `delete from <таблица> where <столбец> = <значение>` — удалить (с подтверждением)
- `info <таблица>` — информация о таблице

Строковые значения указываются в кавычках: `"Sergei"`. Значения в `where`/`set`
приводятся к типу столбца; некорректный тип или неизвестный столбец дают ошибку.

```text
>>>Введите команду: insert into users values ("Sergei", 28, true)
Запись с ID=1 успешно добавлена в таблицу "users".
Функция insert выполнилась за 0.001 секунд.
>>>Введите команду: select from users where age = 28
Функция select выполнилась за 0.000 секунд.
+----+--------+-----+-----------+
| ID |  name  | age | is_active |
+----+--------+-----+-----------+
| 1  | Sergei |  28 |    True   |
+----+--------+-----+-----------+
>>>Введите команду: update users set age = 29 where name = "Sergei"
Запись с ID=1 в таблице "users" успешно обновлена.
>>>Введите команду: info users
Таблица: users
Столбцы: ID:int, name:str, age:int, is_active:bool
Количество записей: 1
```

## Обработка ошибок и подтверждение действий

- Функции `core` обёрнуты декоратором `handle_db_errors` — исключения
  (`KeyError`, `ValueError`, `FileNotFoundError` и др.) перехватываются
  и выводятся человекочитаемо, без трейсбеков.
- Опасные операции — `drop_table` и `delete` — требуют подтверждения
  через декоратор `confirm_action`:
  `Вы уверены, что хотите выполнить "<действие>"? [y/n]:`.
- `insert` и `select` логируют время выполнения через декоратор `log_time`.
- Результаты `select` кэшируются в замыкании `create_cacher()`: повторный
  одинаковый запрос берётся из кэша без чтения файла. Кэш сбрасывается
  при `insert`/`update`/`delete`/`drop_table`.

```text
>>>Введите команду: delete from users where ID = 1
Вы уверены, что хотите выполнить "удаление записи"? [y/n]: n
Операция отменена.
```

## Структура проекта

```text
src/primitive_db/
├── main.py         # точка входа
├── engine.py       # главный цикл, разбор ввода, вызов команд
├── core.py         # логика таблиц и CRUD
├── parser.py       # разбор values / set / where
├── utils.py        # чтение и запись JSON
├── decorators.py   # handle_db_errors, confirm_action, log_time, create_cacher
└── constants.py    # константы
```

## Демонстрация

Полный цикл: создание таблицы, CRUD, подтверждение удаления, удаление таблицы.

[![asciicast](https://asciinema.org/a/aJbEYp5owoQNGgSo.svg)](https://asciinema.org/a/aJbEYp5owoQNGgSo)
