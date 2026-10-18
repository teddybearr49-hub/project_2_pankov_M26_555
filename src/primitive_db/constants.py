"""Константы проекта."""

# Файлы и директории
META_FILE = "db_meta.json"
DATA_DIR = "data"
DATA_FILE_EXT = ".json"
JSON_INDENT = 2

# Схема таблиц
ID_COLUMN = "ID"
ID_TYPE = "int"
VALID_TYPES = {"int", "str", "bool"}
TYPE_SEPARATOR = ":"
BOOL_VALUES = {"true": True, "false": False}

# Синтаксис команд
EQUALS_SIGN = "="
CONDITION_LENGTH = 3  # <столбец> = <значение>
KEYWORD_FROM = "from"
KEYWORD_INTO = "into"
KEYWORD_VALUES = "values"
KEYWORD_SET = "set"
KEYWORD_WHERE = "where"
VALUES_SEPARATORS = ", \t\n"

# Взаимодействие с пользователем
COMMAND_PROMPT = ">>>Введите команду: "
CONFIRM_YES = "y"
