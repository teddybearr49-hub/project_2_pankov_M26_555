import json
import os

from primitive_db.constants import DATA_DIR


def load_metadata(filepath):
    """Загружает данные из JSON-файла. Если файла нет — возвращает {}."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохраняет данные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _ensure_data_dir():
    """Создаёт директорию для данных, если её нет."""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_table_data(table_name):
    """Загружает данные таблицы из data/<table_name>.json."""
    _ensure_data_dir()
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет данные таблицы в data/<table_name>.json."""
    _ensure_data_dir()
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)