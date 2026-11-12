"""Uygulama genelinde kullanılan sabitler, koyu tema renk paleti, fontlar ve paket listesi."""

from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent
PYCACHE_LOG_DIR: Path = BASE_DIR / "__pycache__"

APP_TITLE: str = "MarkItDown - Desktop Document Converter v2.0"
WINDOW_WIDTH: int = 920
WINDOW_HEIGHT: int = 560

COLORS: dict[str, str] = {
    # Ana arka planlar (Dark Slate / Obsidian)
    "bg": "#13151f",
    "menubar_bg": "#181a26",
    "card_bg": "#1b1e2b",
    "card_subtle": "#222636",
    "row_bg": "#242838",
    "row_hover": "#2c3144",
    "drop_bg": "#191c28",
    # Çerçeveler
    "border": "#2a2e42",
    "border_subtle": "#25293a",
    "border_active": "#6366f1",
    "dashed_border": "#4b5270",
    # Vurgu ve Buton Renkleri
    "primary": "#2e358f",
    "primary_hover": "#3b44b0",
    "primary_disabled": "#222645",
    "accent_lilac": "#a5b4fc",
    "accent_lilac_hover": "#c7d2fe",
    "accent_lilac_fg": "#13151f",
    "reconvert_bg": "#3730a3",
    "reconvert_hover": "#4338ca",
    "secondary_bg": "#25293a",
    "secondary_hover": "#31364d",
    "secondary_fg": "#e2e8f0",
    "action_bg": "#232634",
    "action_hover": "#2d3142",
    "action_fg": "#e2e8f0",
    "action_success_bg": "#14532d",
    "action_success_fg": "#86efac",
    "danger_btn_bg": "#2d1f28",
    "danger_btn_hover": "#7f1d1d",
    "danger_btn_fg": "#fca5a5",
    "danger_btn_border": "#5c2836",
    "disabled_bg": "#1b1e2b",
    "disabled_fg": "#565c78",
    # Metin Renkleri
    "text_main": "#f1f5f9",
    "text_muted": "#94a3b8",
    "text_light": "#64748b",
    # Durum Rozetleri (Üst Bar Pill Badge)
    "step_idle_bg": "#222636",
    "step_idle_fg": "#cbd5e1",
    "step_ready_bg": "#222636",
    "step_ready_fg": "#e2e8f0",
    "step_working_bg": "#312e81",
    "step_working_fg": "#c7d2fe",
    "step_done_bg": "#14532d",
    "step_done_fg": "#86efac",
    "step_error_bg": "#450a0a",
    "step_error_fg": "#fca5a5",
    # Switch / Toggle Renkleri
    "switch_on_bg": "#818cf8",
    "switch_off_bg": "#33384e",
    "switch_knob": "#13151f",
    "switch_knob_off": "#94a3b8",
    "badge_on_bg": "#818cf8",
    "badge_on_fg": "#13151f",
    "badge_off_bg": "#33384e",
    "badge_off_fg": "#94a3b8",
    # İlerleme Çubuğu (Progress)
    "progress_track": "#141620",
    "progress_fill": "#818cf8",
    "progress_fill_alt": "#6366f1",
    # Durum İkon / Vurgu Renkleri
    "success": "#4ade80",
    "warning": "#fbbf24",
    "danger": "#f87171",
    # Dosya Türü İkon Renkleri
    "icon_pdf": "#dc2626",
    "icon_word": "#2563eb",
    "icon_excel": "#16a34a",
    "icon_ppt": "#ea580c",
    "icon_archive": "#ca8a04",
    "icon_default": "#4f46e5",
}

FONTS: dict[str, tuple] = {
    "menubar": ("Segoe UI", 9),
    "app_title": ("Segoe UI", 16, "bold"),
    "step_badge": ("Segoe UI", 9, "bold"),
    "section_header": ("Segoe UI", 12, "bold"),
    "section_sub": ("Segoe UI", 9),
    "table_header": ("Segoe UI", 9, "bold"),
    "button_select": ("Segoe UI", 9, "bold"),
    "button_convert": ("Segoe UI", 10, "bold"),
    "button_action": ("Segoe UI", 9),
    "file_name": ("Segoe UI", 9),
    "file_meta": ("Segoe UI", 9),
    "file_icon": ("Segoe UI", 7, "bold"),
    "drop_zone": ("Segoe UI", 10),
    "option_title": ("Segoe UI", 10, "bold"),
    "option_desc": ("Segoe UI", 9),
    "option_badge": ("Segoe UI", 8, "bold"),
    "status": ("Segoe UI", 9, "bold"),
    "progress_pct": ("Segoe UI", 9, "bold"),
    "metric_val_hero": ("Segoe UI", 26, "bold"),
    "metric_val": ("Segoe UI", 15, "bold"),
    "metric_lbl": ("Segoe UI", 9),
}

FILETYPE_PATTERNS: list[tuple[str, str]] = [
    (
        "filetype_supported",
        "*.pdf *.docx *.pptx *.xlsx *.xls *.html *.htm *.csv *.json *.xml *.txt *.zip *.msg *.epub",
    ),
    ("filetype_pdf", "*.pdf"),
    ("filetype_office", "*.docx *.pptx *.xlsx *.xls *.msg"),
    ("filetype_web_data", "*.html *.htm *.csv *.json *.xml *.txt *.zip"),
    ("filetype_all", "*.*"),
]

SUPPORTED_FILETYPES: list[tuple[str, str]] = [
    (
        "Desteklenen Dosyalar",
        "*.pdf *.docx *.pptx *.xlsx *.xls *.html *.htm *.csv *.json *.xml *.txt *.zip *.msg *.epub",
    ),
    ("PDF Dosyaları", "*.pdf"),
    ("Office Belgeleri", "*.docx *.pptx *.xlsx *.xls *.msg"),
    ("Web ve Veri Dosyaları", "*.html *.htm *.csv *.json *.xml *.txt *.zip"),
    ("Tüm Dosyalar", "*.*"),
]

REQUIRED_PACKAGES: list[tuple[str, str]] = [
    ("markitdown", "markitdown"),
    ("pdfminer", "pdfminer.six"),
    ("pdfplumber", "pdfplumber"),
    ("mammoth", "mammoth"),
    ("openpyxl", "openpyxl"),
    ("pandas", "pandas"),
    ("xlrd", "xlrd"),
    ("pptx", "python-pptx"),
    ("lxml", "lxml"),
    ("bs4", "beautifulsoup4"),
    ("olefile", "olefile"),
]
