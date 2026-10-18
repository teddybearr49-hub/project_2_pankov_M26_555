import shlex

from prettytable import PrettyTable

from primitive_db import core
from primitive_db.decorators import create_cacher
from primitive_db.parser import parse_set, parse_where
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

DB_FILE = "db_meta.json"


def print_help():
    """Prints the help message for the current mode."""
    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) "
        "- создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def print_table(rows, columns):
    """Печатает записи через prettytable."""
    table = PrettyTable()
    table.field_names = [c["name"] for c in columns]
    for row in rows:
        table.add_row([row.get(c["name"], "") for c in columns])
    print(table)


def _parse_values(token):
    """
    token — строка вида '("Sergei", 28, true)'.
    Возвращает список значений или None.
    """
    token = token.strip()
    if not (token.startswith("(") and token.endswith(")")):
        return None
    inner = token[1:-1]
    if not inner.strip():
        return []
    try:
        return shlex.split(inner.replace(",", " "))
    except ValueError:
        return None


def run():
    """Главный цикл программы."""
    print("\n***База данных***")
    print_help()

    cache_result = create_cacher()

    while True:
        try:
            user_input = input(">>>Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break

        if not user_input:
            continue

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        command = args[0].lower()
        metadata = load_metadata(DB_FILE)

        # ---------- exit / help ----------
        if command == "exit":
            print("Выход из программы.")
            break

        if command == "help":
            print_help()
            continue

        # ---------- create_table / drop_table / list_tables ----------
        if command == "create_table":
            if len(args) < 3:
                print("Некорректное значение: недостаточно аргументов.")
                continue
            new_meta = core.create_table(metadata, args[1], args[2:])
            if new_meta is not None:
                save_metadata(DB_FILE, new_meta)
            continue

        if command == "drop_table":
            if len(args) != 2:
                print("Некорректное значение: нужно указать имя таблицы.")
                continue
            new_meta = core.drop_table(metadata, args[1])
            if new_meta is not None:
                save_metadata(DB_FILE, new_meta)
                cache_result.clear()
            continue

        if command == "list_tables":
            core.list_tables(metadata)
            continue

        # ---------- info ----------
        if command == "info":
            if len(args) != 2:
                print("Некорректное значение: нужно указать имя таблицы.")
                continue
            table_name = args[1]
            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue
            columns = metadata[table_name]
            table_data = load_table_data(table_name)
            pretty = ", ".join(f"{c['name']}:{c['type']}" for c in columns)
            print(f"Таблица: {table_name}")
            print(f"Столбцы: {pretty}")
            print(f"Количество записей: {len(table_data)}")
            continue

        # ---------- insert ----------
        if command == "insert":
            # insert into <table> values (<v1>, <v2>, ...)
            if (
                len(args) < 5
                or args[1].lower() != "into"
                or args[3].lower() != "values"
            ):
                print("Некорректное значение: неверный синтаксис insert.")
                continue
            table_name = args[2]
            values = _parse_values(" ".join(args[4:]))
            if values is None:
                print("Некорректное значение: неверный формат values.")
                continue
            table_data, _new_id = core.insert(metadata, table_name, values)
            if table_data is not None:
                save_table_data(table_name, table_data)
                cache_result.clear()
            continue

        # ---------- select ----------
        if command == "select":
            # select from <table> [where <col> = <val>]
            if len(args) < 3 or args[1].lower() != "from":
                print("Некорректное значение: неверный синтаксис select.")
                continue
            table_name = args[2]
            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue
            where = None
            if len(args) > 3:
                if args[3].lower() != "where":
                    print("Некорректное значение: ожидалось where.")
                    continue
                where = parse_where(args[4:])
                if where is None:
                    print("Некорректное значение: неверное условие where.")
                    continue
            table_data = load_table_data(table_name)

            key = (table_name, tuple(sorted(where.items())) if where else None)
            rows = cache_result(key, lambda: core.select(table_data, where))

            if rows is not None:
                print_table(rows, metadata[table_name])
            continue

        # ---------- update ----------
        if command == "update":
            # update <table> set <col> = <val> where <col> = <val>
            if (
                len(args) != 10
                or args[2].lower() != "set"
                or args[6].lower() != "where"
            ):
                print("Некорректное значение: неверный синтаксис update.")
                continue
            table_name = args[1]
            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue
            set_clause = parse_set(args[3:6])
            where = parse_where(args[7:10])
            if set_clause is None or where is None:
                print("Некорректное значение: неверное условие set/where.")
                continue
            table_data = load_table_data(table_name)
            new_data, count, ids = core.update(table_data, set_clause, where)
            if count:
                save_table_data(table_name, new_data)
                cache_result.clear()
                for i in ids:
                    print(
                        f'Запись с ID={i} в таблице "{table_name}" успешно обновлена.'
                    )
            else:
                print("Записи не найдены.")
            continue

        # ---------- delete ----------
        if command == "delete":
            # delete from <table> where <col> = <val>
            if (
                len(args) != 7
                or args[1].lower() != "from"
                or args[3].lower() != "where"
            ):
                print("Некорректное значение: неверный синтаксис delete.")
                continue
            table_name = args[2]
            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue
            where = parse_where(args[4:7])
            if where is None:
                print("Некорректное значение: неверное условие where.")
                continue
            table_data = load_table_data(table_name)
            result = core.delete(table_data, where)
            if result is None:
                continue
            new_data, count, ids = result
            if count:
                save_table_data(table_name, new_data)
                cache_result.clear()
                for i in ids:
                    print(
                        f'Запись с ID={i} успешно удалена из таблицы "{table_name}".'
                    )
            else:
                print("Записи не найдены.")
            continue

        print(f"Функции {command} нет. Попробуйте снова.")