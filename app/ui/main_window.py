"""Ana pencere tasarımı, olay yöneticileri ve arka plan iş parçacığı koordinasyonu."""

from datetime import datetime
import os
from pathlib import Path
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any

from app.config import (
    COLORS,
    FONTS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from app.converter_service import ConversionOptions, ConversionResult, ConverterService
from app.env_manager import find_missing_packages, install_packages
from app.i18n import (
    LANGUAGES,
    get_supported_filetypes,
    load_language,
    save_language,
    t,
)
from app.logger import get_logger, get_session_log_path, log_exception
from app.ui.widgets import DarkProgressBar, DashedDropZone, HoverButton, ToggleOptionRow, ToolTip

logger = get_logger("ui.main_window")


def _truncate_middle(text: str, max_len: int = 58) -> str:
    """Çok uzun dosya adlarını ortadan kısaltarak arayüzün kaymasını önler."""
    if len(text) <= max_len:
        return text
    keep = (max_len - 3) // 2
    return f"{text[:keep]}...{text[-keep:]}"


def _format_file_size(size_bytes: int) -> str:
    """Byte cinsinden dosya boyutunu okunabilir formata çevirir."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    kb = size_bytes / 1024
    if kb < 1024:
        return f"{kb:.0f} KB" if kb >= 10 else f"{kb:.1f} KB"
    mb = kb / 1024
    return f"{mb:.2f} MB"


def _get_file_badge_style(path: Path) -> tuple[str, str]:
    """Dosya uzantısına göre (Rozet Metni, Arka Plan Rengi) döndürür."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "PDF", COLORS["icon_pdf"]
    if ext in (".docx", ".doc"):
        return "W", COLORS["icon_word"]
    if ext in (".xlsx", ".xls", ".csv"):
        return "XLS", COLORS["icon_excel"]
    if ext in (".pptx", ".ppt"):
        return "PPT", COLORS["icon_ppt"]
    if ext in (".zip", ".epub"):
        return "ZIP", COLORS["icon_archive"]
    return (ext.lstrip(".")[:3].upper() or "FILE"), COLORS["icon_default"]


class MainWindow:
    """MarkItDown Koyu Tema 2 Sütunlu Ana Pencere Sınıfı."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.current_lang: str = load_language()
        self.selected_files: list[Path] = []
        self.file_statuses: dict[Path, str] = {}
        self.converter_service = ConverterService()
        self.is_converting: bool = False
        self.conversion_run_count: int = 0
        self.has_converted_current_selection: bool = False

        # Son başarılı dönüşüm bilgileri (Hızlı aksiyon butonları için)
        self.last_output_path: Path | None = None
        self.last_converted_content: str = ""

        # Dil değişiminde dinamik metinleri anında yenileyebilmek için durum takibi
        self._badge_state: tuple[str, str, str] = (
            "badge_ready",
            COLORS["step_idle_bg"],
            COLORS["step_idle_fg"],
        )
        self._status_state: tuple[str, dict[str, Any], str] = (
            "status_ready",
            {},
            COLORS["text_muted"],
        )
        self._progress_state_key: str = "progress_idle"
        self._progress_pct: int = 0
        self._convert_btn_key: str = "btn_convert"
        self._copy_feedback_active: bool = False
        self._last_metrics: dict[str, Any] | None = None

        # Kullanıcı seçenekleri (Varsayılan olarak her ikisi de açık)
        self.var_pdf_plain = tk.BooleanVar(value=True)
        self.var_clean_llm = tk.BooleanVar(value=True)

        self.root.title(t("window_title"))
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(True, True)

        self._configure_ttk_styles()
        self._build_ui()
        self._fit_and_center_window(WINDOW_WIDTH, WINDOW_HEIGHT)

    def _configure_ttk_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except Exception as exc:
            logger.debug("ttk tema ayarlanamadı: %s", exc)

        try:
            style.configure(
                "Lang.TCombobox",
                padding=(10, 5),
                foreground=COLORS["text_main"],
                fieldbackground=COLORS["card_subtle"],
                background=COLORS["card_subtle"],
                bordercolor=COLORS["border"],
                lightcolor=COLORS["border"],
                darkcolor=COLORS["border"],
                arrowcolor=COLORS["text_main"],
            )
            style.map(
                "Lang.TCombobox",
                fieldbackground=[("readonly", COLORS["card_subtle"])],
                selectbackground=[("readonly", COLORS["card_subtle"])],
                selectforeground=[("readonly", COLORS["text_main"])],
                background=[("readonly", COLORS["card_subtle"])],
            )
            self.root.option_add("*TCombobox*Listbox.font", FONTS["file_meta"])
            self.root.option_add("*TCombobox*Listbox.background", COLORS["card_subtle"])
            self.root.option_add("*TCombobox*Listbox.foreground", COLORS["text_main"])
            self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["primary"])
            self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        except Exception as exc:
            logger.debug("Lang.TCombobox stili ayarlanamadı: %s", exc)

    def _fit_and_center_window(self, min_width: int, min_height: int) -> None:
        """High-DPI ekran ölçeklemesini hesaba katarak tüm bileşenlerin eksiksiz sığacağı boyutta açar."""
        self.root.update_idletasks()
        req_w = self.root.winfo_reqwidth() + 120
        req_h = self.root.winfo_reqheight() + 48

        final_w = max(min_width, req_w)
        final_h = max(min_height, req_h)

        self.root.minsize(final_w, final_h)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - final_w) // 2)
        y = max(0, (screen_height - final_h) // 2)

        self.root.geometry(f"{final_w}x{final_h}+{x}+{y}")
        logger.info(
            "MainWindow boyutlandı ve ortalandı: %dx%d (req=%dx%d)",
            final_w,
            final_h,
            req_w,
            req_h,
        )
        print(f"[UI] Pencere boyutu ayarlandı: {final_w}x{final_h}")

    def _ensure_window_fits_content(self) -> None:
        """Dil veya içerik değiştiğinde kullanıcının pencere boyutunu bozmadan çizimi günceller."""
        self.root.update_idletasks()

    def _build_ui(self) -> None:
        # Ana İçerik Çerçevesi
        main_frame = tk.Frame(self.root, padx=20, pady=14, bg=COLORS["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # =====================================================================
        # 1. ÜST BAR: MarkItDown + Dil Seçici
        # =====================================================================
        top_bar = tk.Frame(main_frame, bg=COLORS["bg"])
        top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 12))

        self.lbl_title = tk.Label(
            top_bar,
            text=t("app_title"),
            fg=COLORS["text_main"],
            bg=COLORS["bg"],
            font=FONTS["app_title"],
            anchor="w",
        )
        self.lbl_title.pack(side=tk.LEFT)

        # Geriye dönük test uyumluluğu için görünmez referanslar
        self.badge_container = tk.Frame(top_bar, bg=COLORS["step_idle_bg"])
        self.lbl_badge_dot = tk.Label(self.badge_container, text="●")
        self.lbl_step_badge = tk.Label(
            self.badge_container,
            text=t("badge_ready"),
            bg=COLORS["step_idle_bg"],
            fg=COLORS["step_idle_fg"],
            font=FONTS["step_badge"],
        )

        # Dil Seçici Combobox (Sağ Üst)
        self.cmb_language = ttk.Combobox(
            top_bar,
            values=list(LANGUAGES.values()),
            state="readonly",
            width=11,
            font=FONTS["step_badge"],
            style="Lang.TCombobox",
            cursor="hand2",
        )
        self.cmb_language.set(LANGUAGES.get(self.current_lang, LANGUAGES["tr"]))
        self.cmb_language.pack(side=tk.RIGHT)
        self.cmb_language.bind("<<ComboboxSelected>>", self._on_language_selected)

        self.lbl_lang_caption = tk.Label(
            top_bar,
            text=t("lbl_language"),
            fg=COLORS["text_muted"],
            bg=COLORS["bg"],
            font=FONTS["file_meta"],
        )
        self.lbl_lang_caption.pack(side=tk.RIGHT, padx=(0, 8))

        # =====================================================================
        # 2. ALT TAM GENİŞLİK KART: İlerleme + Durum + 4'lü Aksiyon Butonları
        # Not: side=tk.BOTTOM ile orta gövdeden ÖNCE pack edilir; böylece
        # yüksek DPI ekranlarda alt butonların kesilmesi imkansız hale gelir!
        # =====================================================================
        bottom_card = tk.Frame(
            main_frame,
            bg=COLORS["card_bg"],
            padx=16,
            pady=12,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        bottom_card.pack(side=tk.BOTTOM, fill=tk.X, pady=(12, 0))

        # Üst Satır: Sol Progress Bar Kapsülü + Sağ Durum Mesajı
        progress_row = tk.Frame(bottom_card, bg=COLORS["card_bg"])
        progress_row.pack(fill=tk.X, pady=(0, 10))
        progress_row.columnconfigure(0, weight=3)
        progress_row.columnconfigure(1, weight=2)

        prog_capsule = tk.Frame(
            progress_row,
            bg=COLORS["progress_track"],
            padx=12,
            pady=6,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        prog_capsule.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        prog_capsule.columnconfigure(1, weight=1)

        self.lbl_progress_pct = tk.Label(
            prog_capsule,
            text=t("progress_idle"),
            fg=COLORS["text_main"],
            bg=COLORS["progress_track"],
            font=FONTS["progress_pct"],
            anchor="w",
        )
        self.lbl_progress_pct.grid(row=0, column=0, padx=(0, 12))

        self.dark_progress = DarkProgressBar(prog_capsule, height=12)
        self.dark_progress.grid(row=0, column=1, sticky="ew")

        self.lbl_progress_info = tk.Label(
            prog_capsule,
            text="ⓘ",
            font=("Segoe UI", 10),
            fg=COLORS["text_light"],
            bg=COLORS["progress_track"],
            padx=4,
            cursor="hand2",
        )
        self.lbl_progress_info.grid(row=0, column=2, padx=(8, 0))
        self.tooltip_progress = ToolTip(self.lbl_progress_info, t("progress_tooltip"))

        # Geriye dönük test uyumluluğu için standart ttk.Progressbar nesnesi
        self.progress = ttk.Progressbar(
            bottom_card, orient=tk.HORIZONTAL, mode="determinate", maximum=100, value=0
        )

        # Sağ: Durum Bildirimi
        status_wrap = tk.Frame(progress_row, bg=COLORS["card_bg"])
        status_wrap.grid(row=0, column=1, sticky="e")

        self.lbl_status = tk.Label(
            status_wrap,
            text=t("status_ready"),
            fg=COLORS["text_muted"],
            bg=COLORS["card_bg"],
            font=FONTS["status"],
            anchor="e",
            justify=tk.RIGHT,
        )
        self.lbl_status.pack(side=tk.RIGHT)

        # Alt Satır: 4'lü Aksiyon Butonları (Convert | Copy | Open | Show in Folder)
        action_frame = tk.Frame(bottom_card, bg=COLORS["card_bg"])
        action_frame.pack(fill=tk.X)
        action_frame.columnconfigure(0, weight=14, uniform="act")
        action_frame.columnconfigure(1, weight=10, uniform="act")
        action_frame.columnconfigure(2, weight=10, uniform="act")
        action_frame.columnconfigure(3, weight=10, uniform="act")

        self.btn_convert = HoverButton(
            action_frame,
            normal_bg=COLORS["primary"],
            hover_bg=COLORS["primary_hover"],
            normal_fg="#ffffff",
            disabled_bg=COLORS["primary_disabled"],
            disabled_fg=COLORS["disabled_fg"],
            border_color=COLORS["border_active"],
            text=t("btn_convert"),
            state=tk.DISABLED,
            font=FONTS["button_convert"],
            relief="flat",
            pady=9,
            command=self.start_conversion_thread,
        )
        self.btn_convert.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_copy_md = HoverButton(
            action_frame,
            normal_bg=COLORS["action_bg"],
            hover_bg=COLORS["action_hover"],
            normal_fg=COLORS["action_fg"],
            border_color=COLORS["border"],
            text=t("btn_copy"),
            font=FONTS["button_action"],
            relief="flat",
            state=tk.DISABLED,
            pady=9,
            command=self.copy_to_clipboard,
        )
        self.btn_copy_md.grid(row=0, column=1, sticky="ew", padx=6)

        self.btn_open_md = HoverButton(
            action_frame,
            normal_bg=COLORS["action_bg"],
            hover_bg=COLORS["action_hover"],
            normal_fg=COLORS["action_fg"],
            border_color=COLORS["border"],
            text=t("btn_open"),
            font=FONTS["button_action"],
            relief="flat",
            state=tk.DISABLED,
            pady=9,
            command=self.open_output_file,
        )
        self.btn_open_md.grid(row=0, column=2, sticky="ew", padx=6)

        self.btn_reveal_folder = HoverButton(
            action_frame,
            normal_bg=COLORS["action_bg"],
            hover_bg=COLORS["action_hover"],
            normal_fg=COLORS["action_fg"],
            border_color=COLORS["border"],
            text=t("btn_reveal"),
            font=FONTS["button_action"],
            relief="flat",
            state=tk.DISABLED,
            pady=9,
            command=self.reveal_in_explorer,
        )
        self.btn_reveal_folder.grid(row=0, column=3, sticky="ew", padx=(6, 0))

        # =====================================================================
        # 3. ORTA GÖVDE: 2 Sütunlu Grid (Sol: Dosya + Ayarlar, Sağ: Çıktı Özeti)
        # =====================================================================
        body_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        body_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        body_frame.columnconfigure(0, weight=58, minsize=460)
        body_frame.columnconfigure(1, weight=42, minsize=320)
        body_frame.rowconfigure(0, weight=1)

        left_col = tk.Frame(body_frame, bg=COLORS["bg"])
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_col.columnconfigure(0, weight=1)
        left_col.rowconfigure(0, weight=1)
        left_col.rowconfigure(1, weight=0)

        right_col = tk.Frame(body_frame, bg=COLORS["bg"])
        right_col.grid(row=0, column=1, sticky="nsew")
        right_col.columnconfigure(0, weight=1)
        right_col.rowconfigure(0, weight=1)

        # =====================================================================
        # SOL ÜST KART: Kaynak Dosya
        # =====================================================================
        self.sec1_card = tk.Frame(
            left_col,
            bg=COLORS["card_bg"],
            padx=16,
            pady=14,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        self.sec1_card.grid(row=0, column=0, sticky="nsew", pady=(0, 12))

        sec1_header = tk.Frame(self.sec1_card, bg=COLORS["card_bg"])
        sec1_header.pack(fill=tk.X, pady=(0, 8))

        self.lbl_sec1_title = tk.Label(
            sec1_header,
            text=t("sec_source_file"),
            fg=COLORS["text_main"],
            bg=COLORS["card_bg"],
            font=FONTS["section_header"],
            anchor="w",
        )
        self.lbl_sec1_title.pack(side=tk.LEFT)

        # Geriye dönük uyumluluk için gizli btn_clear referansı
        self.btn_clear = HoverButton(
            sec1_header,
            normal_bg=COLORS["secondary_bg"],
            hover_bg=COLORS["secondary_hover"],
            normal_fg=COLORS["secondary_fg"],
            text=t("btn_clear"),
            command=self.clear_files,
        )

        # Dosya Seç / Dosya Değiştir Butonu
        self.btn_select = HoverButton(
            sec1_header,
            normal_bg=COLORS["accent_lilac"],
            hover_bg=COLORS["accent_lilac_hover"],
            normal_fg=COLORS["accent_lilac_fg"],
            text=t("btn_select"),
            font=FONTS["button_select"],
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.select_files,
        )
        self.btn_select.pack(side=tk.RIGHT)

        # Tablo Başlık Satırı (Sadece dosya seçildiğinde gösterilir)
        # padx=11 ile altındaki row_card (padx=10 + 1px border = 11px) birebir hizalanır
        self.table_header = tk.Frame(self.sec1_card, bg=COLORS["card_bg"], padx=11)
        self.table_header.columnconfigure(0, weight=1)
        self.table_header.columnconfigure(1, minsize=76)
        self.table_header.columnconfigure(2, minsize=96)
        self.table_header.columnconfigure(3, minsize=86)

        self.lbl_col_input = tk.Label(
            self.table_header,
            text=t("sec_source_sub"),
            fg=COLORS["text_muted"],
            bg=COLORS["card_bg"],
            font=FONTS["table_header"],
            anchor="w",
        )
        self.lbl_col_input.grid(row=0, column=0, sticky="w")

        self.lbl_col_size = tk.Label(
            self.table_header,
            text=t("col_size"),
            fg=COLORS["text_muted"],
            bg=COLORS["card_bg"],
            font=FONTS["table_header"],
            anchor="w",
        )
        self.lbl_col_size.grid(row=0, column=1, sticky="w")

        self.lbl_col_status = tk.Label(
            self.table_header,
            text=t("col_status"),
            fg=COLORS["text_muted"],
            bg=COLORS["card_bg"],
            font=FONTS["table_header"],
            anchor="w",
        )
        self.lbl_col_status.grid(row=0, column=2, sticky="w")

        tk.Frame(self.table_header, bg=COLORS["card_bg"], width=86, height=1).grid(
            row=0, column=3, sticky="e"
        )

        # Dosya Satırları Konteyneri (Sadece dosya seçildiğinde gösterilir)
        self.queue_rows_frame = tk.Frame(self.sec1_card, bg=COLORS["card_bg"])

        # Geriye dönük uyumluluk için file_info_box, lbl_file_name, lbl_file_meta
        self.file_info_box = tk.Frame(self.queue_rows_frame, bg=COLORS["row_bg"])
        self.lbl_file_name = tk.Label(
            self.file_info_box,
            text=t("no_file_selected"),
            fg=COLORS["text_muted"],
            bg=COLORS["row_bg"],
            font=FONTS["file_name"],
        )
        self.lbl_file_meta = tk.Label(
            self.file_info_box,
            text=t("no_file_hint"),
            fg=COLORS["text_light"],
            bg=COLORS["row_bg"],
            font=FONTS["file_meta"],
        )

        # Kesikli Çizgili Dosya Seçme Alanı (Dosya yokken kartı doldurur)
        self.drop_zone = DashedDropZone(
            self.sec1_card,
            text=t("drop_zone_prompt"),
            on_click=self.select_files,
            height=96,
        )
        self.drop_zone.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        # =====================================================================
        # SOL ALT KART: Dönüştürme Ayarları
        # =====================================================================
        sec2_card = tk.Frame(
            left_col,
            bg=COLORS["card_bg"],
            padx=16,
            pady=12,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        sec2_card.grid(row=1, column=0, sticky="ew")

        self.lbl_sec2_title = tk.Label(
            sec2_card,
            text=t("sec_options"),
            fg=COLORS["text_main"],
            bg=COLORS["card_bg"],
            font=FONTS["section_header"],
            anchor="w",
        )
        self.lbl_sec2_title.pack(fill=tk.X, pady=(0, 6))

        tk.Frame(sec2_card, bg=COLORS["border"], height=1).pack(fill=tk.X, pady=(0, 4))

        self.opt_row_pdf = ToggleOptionRow(
            sec2_card,
            variable=self.var_pdf_plain,
            title=t("opt_pdf_plain_title"),
            description=t("opt_pdf_plain_desc"),
            on_change=self._on_option_toggled,
            on_text=t("toggle_on"),
            off_text=t("toggle_off"),
            tooltip_text=t("opt_pdf_plain_tooltip"),
        )
        self.opt_row_pdf.pack(fill=tk.X)

        tk.Frame(sec2_card, bg=COLORS["border_subtle"], height=1).pack(fill=tk.X, pady=2)

        self.opt_row_clean = ToggleOptionRow(
            sec2_card,
            variable=self.var_clean_llm,
            title=t("opt_clean_llm_title"),
            description=t("opt_clean_llm_desc"),
            on_change=self._on_option_toggled,
            on_text=t("toggle_on"),
            off_text=t("toggle_off"),
            tooltip_text=t("opt_clean_llm_tooltip"),
        )
        self.opt_row_clean.pack(fill=tk.X)

        # =====================================================================
        # SAĞ SÜTUN KARTI: Çıktı Özeti (Bento Grid Metrikler + Bilgi Baloncukları)
        # =====================================================================
        self.sec3_card = tk.Frame(
            right_col,
            bg=COLORS["card_bg"],
            padx=16,
            pady=14,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        self.sec3_card.grid(row=0, column=0, sticky="nsew")

        sec3_header_row = tk.Frame(self.sec3_card, bg=COLORS["card_bg"])
        sec3_header_row.pack(fill=tk.X, pady=(0, 12))

        self.lbl_sec3_title = tk.Label(
            sec3_header_row,
            text=t("sec_output"),
            fg=COLORS["text_main"],
            bg=COLORS["card_bg"],
            font=FONTS["section_header"],
            anchor="w",
        )
        self.lbl_sec3_title.pack(side=tk.LEFT)

        # Geriye dönük uyumluluk için görünmez saat ve alt başlık referansları
        self.lbl_timestamp = tk.Label(sec3_header_row, text="")
        self.lbl_sec3_sub = tk.Label(self.sec3_card, text=t("sec_output_sub"))

        # Bento Grid Konteyneri (2 Satır: Üstte Token, Altta Kelime + Karakter)
        bento_frame = tk.Frame(self.sec3_card, bg=COLORS["card_bg"])
        bento_frame.pack(fill=tk.BOTH, expand=True)
        bento_frame.columnconfigure(0, weight=1, uniform="bento")
        bento_frame.columnconfigure(1, weight=1, uniform="bento")
        bento_frame.rowconfigure(0, weight=3)
        bento_frame.rowconfigure(1, weight=2)

        # 1. Üst Kutu: Tahmini Yapay Zeka Tokenı (Tam Genişlik + Bilgi Baloncuğu)
        self.lbl_val_tokens, self.lbl_title_tokens, self.tooltip_tokens = self._create_bento_box(
            bento_frame,
            row=0,
            col=0,
            colspan=2,
            title=t("metric_tokens"),
            tooltip_text=t("metric_tokens_tooltip"),
            initial_val="—",
            val_font=FONTS["metric_val_hero"],
            pady=(0, 10),
        )

        # 2. Alt Sol: Kelime Sayısı (+ Bilgi Baloncuğu)
        self.lbl_val_words, self.lbl_title_words, self.tooltip_words = self._create_bento_box(
            bento_frame,
            row=1,
            col=0,
            colspan=1,
            title=t("metric_words"),
            tooltip_text=t("metric_words_tooltip"),
            initial_val="—",
            val_font=FONTS["metric_val"],
            padx=(0, 5),
            pady=(0, 0),
        )

        # 3. Alt Sağ: Karakter Sayısı (+ Bilgi Baloncuğu)
        self.lbl_val_chars, self.lbl_title_chars, self.tooltip_chars = self._create_bento_box(
            bento_frame,
            row=1,
            col=1,
            colspan=1,
            title=t("metric_chars"),
            tooltip_text=t("metric_chars_tooltip"),
            initial_val="—",
            val_font=FONTS["metric_val"],
            padx=(5, 0),
            pady=(0, 0),
        )

        # Geriye dönük test uyumluluğu için görünmez süre etiketleri
        # (Gerçek çalışma süresi alttaki ilerleme çubuğunda gösterilir)
        self.lbl_val_time = tk.Label(self.sec3_card, text="—")
        self.lbl_title_time = tk.Label(self.sec3_card, text=t("metric_time"))

        self._refresh_file_info_display()

    def _create_bento_box(
        self,
        parent: tk.Frame,
        row: int,
        col: int,
        colspan: int,
        title: str,
        tooltip_text: str,
        initial_val: str,
        val_font: tuple,
        padx: tuple[int, int] = (0, 0),
        pady: tuple[int, int] = (0, 0),
    ) -> tuple[tk.Label, tk.Label, ToolTip]:
        box = tk.Frame(
            parent,
            bg=COLORS["card_subtle"],
            padx=14,
            pady=12,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        box.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=padx, pady=pady)

        header_row = tk.Frame(box, bg=COLORS["card_subtle"])
        header_row.pack(fill=tk.X)

        lbl_title = tk.Label(
            header_row,
            text=title,
            font=FONTS["metric_lbl"],
            fg=COLORS["text_muted"],
            bg=COLORS["card_subtle"],
            anchor="w",
        )
        lbl_title.pack(side=tk.LEFT)

        lbl_info = tk.Label(
            header_row,
            text="ⓘ",
            font=("Segoe UI", 10),
            fg=COLORS["text_light"],
            bg=COLORS["card_subtle"],
            cursor="hand2",
        )
        lbl_info.pack(side=tk.RIGHT)
        tip = ToolTip(lbl_info, tooltip_text)

        lbl_val = tk.Label(
            box,
            text=initial_val,
            font=val_font,
            fg=COLORS["text_main"],
            bg=COLORS["card_subtle"],
            anchor="center",
        )
        lbl_val.pack(fill=tk.BOTH, expand=True, pady=(6, 2))

        return lbl_val, lbl_title, tip

    def _format_elapsed_time(self, ms: int) -> str:
        return f"{ms / 1000:.2f}{t('unit_sec')}" if ms >= 1000 else f"{ms} {t('unit_ms')}"

    def _set_progress_bar(self, pct: int, state_key: str, elapsed_ms: int | None = None) -> None:
        self._progress_pct = pct
        self._progress_state_key = state_key
        self.progress["value"] = pct
        self.dark_progress.set_value(pct)
        if state_key == "progress_finished" and elapsed_ms is not None:
            time_str = self._format_elapsed_time(elapsed_ms)
            self.lbl_progress_pct.config(text=t("progress_finished_time", time=time_str))
        else:
            self.lbl_progress_pct.config(text=t(state_key, pct=pct))

    def _set_step_badge(self, text: str, bg: str, fg: str) -> None:
        self.lbl_step_badge.config(text=text, bg=bg, fg=fg)
        self.badge_container.config(bg=bg)
        self.lbl_badge_dot.config(bg=bg)

    def _set_step_badge_state(self, key: str, bg: str, fg: str) -> None:
        self._badge_state = (key, bg, fg)
        dot_color = COLORS["success"]
        if key == "badge_converting":
            dot_color = COLORS["warning"]
        elif key == "badge_error":
            dot_color = COLORS["danger"]
        self.lbl_badge_dot.config(fg=dot_color)
        self._set_step_badge(t(key), bg, fg)

    def _set_metrics(self, tokens: str = "—", words: str = "—", chars: str = "—", elapsed: str = "—") -> None:
        self.lbl_val_tokens.config(text=tokens)
        self.lbl_val_words.config(text=words)
        self.lbl_val_chars.config(text=chars)
        self.lbl_val_time.config(text=elapsed)

    def _render_metrics(self) -> None:
        """Son metrik verisini aktif dildeki birim ve hata etiketleriyle ekrana yansıtır."""
        data = self._last_metrics
        if not data:
            self._set_metrics()
            return

        mode = data.get("mode")
        if mode == "loading":
            self._set_metrics("...", "...", "...", "...")
        elif mode == "fatal_error":
            self._set_metrics(t("metric_error"), "—", "—", "—")
        elif mode == "single_error":
            ms = int(data.get("ms", 0))
            self._set_metrics(t("metric_error"), "—", "—", f"{ms} {t('unit_ms')}")
        elif mode == "values":
            tokens = int(data.get("tokens", 0))
            words = int(data.get("words", 0))
            chars = int(data.get("chars", 0))
            ms = int(data.get("ms", 0))
            sep = "," if self.current_lang == "en" else "."
            elapsed_str = self._format_elapsed_time(ms)
            self._set_metrics(
                tokens=f"~{tokens:,}".replace(",", sep),
                words=f"{words:,}".replace(",", sep),
                chars=f"{chars:,}".replace(",", sep),
                elapsed=elapsed_str,
            )

    def _refresh_file_info_display(self) -> None:
        """Dosya seçili olmadığında bırakma alanını, dosya seçildiğinde ise tablo satırını gösterir."""
        for child in self.queue_rows_frame.winfo_children():
            if child is not self.file_info_box:
                child.destroy()

        count = len(self.selected_files)
        if count == 0:
            self.table_header.pack_forget()
            self.queue_rows_frame.pack_forget()
            self.drop_zone.set_text(t("drop_zone_prompt"))
            self.drop_zone.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

            self.lbl_file_name.config(text=t("no_file_selected"), fg=COLORS["text_muted"])
            self.lbl_file_meta.config(text=t("no_file_hint"), fg=COLORS["text_light"])
            self.btn_select.config(text=t("btn_select"))
            return

        # Dosya seçildiğinde drop_zone gizlenir; tablo başlığı ve dosya satırı ferahça gösterilir
        self.drop_zone.pack_forget()
        self.table_header.pack(fill=tk.X, pady=(2, 6))
        self.queue_rows_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 2))

        # Geriye dönük uyumluluk için lbl_file_name & lbl_file_meta güncellemesi
        if count == 1:
            p = self.selected_files[0]
            ext = (p.suffix.lstrip(".") or t("file_default_ext")).upper()
            size_str = _format_file_size(p.stat().st_size) if p.exists() else "?"
            folder_str = _truncate_middle(str(p.parent), 52)
            self.lbl_file_name.config(text=_truncate_middle(p.name, 56), fg=COLORS["text_main"])
            self.lbl_file_meta.config(
                text=t("file_meta_single", ext=ext, size=size_str, folder=folder_str),
                fg=COLORS["text_muted"],
            )
        else:
            total_bytes = sum(p.stat().st_size for p in self.selected_files if p.exists())
            names_preview = ", ".join(_truncate_middle(p.name, 24) for p in self.selected_files[:2])
            extra = t("files_selected_extra", count=count - 2) if count > 2 else ""
            self.lbl_file_name.config(
                text=t("files_selected_count", count=count, size=_format_file_size(total_bytes)),
                fg=COLORS["text_main"],
            )
            self.lbl_file_meta.config(
                text=t("files_selected_list", names=names_preview, extra=extra),
                fg=COLORS["text_muted"],
            )

        self.btn_select.config(text=t("btn_change"))

        # Görsel Dosya Satırını Oluştur (table_header ile birebir aynı sütun genişlikleri: 76, 96, 86)
        avail_row_w = self.sec1_card.winfo_width() if hasattr(self, "sec1_card") else 0
        max_name_chars = max(26, (avail_row_w - 340) // 9) if avail_row_w > 400 else 26
        visible_files = self.selected_files[:3]
        for idx, file_path in enumerate(visible_files):
            row_card = tk.Frame(
                self.queue_rows_frame,
                bg=COLORS["row_bg"],
                padx=10,
                pady=10,
                highlightbackground=COLORS["border_subtle"],
                highlightthickness=1,
            )
            row_card.pack(fill=tk.X, pady=(0, 6))
            row_card.columnconfigure(1, weight=1)
            row_card.columnconfigure(2, minsize=76)
            row_card.columnconfigure(3, minsize=96)
            row_card.columnconfigure(4, minsize=86)

            badge_txt, badge_col = _get_file_badge_style(file_path)
            lbl_icon = tk.Label(
                row_card,
                text=badge_txt,
                bg=badge_col,
                fg="#ffffff",
                font=FONTS["file_icon"],
                width=4,
                pady=3,
            )
            lbl_icon.grid(row=0, column=0, padx=(0, 10))

            lbl_name = tk.Label(
                row_card,
                text=_truncate_middle(file_path.name, max_name_chars),
                fg=COLORS["text_main"],
                bg=COLORS["row_bg"],
                font=FONTS["file_name"],
                anchor="w",
            )
            lbl_name.grid(row=0, column=1, sticky="ew", padx=(0, 8))

            f_size = _format_file_size(file_path.stat().st_size) if file_path.exists() else "?"
            lbl_size = tk.Label(
                row_card,
                text=f_size,
                fg=COLORS["text_muted"],
                bg=COLORS["row_bg"],
                font=FONTS["file_meta"],
                anchor="w",
            )
            lbl_size.grid(row=0, column=2, sticky="w")

            st_key = self.file_statuses.get(file_path, "row_ready")
            st_fg = COLORS["text_main"]
            if st_key == "row_done":
                st_fg = COLORS["success"]
            elif st_key == "row_working":
                st_fg = COLORS["warning"]
            elif st_key == "row_error":
                st_fg = COLORS["danger"]

            lbl_st = tk.Label(
                row_card,
                text=t(st_key),
                fg=st_fg,
                bg=COLORS["row_bg"],
                font=FONTS["file_meta"],
                anchor="w",
            )
            lbl_st.grid(row=0, column=3, sticky="w")

            # Açık ve net Sil / Kaldır butonu
            btn_remove = HoverButton(
                row_card,
                normal_bg=COLORS["danger_btn_bg"],
                hover_bg=COLORS["danger_btn_hover"],
                normal_fg=COLORS["danger_btn_fg"],
                border_color=COLORS["danger_btn_border"],
                text=t("btn_remove_file"),
                font=("Segoe UI", 8, "bold"),
                relief="flat",
                padx=10,
                pady=3,
                cursor="hand2",
                command=lambda i=idx: self.remove_file_at(i),
            )
            btn_remove.set_enabled(not self.is_converting)
            btn_remove.grid(row=0, column=4, sticky="e")

        if count == 1:
            p = self.selected_files[0]
            lbl_loc = tk.Label(
                self.queue_rows_frame,
                text=t("file_folder_label", folder=_truncate_middle(str(p.parent), 58)),
                fg=COLORS["text_light"],
                bg=COLORS["card_bg"],
                font=FONTS["option_desc"],
                anchor="w",
                padx=2,
            )
            lbl_loc.pack(fill=tk.X, pady=(2, 0))

    def remove_file_at(self, index: int) -> None:
        """Seçili dosyayı listeden kaldırır ve durumu sıfırlar."""
        if self.is_converting or not (0 <= index < len(self.selected_files)):
            return
        removed = self.selected_files.pop(index)
        self.file_statuses.pop(removed, None)
        if not self.selected_files:
            self.clear_files()
        else:
            self._refresh_file_info_display()

    def clear_files(self) -> None:
        """Seçili dosyayı tamamen temizler ve durumu sıfırlar."""
        if self.is_converting:
            return
        self.selected_files.clear()
        self.file_statuses.clear()
        self.has_converted_current_selection = False
        self.last_output_path = None
        self.last_converted_content = ""
        self._last_metrics = None
        self._convert_btn_key = "btn_convert"
        self.btn_convert.set_palette(COLORS["primary"], COLORS["primary_hover"], "#ffffff")
        self.btn_convert.set_enabled(False, text=t("btn_convert"))
        self._set_action_buttons_enabled(False)
        self._set_progress_bar(0, "progress_idle")
        self._set_step_badge_state("badge_ready", COLORS["step_idle_bg"], COLORS["step_idle_fg"])
        self._set_status_state("status_ready", COLORS["text_muted"])
        self._render_metrics()
        self._refresh_file_info_display()

    def _on_language_selected(self, _event: tk.Event) -> None:
        self.cmb_language.selection_clear()
        selected_label = self.cmb_language.get()
        lang_code = next(
            (code for code, label in LANGUAGES.items() if label == selected_label),
            "tr",
        )
        self.apply_language(lang_code)

    def apply_language(self, lang_code: str) -> None:
        """Seçilen dili kaydeder ve pencere boyutunu değiştirmeden tüm metinleri anında günceller."""
        self.current_lang = save_language(lang_code)
        self.cmb_language.set(LANGUAGES.get(self.current_lang, LANGUAGES["tr"]))

        self.root.title(t("window_title"))
        self.lbl_title.config(text=t("app_title"))
        self.lbl_lang_caption.config(text=t("lbl_language"))

        self.lbl_sec1_title.config(text=t("sec_source_file"))
        self.lbl_col_input.config(text=t("sec_source_sub"))
        self.lbl_col_size.config(text=t("col_size"))
        self.lbl_col_status.config(text=t("col_status"))
        self.btn_clear.config(text=t("btn_clear"))

        self.lbl_sec2_title.config(text=t("sec_options"))
        self.lbl_sec3_title.config(text=t("sec_output"))
        self.lbl_sec3_sub.config(text=t("sec_output_sub"))

        self._refresh_file_info_display()

        self.opt_row_pdf.update_texts(
            t("opt_pdf_plain_title"),
            t("opt_pdf_plain_desc"),
            t("toggle_on"),
            t("toggle_off"),
            t("opt_pdf_plain_tooltip"),
        )
        self.opt_row_clean.update_texts(
            t("opt_clean_llm_title"),
            t("opt_clean_llm_desc"),
            t("toggle_on"),
            t("toggle_off"),
            t("opt_clean_llm_tooltip"),
        )

        self.btn_convert.config(text=t(self._convert_btn_key))

        badge_key, badge_bg, badge_fg = self._badge_state
        self._set_step_badge_state(badge_key, badge_bg, badge_fg)

        elapsed_ms = (
            int(self._last_metrics["ms"])
            if self._last_metrics and self._last_metrics.get("mode") == "values"
            else None
        )
        self._set_progress_bar(self._progress_pct, self._progress_state_key, elapsed_ms)
        self.tooltip_progress.set_text(t("progress_tooltip"))

        status_key, status_kwargs, status_fg = self._status_state
        self._set_status(t(status_key, **status_kwargs), status_fg)

        self.lbl_title_tokens.config(text=t("metric_tokens"))
        self.tooltip_tokens.set_text(t("metric_tokens_tooltip"))
        self.lbl_title_words.config(text=t("metric_words"))
        self.tooltip_words.set_text(t("metric_words_tooltip"))
        self.lbl_title_chars.config(text=t("metric_chars"))
        self.tooltip_chars.set_text(t("metric_chars_tooltip"))
        self.lbl_title_time.config(text=t("metric_time"))
        self._render_metrics()

        copy_key = "btn_copied" if self._copy_feedback_active else "btn_copy"
        self.btn_copy_md.config(text=t(copy_key))
        self.btn_open_md.config(text=t("btn_open"))
        self.btn_reveal_folder.config(text=t("btn_reveal"))

        self._ensure_window_fits_content()
        logger.info("Uygulama dili güncellendi: %s", self.current_lang)

    def _on_option_toggled(self) -> None:
        logger.info(
            "Kullanıcı dönüştürme seçeneğini değiştirdi -> pdf_plain=%s, clean_llm=%s",
            self.var_pdf_plain.get(),
            self.var_clean_llm.get(),
        )
        print(
            f"[UI-OPTION] Ayar güncellendi: pdf_plain={self.var_pdf_plain.get()}, "
            f"clean_llm={self.var_clean_llm.get()}"
        )
        if self.selected_files and not self.is_converting and self.has_converted_current_selection:
            self._convert_btn_key = "btn_convert"
            self.btn_convert.set_palette(COLORS["primary"], COLORS["primary_hover"], "#ffffff")
            self.btn_convert.set_enabled(True, text=t("btn_convert"))
            self._set_step_badge_state(
                "badge_ready",
                COLORS["step_ready_bg"],
                COLORS["step_ready_fg"],
            )
            self._set_status_state(
                "status_options_updated",
                COLORS["accent_lilac"],
            )

    def _set_status(self, text: str, fg: str) -> None:
        prefix = "✔  " if fg == COLORS["success"] and not text.startswith("✔") else ""
        self.lbl_status.config(text=f"{prefix}{text}", fg=fg)

    def _set_status_state(self, key: str, fg: str, **kwargs: Any) -> None:
        self._status_state = (key, kwargs, fg)
        self._set_status(t(key, **kwargs), fg)

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        self._copy_feedback_active = False
        self.btn_copy_md.set_palette(COLORS["action_bg"], COLORS["action_hover"], COLORS["action_fg"])
        self.btn_copy_md.set_enabled(enabled, text=t("btn_copy"))
        self.btn_open_md.set_enabled(enabled)
        self.btn_reveal_folder.set_enabled(enabled)

    def select_files(self) -> None:
        """Kullanıcının dönüştürülecek tek bir dosyayı seçmesini veya değiştirmesini sağlar."""
        if self.is_converting:
            logger.debug("Dönüştürme sürerken dosya seçimi engellendi.")
            return

        logger.info("Dosya seçim penceresi açılıyor...")
        filepath = filedialog.askopenfilename(
            title=t("dialog_select_title"),
            filetypes=get_supported_filetypes(),
        )
        if not filepath:
            logger.info("Kullanıcı dosya seçimini iptal etti.")
            return

        selected_path = Path(filepath)
        self.selected_files = [selected_path]
        self.file_statuses = {selected_path: "row_ready"}
        self.has_converted_current_selection = False
        logger.info("Dosya seçildi: %s", selected_path.name)
        print(f"[UI-SELECT] Dosya seçildi: {selected_path.name}")

        self._refresh_file_info_display()
        self.file_info_box.config(highlightbackground=COLORS["border_active"])
        self._convert_btn_key = "btn_convert"
        self.btn_convert.set_palette(COLORS["primary"], COLORS["primary_hover"], "#ffffff")
        self.btn_convert.set_enabled(True, text=t("btn_convert"))
        self._set_progress_bar(0, "progress_idle")
        self._set_step_badge_state(
            "badge_ready",
            COLORS["step_ready_bg"],
            COLORS["step_ready_fg"],
        )
        self._set_status_state("status_ready", COLORS["text_muted"])
        self._last_metrics = None
        self._render_metrics()
        self._ensure_window_fits_content()

    # Geriye dönük uyumluluk için tekil metod adı
    select_file = select_files

    def start_conversion_thread(self) -> None:
        """Arka plan dönüştürme iş parçacığını başlatır."""
        if self.is_converting or not self.selected_files:
            return

        missing_files = [p for p in self.selected_files if not p.exists()]
        if missing_files:
            short_missing = _truncate_middle(missing_files[0].name, 45)
            logger.warning("Eksik dosya: %s", missing_files[0])
            self._set_step_badge_state("badge_error", COLORS["step_error_bg"], COLORS["step_error_fg"])
            self._set_status_state("status_file_missing", COLORS["danger"], name=short_missing)
            return

        options = ConversionOptions(
            pdf_plain_text=bool(self.var_pdf_plain.get()),
            clean_for_llm=bool(self.var_clean_llm.get()),
        )

        self.is_converting = True
        self.conversion_run_count += 1
        self.btn_select.set_enabled(False)
        self.btn_clear.set_enabled(False)
        self._convert_btn_key = "btn_converting"
        self.btn_convert.config(
            state=tk.DISABLED,
            text=t("btn_converting"),
            bg=COLORS["primary_disabled"],
            cursor="arrow",
        )
        self._set_action_buttons_enabled(False)
        self._set_progress_bar(5, "progress_running")
        self._set_step_badge_state(
            "badge_converting",
            COLORS["step_working_bg"],
            COLORS["step_working_fg"],
        )
        self._set_status_state(
            "status_converting",
            COLORS["warning"],
        )
        self._last_metrics = {"mode": "loading"}
        self._render_metrics()
        self._refresh_file_info_display()

        files_copy = list(self.selected_files)
        logger.info(
            "Dönüştürme worker thread başlatılıyor (Tur #%d, %d dosya)...",
            self.conversion_run_count,
            len(files_copy),
        )
        threading.Thread(
            target=self._run_conversion_worker,
            args=(files_copy, options),
            name=f"ConversionWorker-{self.conversion_run_count}",
            daemon=True,
        ).start()

    def _run_conversion_worker(self, files: list[Path], options: ConversionOptions) -> None:
        """Arka plan iş parçacığında paket kontrolü ve dosya dönüşümü yapar."""
        try:
            missing_pkgs = find_missing_packages()
            if missing_pkgs:
                self.root.after(
                    0,
                    self._set_status_state,
                    "status_installing_deps",
                    COLORS["warning"],
                )
                ok, err_detail = install_packages(missing_pkgs)
                if not ok:
                    raise RuntimeError(
                        t(
                            "err_pip_install_failed",
                            packages=", ".join(missing_pkgs),
                            detail=err_detail,
                        )
                    )

            total = len(files)
            results: list[ConversionResult] = []
            for idx, file_path in enumerate(files, start=1):
                short_name = _truncate_middle(file_path.name, 48)
                self.file_statuses[file_path] = "row_working"
                self.root.after(
                    0,
                    self._on_worker_progress,
                    idx - 1,
                    total,
                    "status_converting_file",
                    {"name": short_name},
                )
                res = self.converter_service.convert_file(file_path, options)
                self.file_statuses[file_path] = "row_done" if res.success else "row_error"
                results.append(res)
                self.root.after(
                    0,
                    self._on_worker_progress,
                    idx,
                    total,
                    "status_completed_file",
                    {"name": short_name},
                )

            self.root.after(0, self._on_batch_complete, results)
        except Exception as exc:
            log_exception("_run_conversion_worker", exc)
            err_msg = str(exc).strip() or t("err_unknown_conversion")
            self.root.after(
                0,
                self._on_fatal_worker_error,
                err_msg[:140],
            )

    def _on_worker_progress(
        self, completed: int, total: int, status_key: str, status_kwargs: dict[str, Any]
    ) -> None:
        pct = max(10, int((completed / max(1, total)) * 100))
        self._set_progress_bar(pct, "progress_running")
        self._set_status_state(status_key, COLORS["warning"], **status_kwargs)
        self._refresh_file_info_display()

    def _on_fatal_worker_error(self, error_detail: str) -> None:
        self.is_converting = False
        self.btn_select.set_enabled(True)
        self.btn_clear.set_enabled(True)
        self._convert_btn_key = "btn_reconvert"
        self.btn_convert.set_palette(COLORS["primary"], COLORS["primary_hover"], "#ffffff")
        self.btn_convert.set_enabled(True, text=t("btn_reconvert"))
        self._set_progress_bar(0, "progress_failed")
        self._set_step_badge_state("badge_error", COLORS["step_error_bg"], COLORS["step_error_fg"])
        self._set_status_state("status_error_prefix", COLORS["danger"], error=error_detail)
        self._last_metrics = {"mode": "fatal_error"}
        self._render_metrics()
        self._refresh_file_info_display()
        self._ensure_window_fits_content()

    def _on_batch_complete(self, results: list[ConversionResult]) -> None:
        self.is_converting = False
        self.has_converted_current_selection = True
        self.btn_select.set_enabled(True)
        self.btn_clear.set_enabled(True)

        now_time = datetime.now().strftime("%H:%M:%S")
        self.lbl_timestamp.config(
            text=now_time,
            fg=COLORS["success"],
        )

        succeeded = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_tokens = sum(r.token_count for r in succeeded)
        total_words = sum(r.word_count for r in succeeded)
        total_chars = sum(r.char_count for r in succeeded)
        total_ms = sum(r.elapsed_ms for r in results)

        if succeeded:
            self._set_progress_bar(100, "progress_finished", elapsed_ms=total_ms)
            last_ok = succeeded[-1]
            self.last_output_path = last_ok.output_path
            if len(succeeded) == 1:
                self.last_converted_content = last_ok.content
            else:
                combined_parts = [
                    f"{t('combined_file_header', name=r.source_path.name)}\n{r.content}"
                    for r in succeeded
                ]
                self.last_converted_content = "\n\n---\n\n".join(combined_parts)

            self._set_action_buttons_enabled(True)
            self._convert_btn_key = "btn_reconvert"
            self.btn_convert.set_palette(COLORS["reconvert_bg"], COLORS["reconvert_hover"], "#ffffff")
            self.btn_convert.set_enabled(True, text=t("btn_reconvert"))
            self._set_step_badge_state(
                "badge_done",
                COLORS["step_done_bg"],
                COLORS["step_done_fg"],
            )
            self.sec3_card.config(highlightbackground=COLORS["border_active"], highlightthickness=1)
            self.root.after(
                1200,
                lambda: self.sec3_card.config(highlightbackground=COLORS["border"], highlightthickness=1),
            )
        else:
            self._set_progress_bar(0, "progress_failed")
            self.last_output_path = None
            self.last_converted_content = ""
            self._set_action_buttons_enabled(False)
            self._convert_btn_key = "btn_reconvert"
            self.btn_convert.set_palette(COLORS["primary"], COLORS["primary_hover"], "#ffffff")
            self.btn_convert.set_enabled(True, text=t("btn_reconvert"))
            self._set_step_badge_state("badge_error", COLORS["step_error_bg"], COLORS["step_error_fg"])

        if len(results) == 1:
            r = results[0]
            if r.success and r.output_path is not None:
                short_out = _truncate_middle(r.output_path.name, 48)
                self._set_status_state("status_saved_file", COLORS["success"], name=short_out)
                self._last_metrics = {
                    "mode": "values",
                    "tokens": r.token_count,
                    "words": r.word_count,
                    "chars": r.char_count,
                    "ms": r.elapsed_ms,
                }
            else:
                self._set_status_state(
                    "status_error_prefix",
                    COLORS["danger"],
                    error=r.error_message[:100],
                )
                self._last_metrics = {"mode": "single_error", "ms": r.elapsed_ms}
            self._render_metrics()
        else:
            if not failed:
                self._set_status_state(
                    "status_saved_count", COLORS["success"], count=len(succeeded)
                )
            elif succeeded:
                self._set_status_state(
                    "status_partial",
                    COLORS["warning"],
                    succeeded=len(succeeded),
                    failed=len(failed),
                )
            else:
                self._set_status_state(
                    "status_error_prefix",
                    COLORS["danger"],
                    error=failed[0].error_message[:90],
                )

            if succeeded:
                self._last_metrics = {
                    "mode": "values",
                    "tokens": total_tokens,
                    "words": total_words,
                    "chars": total_chars,
                    "ms": total_ms,
                }
            else:
                self._last_metrics = {"mode": "single_error", "ms": total_ms}
            self._render_metrics()

        self._refresh_file_info_display()
        self._ensure_window_fits_content()
        log_file = get_session_log_path()
        logger.info(
            "Dönüştürme turu #%d tamamlandı -> Başarılı: %d, Hatalı: %d, Toplam Token: ~%d, Log: %s",
            self.conversion_run_count,
            len(succeeded),
            len(failed),
            total_tokens,
            log_file.name if log_file else "YOK",
        )

    def copy_to_clipboard(self) -> None:
        """Son dönüştürülen Markdown metnini doğrudan panoya kopyalar."""
        if not self.last_converted_content:
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_converted_content)
            self.root.update()
            self._copy_feedback_active = True
            self.btn_copy_md.set_palette(
                COLORS["action_success_bg"],
                COLORS["action_success_bg"],
                COLORS["action_success_fg"],
            )
            self.btn_copy_md.config(text=t("btn_copied"))
            logger.info(
                "Markdown içeriği panoya kopyalandı (%d karakter).",
                len(self.last_converted_content),
            )
            print(f"[ACTION] Panoya kopyalandı ({len(self.last_converted_content)} karakter).")

            def _restore_copy_btn() -> None:
                self._copy_feedback_active = False
                if not self.is_converting and self.last_converted_content:
                    self.btn_copy_md.set_palette(
                        COLORS["action_bg"],
                        COLORS["action_hover"],
                        COLORS["action_fg"],
                    )
                    self.btn_copy_md.config(text=t("btn_copy"))

            self.root.after(1800, _restore_copy_btn)
        except Exception as exc:
            log_exception("copy_to_clipboard", exc)

    def open_output_file(self) -> None:
        """Son oluşturulan .md dosyasını varsayılan metin düzenleyicide açar."""
        if not self.last_output_path or not self.last_output_path.exists():
            return
        try:
            logger.info("Çıktı dosyası açılıyor: %s", self.last_output_path)
            print(f"[ACTION] Dosya açılıyor: {self.last_output_path}")
            if os.name == "nt":
                os.startfile(str(self.last_output_path))
        except Exception as exc:
            log_exception("open_output_file", exc)

    def reveal_in_explorer(self) -> None:
        """Son oluşturulan .md dosyasını Windows Gezgini içinde seçili olarak gösterir."""
        if not self.last_output_path or not self.last_output_path.exists():
            return
        try:
            logger.info("Klasörde gösteriliyor: %s", self.last_output_path)
            print(f"[ACTION] Klasörde gösteriliyor: {self.last_output_path}")
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", str(self.last_output_path)])
        except Exception as exc:
            log_exception("reveal_in_explorer", exc)


# Geriye dönük sınıf ismi uyumluluğu
MarkItDownQuickApp = MainWindow
