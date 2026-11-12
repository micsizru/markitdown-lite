"""MarkItDown Hızlı Dönüştürücü - Ana Giriş Noktası (Bootstrapper)."""

import os
import sys

# pythonw.exe altında erken aşama çökme koruması (logger devreye girene kadar)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# Çalışma dizinini proje köküne sabitle
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.logger import get_logger, init_session_logger, log_exception


def _enable_windows_high_dpi() -> None:
    """Windows yüksek DPI ekranlarda bulanık yazı sorununu giderir."""
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def main() -> None:
    log_path = init_session_logger()
    logger = get_logger("bootstrap")
    logger.info("Uygulama başlatılıyor (High-DPI etkinleştiriliyor)...")

    _enable_windows_high_dpi()

    from app.ui.main_window import MainWindow

    root = tk.Tk()
    _app = MainWindow(root)

    def _on_close() -> None:
        logger.info("Kullanıcı pencereyi kapattı. Oturum sonlandırılıyor (Log: %s).", log_path.name)
        print("[EXIT] Uygulama normal şekilde kapatıldı.")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    logger.info("Tkinter mainloop başlatıldı.")
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            log_exception("FATAL_STARTUP_ERROR", e)
        except Exception:
            pass
        try:
            from app.i18n import t

            err_title = t("err_startup_title")
        except Exception:
            err_title = "Başlatma Hatası"
        messagebox.showerror(err_title, str(e))
