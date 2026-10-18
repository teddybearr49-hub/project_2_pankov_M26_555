"""Декораторы и замыкание для кэширования."""

import time
from functools import wraps

import prompt

from primitive_db.constants import CONFIRM_YES


def handle_db_errors(func):
    """Централизованная обработка ошибок БД. При ошибке возвращает None."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
        return None

    return wrapper


def confirm_action(action_name):
    """Фабрика декораторов: спрашивает подтверждение перед действием."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            answer = prompt.string(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            )
            if answer.strip().lower() != CONFIRM_YES:
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Замеряет и печатает время выполнения функции."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result

    return wrapper


def create_cacher():
    """Возвращает функцию cache_result с кэшем в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        """Возвращает значение из кэша или вычисляет и сохраняет его."""
        if key in cache:
            return cache[key]
        result = value_func()
        if result is not None:  # ошибки не кэшируем
            cache[key] = result
        return result

    def clear():
        """Сбрасывает кэш (после изменения данных)."""
        cache.clear()

    cache_result.clear = clear
    return cache_result
