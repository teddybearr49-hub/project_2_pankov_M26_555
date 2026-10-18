"""Разбор сложных частей команд: values, set, where."""

import shlex

from primitive_db.constants import (
    CONDITION_LENGTH,
    EQUALS_SIGN,
    KEYWORD_VALUES,
    KEYWORD_WHERE,
    VALUES_SEPARATORS,
)


def parse_condition(tokens):
    """['age', '=', '28'] -> {'age': '28'}. При ошибке синтаксиса — None.

    Значения остаются строками: к типу столбца их приводит core.
    """
    if len(tokens) != CONDITION_LENGTH or tokens[1] != EQUALS_SIGN:
        return None
    column, _, raw_value = tokens
    return {column: raw_value}


def parse_where(tokens):
    """Разбирает условие where <столбец> = <значение>."""
    return parse_condition(tokens)


def parse_set(tokens):
    """Разбирает выражение set <столбец> = <значение>."""
    return parse_condition(tokens)


def split_by_keyword(tokens, keyword):
    """Делит токены по ключевому слову: (до, после). Если слова нет — None."""
    lowered = [token.lower() for token in tokens]
    if keyword not in lowered:
        return None
    index = lowered.index(keyword)
    return tokens[:index], tokens[index + 1 :]


def parse_values(raw_tail):
    """'values ("Anna Maria", 30, true)' -> ['Anna Maria', '30', 'true'].

    Разбирает исходную строку, а не токены, чтобы строки в кавычках
    с пробелами и запятыми не разваливались. При ошибке — None.
    """
    text = raw_tail.strip()
    if not text.lower().startswith(KEYWORD_VALUES):
        return None
    text = text[len(KEYWORD_VALUES) :].strip()
    if not (text.startswith("(") and text.endswith(")")):
        return None

    lexer = shlex.shlex(text[1:-1], posix=True)
    lexer.whitespace = VALUES_SEPARATORS
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def split_where(tokens):
    """Делит токены на часть до where и условие после него."""
    return split_by_keyword(tokens, KEYWORD_WHERE)
