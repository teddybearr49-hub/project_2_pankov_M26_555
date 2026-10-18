import shlex

from primitive_db import core
from primitive_db.utils import load_metadata, save_metadata

DB_FILE = "db_meta.json"


def print_help():
    """Prints the help message for the current mode."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run():
    """Главный цикл программы."""
    print("\n***База данных***")
    print_help()

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

        if command == "exit":
            print("Выход из программы.")
            break

        elif command == "help":
            print_help()

        elif command == "list_tables":
            core.list_tables(metadata)

        elif command == "create_table":
            if len(args) < 3:
                print("Некорректное значение: недостаточно аргументов. Попробуйте снова.")
                continue
            table_name = args[1]
            columns = args[2:]
            new_meta = core.create_table(metadata, table_name, columns)
            if new_meta is not None:
                save_metadata(DB_FILE, new_meta)

        elif command == "drop_table":
            if len(args) != 2:
                print(
                    "Некорректное значение: нужно указать имя таблицы. "
                    "Попробуйте снова."
                )
                continue
            new_meta = core.drop_table(metadata, args[1])
            if new_meta is not None:
                save_metadata(DB_FILE, new_meta)

        else:
            print(f"Функции {command} нет. Попробуйте снова.")