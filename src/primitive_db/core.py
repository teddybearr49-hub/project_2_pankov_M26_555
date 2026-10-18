"""Бизнес-логика: управление таблицами и CRUD-операции."""

from primitive_db.constants import (
    BOOL_VALUES,
    ID_COLUMN,
    ID_TYPE,
    TYPE_SEPARATOR,
    VALID_TYPES,
)
from primitive_db.decorators import confirm_action, handle_db_errors, log_time
from primitive_db.utils import delete_table_data, load_table_data


def _format_columns(columns):
    """[{'name': 'ID', 'type': 'int'}, ...] -> 'ID:int, ...'."""
    return ", ".join(f"{c['name']}{TYPE_SEPARATOR}{c['type']}" for c in columns)


def _print_invalid(value):
    """Печатает стандартное сообщение о некорректном значении."""
    print(f"Некорректное значение: {value}. Попробуйте снова.")


def _table_exists(metadata, table_name):
    """Проверяет наличие таблицы и печатает ошибку, если её нет."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return False
    return True


def _matches(row, where_clause):
    """Проверяет, подходит ли запись под условие."""
    return all(row.get(col) == val for col, val in where_clause.items())


def cast_value(raw, col_type):
    """Приводит строку к типу столбца. Возвращает (ok, value)."""
    if col_type == "int":
        try:
            return True, int(raw)
        except ValueError:
            return False, None
    if col_type == "bool":
        key = raw.lower()
        return (True, BOOL_VALUES[key]) if key in BOOL_VALUES else (False, None)
    return True, raw


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу в метаданных. Столбец ID:int добавляется сам."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None

    parsed_columns = [{"name": ID_COLUMN, "type": ID_TYPE}]
    seen_names = {ID_COLUMN}

    for col in columns:
        name, sep, col_type = col.partition(TYPE_SEPARATOR)
        name, col_type = name.strip(), col_type.strip().lower()
        if not sep or not name or name in seen_names or col_type not in VALID_TYPES:
            _print_invalid(col)
            return None
        seen_names.add(name)
        parsed_columns.append({"name": name, "type": col_type})

    metadata[table_name] = parsed_columns
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        f"{_format_columns(parsed_columns)}"
    )
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных и её файл данных."""
    if not _table_exists(metadata, table_name):
        return None
    del metadata[table_name]
    delete_table_data(table_name)
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит список всех таблиц."""
    if not metadata:
        print("Список таблиц пуст.")
        return
    for name in metadata:
        print(f"- {name}")


@handle_db_errors
def table_info(metadata, table_name):
    """Выводит структуру таблицы и количество записей."""
    if not _table_exists(metadata, table_name):
        return
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {_format_columns(metadata[table_name])}")
    print(f"Количество записей: {len(load_table_data(table_name))}")


@handle_db_errors
def prepare_clause(columns, clause, allow_id=True):
    """Приводит значения условия {'age': '28'} к типам столбцов схемы.

    Возвращает типизированный словарь или None.
    Неизвестный столбец -> KeyError (обрабатывается декоратором).
    """
    types = {c["name"]: c["type"] for c in columns}
    result = {}
    for col, raw in clause.items():
        if col not in types:
            raise KeyError(col)
        if col == ID_COLUMN and not allow_id:
            print(f'Ошибка: Столбец "{ID_COLUMN}" нельзя изменять.')
            return None
        ok, value = cast_value(raw, types[col])
        if not ok:
            _print_invalid(raw)
            return None
        result[col] = value
    return result


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет запись. Возвращает обновлённые данные таблицы или None."""
    if not _table_exists(metadata, table_name):
        return None

    columns = metadata[table_name][1:]  # без ID
    if len(values) != len(columns):
        print(
            f"Некорректное значение: ожидалось {len(columns)} значений, "
            f"получено {len(values)}. Попробуйте снова."
        )
        return None

    record = {}
    for col, raw in zip(columns, values):
        ok, value = cast_value(raw, col["type"])
        if not ok:
            _print_invalid(raw)
            return None
        record[col["name"]] = value

    table_data = load_table_data(table_name)
    new_id = max((row[ID_COLUMN] for row in table_data), default=0) + 1
    table_data.append({ID_COLUMN: new_id, **record})
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает все записи или только подходящие под условие."""
    if not where_clause:
        return list(table_data)
    return [row for row in table_data if _matches(row, where_clause)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет записи. Возвращает (данные, список ID обновлённых)."""
    updated_ids = []
    for row in table_data:
        if _matches(row, where_clause):
            row.update(set_clause)
            updated_ids.append(row[ID_COLUMN])
    return table_data, updated_ids


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data, where_clause):
    """Удаляет записи. Возвращает (оставшиеся данные, список ID удалённых)."""
    kept, deleted_ids = [], []
    for row in table_data:
        if _matches(row, where_clause):
            deleted_ids.append(row[ID_COLUMN])
        else:
            kept.append(row)
    return kept, deleted_ids
