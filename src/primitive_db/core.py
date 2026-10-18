import os

from primitive_db.constants import DATA_DIR, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    handle_db_errors,
    log_time,
)


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу в метаданных."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None

    parsed_columns = [{"name": "ID", "type": "int"}]

    for col in columns:
        if ":" not in col:
            print(f"Некорректное значение: {col}. Попробуйте снова.")
            return None
        name, col_type = col.split(":", 1)
        name = name.strip()
        col_type = col_type.strip().lower()

        if col_type not in VALID_TYPES:
            print(f"Некорректное значение: {col}. Попробуйте снова.")
            return None

        parsed_columns.append({"name": name, "type": col_type})

    metadata[table_name] = parsed_columns

    pretty = ", ".join(f"{c['name']}:{c['type']}" for c in parsed_columns)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {pretty}')
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных и её файл данных."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    del metadata[table_name]
    data_file = os.path.join(DATA_DIR, f"{table_name}.json")
    if os.path.exists(data_file):
        os.remove(data_file)
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит список всех таблиц."""
    if not metadata:
        print("Список таблиц пуст.")
        return

    for name in metadata:
        print(f"- {name}")


def _cast_value(value, col_type):
    """Приводит строковое значение к нужному типу. Возвращает (ok, value)."""
    try:
        if col_type == "int":
            return True, int(value)
        if col_type == "bool":
            return True, value.lower() in ("true", "1", "yes")
        return True, str(value)
    except (ValueError, AttributeError):
        return False, None


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет запись. Возвращает (table_data, new_id) или (None, None)."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None, None

    columns = metadata[table_name]
    expected = len(columns) - 1  # без ID
    if len(values) != expected:
        print(f"Ошибка: ожидалось {expected} значений, получено {len(values)}.")
        return None, None

    from primitive_db.utils import load_table_data

    table_data = load_table_data(table_name)
    new_id = max((row["ID"] for row in table_data), default=0) + 1

    record = {"ID": new_id}
    for col, raw in zip(columns[1:], values):
        ok, parsed = _cast_value(raw, col["type"])
        if not ok:
            print(f"Некорректное значение: {raw}. Попробуйте снова.")
            return None, None
        record[col["name"]] = parsed

    table_data.append(record)
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data, new_id


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает список записей, подходящих под условие."""
    if not where_clause:
        return list(table_data)
    result = []
    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            result.append(row)
    return result


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет записи. Возвращает (updated_data, count, updated_ids)."""
    count = 0
    updated_ids = []
    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            row.update(set_clause)
            count += 1
            updated_ids.append(row["ID"])
    return table_data, count, updated_ids


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data, where_clause):
    """Удаляет записи. Возвращает (new_data, count, deleted_ids)."""
    kept = []
    deleted_ids = []
    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            deleted_ids.append(row["ID"])
        else:
            kept.append(row)
    return kept, len(deleted_ids), deleted_ids