import subprocess
from pathlib import Path


SSH_CONFIG_PATH = Path.home() / ".ssh" / "config"
KNOWN_HOSTS_PATH = Path.home() / ".ssh" / "known_hosts"


def _make_alias(ip: str, label: str = "vps") -> str:
    return f"{label}-{ip.replace('.', '-')}"


def _build_block(alias: str, ip: str, user: str, key_path: Path) -> str:
    from datetime import datetime
    key  = str(key_path.resolve()).replace("\\", "/")
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"\n# === added by ssh-setup | {ip} | {date} ===\n"
        f"Host {alias}\n"
        f"    HostName {ip}\n"
        f"    User {user}\n"
        f"    IdentityFile {key}\n"
        f"    IdentitiesOnly yes\n"
        f"    StrictHostKeyChecking accept-new\n"
    )


def clear_known_hosts(ip: str) -> None:
    """Удаляет старый отпечаток сервера из known_hosts (нужно при пересоздании сервера)."""
    if not KNOWN_HOSTS_PATH.exists():
        return
    subprocess.run(
        ["ssh-keygen", "-R", ip],
        capture_output=True,
    )


def _block_exists(config_text: str, alias: str) -> bool:
    return f"Host {alias}" in config_text


def _insert_before_host_star(existing: str, block: str) -> str:
    """Вставляет блок перед секцией 'Host *', если она есть."""
    marker = "Host *"
    idx = existing.find(f"\n{marker}")
    if idx == -1:
        idx = existing.find(marker)
        if idx == -1:
            return existing + block
    return existing[:idx] + block + existing[idx:]


def _remove_block(config_text: str, alias: str) -> str:
    """Удаляет существующий блок хоста из конфига."""
    lines = config_text.splitlines(keepends=True)
    result = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == f"Host {alias}":
            inside = True
            continue
        if inside:
            if stripped.startswith("Host ") and stripped != f"Host {alias}":
                inside = False
            else:
                continue
        if not inside:
            result.append(line)
    return "".join(result)


def write_ssh_config(ip: str, user: str, key_path: Path, label: str = "vps") -> str:
    """Пишет/обновляет запись в ~/.ssh/config перед блоком Host *. Возвращает алиас."""
    SSH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    alias = _make_alias(ip, label)
    existing = SSH_CONFIG_PATH.read_text(encoding="utf-8") if SSH_CONFIG_PATH.exists() else ""

    if _block_exists(existing, alias):
        existing = _remove_block(existing, alias)

    block = _build_block(alias, ip, user, key_path)
    updated = _insert_before_host_star(existing, block)
    SSH_CONFIG_PATH.write_text(updated, encoding="utf-8")

    return alias
