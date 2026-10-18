"""Работа с файловой системой: метаданные и данные таблиц."""

import json
import os

from primitive_db.constants import DATA_DIR, DATA_FILE_EXT, JSON_INDENT


def _read_json(filepath, default):
    """Читает JSON-файл. Если файла нет — возвращает default."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _write_json(filepath, data):
    """Записывает данные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=JSON_INDENT)


def get_table_path(table_name):
    """Возвращает путь к файлу данных таблицы."""
    return os.path.join(DATA_DIR, f"{table_name}{DATA_FILE_EXT}")


def load_metadata(filepath):
    """Загружает метаданные. Если файла нет — возвращает {}."""
    return _read_json(filepath, {})


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    _write_json(filepath, data)


def load_table_data(table_name):
    """Загружает записи таблицы. Если файла нет — возвращает []."""
    return _read_json(get_table_path(table_name), [])


def save_table_data(table_name, data):
    """Сохраняет записи таблицы в data/<table_name>.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    _write_json(get_table_path(table_name), data)


def delete_table_data(table_name):
    """Удаляет файл данных таблицы, если он существует."""
    filepath = get_table_path(table_name)
    if os.path.exists(filepath):
        os.remove(filepath)
