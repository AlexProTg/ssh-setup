from pathlib import Path


def print_success(
    ip: str,
    root_alias: str,
    user_alias: str,
    username: str,
    private_key_path: Path,
) -> None:
    key = private_key_path.resolve()
    print()
    print("  ✓ SSH настроен. Всё готово!")
    print()
    print("  Подключение от root:")
    print(f"    ssh {root_alias}")
    print()
    print(f"  Подключение от {username} (sudo без пароля):")
    print(f"    ssh {user_alias}")
    print()
    print("  Ключ:")
    print(f"    {key}")
    print()


def print_step(message: str) -> None:
    print(f"  >> {message}")


def print_error(message: str) -> None:
    print(f"  [ОШИБКА] {message}")
