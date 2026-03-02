import os
import sys
from pathlib import Path
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)


KEYS_DIR = Path(__file__).parent.parent / "keys"


@dataclass
class KeyPaths:
    private: Path
    public: Path


def _fix_windows_key_permissions(path: Path) -> None:
    """Оставляет доступ к ключу только текущему пользователю (требование OpenSSH на Windows).

    /inheritance:r  — отключает наследование и удаляет все унаследованные ACE
    /grant:r        — заменяет все права текущего пользователя на FullControl
    Работает на любой локали Windows, т.к. не зависит от имён групп.
    """
    import subprocess
    p = str(path)
    current_user = os.environ.get("USERNAME", "")
    subprocess.run(["icacls", p, "/inheritance:r"], check=True, capture_output=True)
    subprocess.run(["icacls", p, "/grant:r", f"{current_user}:F"], check=True, capture_output=True)


def generate_keys(ip: str) -> KeyPaths:
    """Генерирует ED25519 ключевую пару для конкретного IP и сохраняет в папку keys/."""
    KEYS_DIR.mkdir(exist_ok=True)

    safe_ip = ip.replace(".", "-")
    private_path = KEYS_DIR / f"id_ed25519_{safe_ip}"
    public_path  = KEYS_DIR / f"id_ed25519_{safe_ip}.pub"

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(Encoding.PEM, PrivateFormat.OpenSSH, NoEncryption())
    private_path.write_bytes(private_bytes)

    if sys.platform == "win32":
        _fix_windows_key_permissions(private_path)
    else:
        private_path.chmod(0o600)

    public_str = public_key.public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode()
    public_path.write_text(public_str, encoding="utf-8")

    return KeyPaths(private=private_path, public=public_path)


def load_public_key(paths: KeyPaths) -> str:
    return paths.public.read_text(encoding="utf-8").strip()
