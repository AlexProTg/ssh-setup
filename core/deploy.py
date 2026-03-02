import time
import paramiko


DEFAULT_USER = "root"
SSH_PORT = 22
TIMEOUT = 20
RETRIES = 3
RETRY_DELAY = 3


def _run(client: paramiko.SSHClient, cmd: str) -> None:
    _, stdout, _ = client.exec_command(cmd)
    stdout.channel.recv_exit_status()


def _connect(ip: str, password: str) -> paramiko.SSHClient:
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ip,
                port=SSH_PORT,
                username=DEFAULT_USER,
                password=password,
                timeout=TIMEOUT,
                banner_timeout=30,
                auth_timeout=30,
                look_for_keys=False,
                allow_agent=False,
            )
            return client
        except Exception as e:
            last_err = e
            if attempt < RETRIES:
                print(f"  Попытка {attempt}/{RETRIES} не удалась, повтор через {RETRY_DELAY}с...")
                time.sleep(RETRY_DELAY)
    raise last_err


def deploy_and_setup(ip: str, password: str, public_key: str, new_user: str) -> None:
    """Одно соединение: деплоит ключ руту и создаёт нового пользователя."""
    client = _connect(ip, password)
    escaped = public_key.replace("'", "'\\''")

    try:
        # Ключ для root
        _run(client, "mkdir -p ~/.ssh && chmod 700 ~/.ssh")
        _run(
            client,
            f"grep -qxF '{escaped}' ~/.ssh/authorized_keys 2>/dev/null "
            f"|| echo '{escaped}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys",
        )

        # Новый пользователь
        _run(client, f"id -u {new_user} &>/dev/null || useradd -m -s /bin/bash {new_user}")
        _run(client, f"echo '{new_user} ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/{new_user}")
        _run(client, f"chmod 440 /etc/sudoers.d/{new_user}")
        _run(client, f"mkdir -p /home/{new_user}/.ssh && chmod 700 /home/{new_user}/.ssh")
        _run(
            client,
            f"grep -qxF '{escaped}' /home/{new_user}/.ssh/authorized_keys 2>/dev/null "
            f"|| echo '{escaped}' >> /home/{new_user}/.ssh/authorized_keys",
        )
        _run(client, f"chmod 600 /home/{new_user}/.ssh/authorized_keys")
        _run(client, f"chown -R {new_user}:{new_user} /home/{new_user}/.ssh")

    finally:
        client.close()
