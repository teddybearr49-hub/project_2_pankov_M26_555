"""Главный цикл программы: ввод, разбор команд и вызов функций core."""

import shlex

import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import (
    COMMAND_PROMPT,
    KEYWORD_FROM,
    KEYWORD_INTO,
    KEYWORD_SET,
    KEYWORD_WHERE,
    META_FILE,
)
from primitive_db.decorators import create_cacher
from primitive_db.parser import parse_set, parse_values, parse_where, split_where
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Печатает справку по всем командам."""
    print("\n***База данных***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. "
        "- создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
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
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def print_table(rows, columns):
    """Печатает записи через prettytable."""
    table = PrettyTable()
    table.field_names = [c["name"] for c in columns]
    for row in rows:
        table.add_row([row.get(c["name"], "") for c in columns])
    print(table)


def _syntax_error(command):
    """Сообщение о неверном синтаксисе команды."""
    print(f"Некорректное значение: неверный синтаксис {command}. Попробуйте снова.")


def _typed_where(metadata, table_name, tokens):
    """Разбирает условие where и приводит значения к типам столбцов."""
    where = parse_where(tokens)
    if where is None:
        _syntax_error(KEYWORD_WHERE)
        return None
    return core.prepare_clause(metadata[table_name], where)


# ---------- обработчики команд ----------


def handle_create_table(args, user_input, metadata, cache_result):
    """create_table <имя> <столбец:тип> ..."""
    if len(args) < 3:
        _syntax_error("create_table")
        return
    new_meta = core.create_table(metadata, args[1], args[2:])
    if new_meta is not None:
        save_metadata(META_FILE, new_meta)


def handle_drop_table(args, user_input, metadata, cache_result):
    """drop_table <имя>"""
    if len(args) != 2:
        _syntax_error("drop_table")
        return
    if args[1] not in metadata:  # не спрашиваем подтверждение впустую
        print(f'Ошибка: Таблица "{args[1]}" не существует.')
        return
    new_meta = core.drop_table(metadata, args[1])
    if new_meta is not None:
        save_metadata(META_FILE, new_meta)
        cache_result.clear()


def handle_list_tables(args, user_input, metadata, cache_result):
    """list_tables"""
    core.list_tables(metadata)


def handle_info(args, user_input, metadata, cache_result):
    """info <имя>"""
    if len(args) != 2:
        _syntax_error("info")
        return
    core.table_info(metadata, args[1])


def handle_insert(args, user_input, metadata, cache_result):
    """insert into <имя> values (<v1>, <v2>, ...)"""
    parts = user_input.split(maxsplit=3)
    if len(parts) != 4 or parts[1].lower() != KEYWORD_INTO:
        _syntax_error("insert")
        return
    table_name = parts[2]
    values = parse_values(parts[3])
    if values is None:
        _syntax_error("values")
        return
    table_data = core.insert(metadata, table_name, values)
    if table_data is not None:
        save_table_data(table_name, table_data)
        cache_result.clear()


def handle_select(args, user_input, metadata, cache_result):
    """select from <имя> [where <столбец> = <значение>]"""
    if len(args) < 3 or args[1].lower() != KEYWORD_FROM:
        _syntax_error("select")
        return
    table_name = args[2]
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    where = None
    if len(args) > 3:
        if args[3].lower() != KEYWORD_WHERE:
            _syntax_error("select")
            return
        where = _typed_where(metadata, table_name, args[4:])
        if where is None:
            return

    key = (table_name, tuple(sorted(where.items())) if where else None)
    rows = cache_result(key, lambda: core.select(load_table_data(table_name), where))
    if rows is not None:
        print_table(rows, metadata[table_name])


def handle_update(args, user_input, metadata, cache_result):
    """update <имя> set <столбец> = <значение> where <столбец> = <значение>"""
    if len(args) < 3 or args[2].lower() != KEYWORD_SET:
        _syntax_error("update")
        return
    table_name = args[1]
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return
    split = split_where(args[3:])
    if split is None:
        _syntax_error("update")
        return
    set_tokens, where_tokens = split

    raw_set = parse_set(set_tokens)
    if raw_set is None:
        _syntax_error(KEYWORD_SET)
        return
    set_clause = core.prepare_clause(metadata[table_name], raw_set, allow_id=False)
    where = _typed_where(metadata, table_name, where_tokens)
    if set_clause is None or where is None:
        return

    result = core.update(load_table_data(table_name), set_clause, where)
    if result is None:
        return
    new_data, updated_ids = result
    if not updated_ids:
        print("Записи не найдены.")
        return
    save_table_data(table_name, new_data)
    cache_result.clear()
    for record_id in updated_ids:
        print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')


def handle_delete(args, user_input, metadata, cache_result):
    """delete from <имя> where <столбец> = <значение>"""
    if (
        len(args) < 4
        or args[1].lower() != KEYWORD_FROM
        or args[3].lower() != KEYWORD_WHERE
    ):
        _syntax_error("delete")
        return
    table_name = args[2]
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return
    where = _typed_where(metadata, table_name, args[4:])
    if where is None:
        return

    result = core.delete(load_table_data(table_name), where)
    if result is None:
        return
    new_data, deleted_ids = result
    if not deleted_ids:
        print("Записи не найдены.")
        return
    save_table_data(table_name, new_data)
    cache_result.clear()
    for record_id in deleted_ids:
        print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')


COMMANDS = {
    "create_table": handle_create_table,
    "drop_table": handle_drop_table,
    "list_tables": handle_list_tables,
    "info": handle_info,
    "insert": handle_insert,
    "select": handle_select,
    "update": handle_update,
    "delete": handle_delete,
}


def run():
    """Главный цикл программы."""
    print_help()
    cache_result = create_cacher()

    while True:
        try:
            user_input = prompt.string(COMMAND_PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue
        if not args:
            continue

        command = args[0].lower()
        if command == "exit":
            print("Выход из программы.")
            break
        if command == "help":
            print_help()
            continue

        handler = COMMANDS.get(command)
        if handler is None:
            print(f"Функции {command} нет. Попробуйте снова.")
            continue

        try:
            metadata = load_metadata(META_FILE)
            handler(args, user_input, metadata, cache_result)
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break
