VALID_TYPES = {"int", "str", "bool"}


def create_table(metadata, table_name, columns):
    """
    Создаёт таблицу в метаданных.
    columns — список строк вида ["name:str", "age:int"].
    Возвращает обновлённый metadata или None, если была ошибка.
    """
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


def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит список всех таблиц."""
    if not metadata:
        print("Список таблиц пуст.")
        return

    for name in metadata:
        print(f"- {name}")
