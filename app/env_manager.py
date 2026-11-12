"""Python ortamı ve pip paket bağımlılıklarını kontrol eden ve kuran modül."""

import importlib
import os
from pathlib import Path
import subprocess
import sys

from app.config import REQUIRED_PACKAGES
from app.logger import get_logger

logger = get_logger("env_manager")


def get_python_executable() -> str:
    """pythonw.exe altında çalışırken pip çağrıları için python.exe yolunu döndürür."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        candidate = exe.with_name("python.exe")
        if candidate.exists():
            logger.debug("pythonw.exe tespit edildi, pip için python.exe kullanılacak: %s", candidate)
            return str(candidate)
    logger.debug("Aktif Python yürütülebilir dosyası: %s", exe)
    return str(exe)


def find_missing_packages() -> list[str]:
    """REQUIRED_PACKAGES listesindeki eksik paketleri kontrol edip pip adlarını döndürür."""
    logger.info("Gerekli Python paketleri kontrol ediliyor (%d paket)...", len(REQUIRED_PACKAGES))
    missing: list[str] = []
    for module_name, pip_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
            logger.debug("Paket mevcut: %s (%s)", module_name, pip_name)
        except ImportError as exc:
            logger.warning("Eksik paket tespit edildi: %s (pip: %s) -> %s", module_name, pip_name, exc)
            missing.append(pip_name)

    if missing:
        print(f"[ENV] Eksik paketler bulundu: {', '.join(missing)}")
    else:
        print("[ENV] Tüm gerekli paketler kurulu ve doğrulandı.")
    return missing


def install_packages(packages: list[str]) -> tuple[bool, str]:
    """Eksik pip paketlerini arka planda konsol açmadan kurar."""
    if not packages:
        return True, ""

    python_exe = get_python_executable()
    cmd = [python_exe, "-m", "pip", "install", *packages]
    logger.info("Pip kurulum komutu başlatılıyor: %s", " ".join(cmd))
    print(f"[ENV] Pip kurulumu başlıyor: {' '.join(packages)}")

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=creationflags,
            timeout=300,
        )
        if proc.stdout:
            logger.debug("PIP STDOUT:\n%s", proc.stdout.strip())
        if proc.stderr:
            logger.debug("PIP STDERR:\n%s", proc.stderr.strip())

        if proc.returncode == 0:
            importlib.invalidate_caches()
            logger.info("Paket kurulumu başarıyla tamamlandı: %s", ", ".join(packages))
            print("[ENV] Paket kurulumu tamamlandı.")
            return True, ""

        err = (proc.stderr or proc.stdout or "Bilinmeyen pip kurulum hatası").strip()
        logger.error("Pip kurulumu başarısız oldu (kod=%d): %s", proc.returncode, err)
        return False, err
    except Exception as exc:
        logger.error("Pip alt işlemi çalıştırılırken istisna oluştu: %s", exc, exc_info=True)
        return False, str(exc)
