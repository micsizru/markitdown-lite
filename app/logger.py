"""__pycache__ dizinine tarih + saat + benzersiz ID ile detaylı oturum logu yazan modül."""

from datetime import datetime
import logging
import os
import platform
import sys
import threading
import traceback
import uuid
from pathlib import Path

from app.config import PYCACHE_LOG_DIR

_SESSION_LOG_PATH: Path | None = None
_LOGGER_INITIALIZED: bool = False


class _LogStreamRedirector:
    """sys.stdout ve sys.stderr çıktılarını yakalayıp log dosyasına yönlendirir.

    pythonw.exe altında sys.stdout/stderr None olduğunda çökmeyi engeller ve
    tüm print() veya alt kütüphane mesajlarını oturum loguna yazar.
    """

    def __init__(self, log_file_path: Path, stream_Label: str) -> None:
        self.log_file_path = log_file_path
        self.stream_label = stream_Label
        self.encoding = "utf-8"
        self._lock = threading.Lock()
        self._buffer: str = ""

    def _emit_line(self, text: str) -> None:
        cleaned = text.strip("\r\n")
        if not cleaned.strip():
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        thread_name = threading.current_thread().name
        line = f"[{timestamp}] [{self.stream_label}] [{thread_name}] {cleaned}\n"
        try:
            with open(self.log_file_path, "a", encoding="utf-8", errors="replace") as f:
                f.write(line)
        except Exception:
            pass

    def write(self, message: str) -> int:
        if not message:
            return 0
        with self._lock:
            self._buffer += message
            while "\n" in self._buffer:
                line_part, self._buffer = self._buffer.split("\n", 1)
                self._emit_line(line_part)
        return len(message)

    def flush(self) -> None:
        with self._lock:
            if self._buffer.strip():
                self._emit_line(self._buffer)
            self._buffer = ""

    def isatty(self) -> bool:
        return False


def init_session_logger() -> Path:
    """Yeni bir oturum log dosyası oluşturur ve logging + stdout/stderr yönlendirmesini başlatır."""
    global _SESSION_LOG_PATH, _LOGGER_INITIALIZED

    if _LOGGER_INITIALIZED and _SESSION_LOG_PATH is not None:
        return _SESSION_LOG_PATH

    PYCACHE_LOG_DIR.mkdir(parents=True, exist_ok=True)

    env_log_file = os.environ.get("MARKITDOWN_LOG_FILE", "").strip()
    if env_log_file:
        log_path = Path(env_log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        log_path = PYCACHE_LOG_DIR / f"run_{now_str}_{unique_id}.log"

    _SESSION_LOG_PATH = log_path

    # sys.stdout ve sys.stderr'i log dosyasına bağla (hem pythonw.exe çökme koruması hem print yakalama)
    sys.stdout = _LogStreamRedirector(log_path, "STDOUT")
    sys.stderr = _LogStreamRedirector(log_path, "STDERR")

    root_logger = logging.getLogger("markitdown_app")
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(threadName)s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _LOGGER_INITIALIZED = True

    root_logger.info("=" * 76)
    root_logger.info("MARKITDOWN OTURUM LOGU BAŞLATILDI")
    root_logger.info("Log Dosyası     : %s", log_path)
    root_logger.info("Tarih / Saat    : %s", datetime.now().isoformat())
    root_logger.info("Python Sürümü   : %s", sys.version.replace("\n", " "))
    root_logger.info("Python Yolu     : %s", sys.executable)
    root_logger.info("İşletim Sistemi : %s (%s)", platform.system(), platform.version())
    root_logger.info("Çalışma Dizini  : %s", os.getcwd())
    root_logger.info("=" * 76)
    print(f"[BOOT] Loglama sistemi aktif -> {log_path.name}")

    return log_path


def get_logger(name: str = "markitdown_app") -> logging.Logger:
    """Uygulama logger nesnesini döndürür."""
    if not _LOGGER_INITIALIZED:
        init_session_logger()
    if name == "markitdown_app":
        return logging.getLogger("markitdown_app")
    return logging.getLogger(f"markitdown_app.{name}")


def get_session_log_path() -> Path | None:
    """Aktif oturumun log dosya yolunu döndürür."""
    return _SESSION_LOG_PATH


def log_exception(context: str, exc: BaseException) -> None:
    """Hata detayını ve tam traceback'i log dosyasına yazar."""
    logger = get_logger("exception")
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("HATA YAKALANDI [%s]: %s\n%s", context, exc, tb_str)
