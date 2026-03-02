import configparser
import getpass
import re
import sys
from pathlib import Path

from core.keygen import generate_keys, load_public_key
from core.deploy import deploy_and_setup
from core.ssh_config import write_ssh_config, clear_known_hosts
from core.display import print_step, print_success, print_error

CONFIG_PATH = Path(__file__).parent / "config.ini"


def load_config() -> tuple[str, str, str]:
    cfg = configparser.RawConfigParser()
    cfg.read(CONFIG_PATH, encoding="utf-8")
    s = cfg["server"] if "server" in cfg else {}
    return (
        s.get("ip", "").strip(),
        s.get("password", "").strip(),
        s.get("username", "").strip().lower(),
    )


def get_credentials() -> tuple[str, str, str]:
    cfg_ip, cfg_password, cfg_username = load_config()

    ip = cfg_ip or input("  IP-адрес VPS: ").strip()

    if cfg_password:
        password = cfg_password
        print(f"  Пароль root: (из config.ini, {len(password)} символов)")
    else:
        password = getpass.getpass("  Пароль root: ")
        print(f"  (принято символов: {len(password)})")

    if cfg_username and re.match(r'^[a-z][a-z0-9_-]{0,31}$', cfg_username):
        username = cfg_username
        print(f"  Новый пользователь: {username} (из config.ini)")
    else:
        while True:
            username = input("  Имя нового пользователя (англ.): ").strip().lower()
            if re.match(r'^[a-z][a-z0-9_-]{0,31}$', username):
                break
            print("  Только латиница, цифры, _ и -, начало с буквы. Попробуй ещё раз.")

    return ip, password, username


def main() -> None:
    print("\n  === Настройка SSH-доступа по ключу ===\n")

    try:
        ip, password, username = get_credentials()

        print_step("Генерация ED25519 ключевой пары...")
        key_paths = generate_keys(ip)
        public_key = load_public_key(key_paths)

        print_step(f"Очистка старого отпечатка {ip} из known_hosts...")
        clear_known_hosts(ip)

        print_step(f"Подключение к {ip}, установка ключа и создание пользователя '{username}'...")
        deploy_and_setup(ip=ip, password=password, public_key=public_key, new_user=username)

        print_step("Запись в ~/.ssh/config...")
        root_alias = write_ssh_config(ip=ip, user="root", key_path=key_paths.private, label="vps")
        user_alias = write_ssh_config(ip=ip, user=username, key_path=key_paths.private, label=username)

        print_success(
            ip=ip,
            root_alias=root_alias,
            user_alias=user_alias,
            username=username,
            private_key_path=key_paths.private,
        )

    except KeyboardInterrupt:
        print("\n  Отменено.")
        sys.exit(0)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
