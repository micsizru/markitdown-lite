"""Çoklu dil desteği (TR / EN / RU) ve kalıcı dil ayarı yönetimi modülü."""

import json
from pathlib import Path
from typing import Any

from app.config import BASE_DIR, FILETYPE_PATTERNS
from app.logger import get_logger

logger = get_logger("i18n")

SETTINGS_FILE: Path = BASE_DIR / "settings.json"
DEFAULT_LANGUAGE: str = "tr"

LANGUAGES: dict[str, str] = {
    "tr": "Türkçe",
    "en": "English",
    "ru": "Русский",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "tr": {
        "app_title": "MarkItDown",
        "window_title": "MarkItDown - Masaüstü Belge Dönüştürücü v2.0",
        "err_startup_title": "Başlatma Hatası",
        "menu_file": "Dosya",
        "menu_view": "Görünüm",
        "menu_tools": "Araçlar",
        "menu_help": "Yardım",
        "lbl_language": "Dil",
        "sec_source_file": "Kaynak Dosya",
        "sec_source_sub": "Dosya Adı",
        "col_size": "Boyut",
        "col_status": "Durum",
        "sec_options": "Dönüştürme Ayarları",
        "sec_output": "Çıktı Özeti",
        "sec_output_sub": "Dönüştürülen Belge İstatistikleri",
        "no_file_selected": "Henüz dosya seçilmedi",
        "no_file_hint": "Dosya seçmek için buraya tıklayın",
        "drop_zone_prompt": "Dosya seçmek için buraya tıklayın\n(PDF, Word, Excel, PowerPoint, HTML, CSV, ZIP)",
        "drop_zone_change_prompt": "Farklı bir dosya ile değiştirmek için buraya tıklayın",
        "file_meta_single": "Tür: {ext}   •   Boyut: {size}   •   Klasör: {folder}",
        "file_folder_label": "Konum: {folder}",
        "file_default_ext": "Dosya",
        "files_selected_count": "{count} Dosya Seçildi ({size})",
        "files_selected_extra": " (+{count} diğer)",
        "files_selected_list": "Seçilenler: {names}{extra}",
        "btn_select": "Dosya Seç",
        "btn_change": "Dosya Değiştir",
        "btn_clear": "Temizle",
        "btn_remove_file": "✕ Sil",
        "opt_pdf_plain_title": "Saf Metin Modu (PDF)",
        "opt_pdf_plain_desc": "PDF'lerde tablo algılamayı kapatır ve metni düz akış olarak çıkarır",
        "opt_pdf_plain_tooltip": (
            "PDF'lerdeki tablo çizgilerini ve sütun ızgaralarını çözmeye çalışmak yerine "
            "metni doğrudan düz yazı akışı olarak çıkarır.\n\n"
            "Hangi durumlarda açılması tavsiye edilir:\n"
            "• İki sütunlu akademik makaleler, ders notları, kitaplar ve raporlarda "
            "(bozuk tablo oluşumunu ve %60'a varan gereksiz token israfını önler).\n\n"
            "Hangi durumlarda kapatılması tavsiye edilir:\n"
            "• İçinde gerçekten korunması gereken fiyat listesi, finansal tablo veya "
            "veri çizelgesi bulunan PDF'lerde."
        ),
        "opt_clean_llm_title": "Gelişmiş Metin Temizliği",
        "opt_clean_llm_desc": "Bozuk font kodlarını (cid:...), satır sonu tirelerini ve fazla boşlukları temizler",
        "opt_clean_llm_tooltip": (
            "Dönüştürülen metindeki okunamayan font kalıntılarını (ör. cid:123), "
            "satır sonu tire bölünmelerini ve gereksiz boş satırları temizler.\n\n"
            "Hangi durumlarda açılması tavsiye edilir:\n"
            "• Çıktıyı ChatGPT, Claude veya Gemini gibi yapay zeka modellerine "
            "vereceğiniz her durumda (metin kalitesini artırır ve token tasarrufu sağlar).\n\n"
            "Hangi durumlarda kapatılması tavsiye edilir:\n"
            "• Belgedeki ham boşluk yapısına ve orijinal satır kırılımlarına "
            "birebir sadık kalınması gerektiğinde."
        ),
        "toggle_on": "✓ Açık",
        "toggle_off": "Kapalı",
        "btn_convert": "▷  Dönüştür",
        "btn_reconvert": "▷  Tekrar Dönüştür",
        "btn_converting": "⏳  Dönüştürülüyor...",
        "badge_ready": "Hazır",
        "badge_converting": "İşleniyor...",
        "badge_done": "Tamamlandı",
        "badge_error": "Hata",
        "row_ready": "Hazır",
        "row_working": "İşleniyor...",
        "row_done": "Tamamlandı ✓",
        "row_error": "Hata",
        "progress_idle": "0% / Hazır",
        "progress_running": "{pct}% / İşleniyor",
        "progress_finished": "100% / Tamamlandı",
        "progress_finished_time": "100% / Tamamlandı ({time})",
        "progress_failed": "0% / Hata",
        "progress_tooltip": (
            "Dönüştürme işleminin ilerleme durumunu ve işlemin tamamlanması için "
            "geçen toplam çalışma (execute) süresini gösterir."
        ),
        "status_ready": "Dönüştürmeye hazır",
        "status_options_updated": "Ayarlar güncellendi — tekrar dönüştürebilirsiniz",
        "status_converting": "Dönüştürülüyor...",
        "status_installing_deps": "Eksik kütüphaneler kuruluyor...",
        "status_converting_file": "Dönüştürülüyor: {name}",
        "status_completed_file": "Tamamlandı: {name}",
        "status_saved_file": "Kaydedildi: {name}",
        "status_saved_count": "Kaydedildi: {count} dosya",
        "status_partial": "Kısmen Tamamlandı: {succeeded} başarılı, {failed} hatalı",
        "status_file_missing": "Hata: '{name}' artık mevcut değil!",
        "status_error_prefix": "Hata: {error}",
        "metric_tokens": "Tahmini Yapay Zeka Tokenı",
        "metric_tokens_tooltip": (
            "Üretilen Markdown metninin ChatGPT, Claude veya Gemini gibi yapay zeka (LLM) "
            "modellerinde kaplayacağı yaklaşık token miktarıdır (1 token ≈ 4 karakter).\n\n"
            "Ne işe yarar?\n"
            "• Yapay zeka modellerinin tek seferde okuyabileceği bir bağlam sınırı (context limit) vardır.\n"
            "• Bu sayı sayesinde belgenin modele sığıp sığmayacağını ve ne kadar kota harcayacağını önceden görürsünüz."
        ),
        "metric_words": "Kelime Sayısı",
        "metric_words_tooltip": (
            "Dönüştürme sonucunda oluşan Markdown belgesinin içerdiği toplam kelime sayısıdır.\n\n"
            "Belgenin metin yoğunluğunu ve eksiksiz çıkarılıp çıkarılmadığını kontrol etmenizi sağlar."
        ),
        "metric_chars": "Karakter Sayısı",
        "metric_chars_tooltip": (
            "Boşluklar, noktalama işaretleri ve Markdown biçimlendirme karakterleri dahil "
            "üretilen toplam metin uzunluğudur."
        ),
        "metric_time": "İşlem Süresi",
        "metric_error": "Hata",
        "unit_sec": "sn",
        "unit_ms": "ms",
        "btn_copy": "📋  Panoya Kopyala",
        "btn_copied": "✔  Kopyalandı",
        "btn_open": "↗  Dosyayı Aç",
        "btn_reveal": "📁  Klasörde Göster",
        "dialog_select_title": "Dönüştürülecek Dosyayı Seçin",
        "filetype_supported": "Desteklenen Dosyalar",
        "filetype_pdf": "PDF Dosyaları",
        "filetype_office": "Office Belgeleri",
        "filetype_web_data": "Web ve Veri Dosyaları",
        "filetype_all": "Tüm Dosyalar",
        "combined_file_header": "<!-- Dosya: {name} -->",
        "err_file_not_found": "Seçilen dosya bulunamadı: {name}",
        "err_pdf_no_text_layer": "Dosyadan metin çıkarılamadı (Görsel/taranmış PDF, metin katmanı yok).",
        "err_no_text_extracted": "Dosyadan metin çıkarılamadı (Görsel/taranmış PDF veya boş dosya olabilir).",
        "err_unknown_conversion": "Bilinmeyen dönüştürme hatası.",
        "err_missing_dependency": "Bu dosya türü için gerekli alt kütüphane eksik. Lütfen uygulamayı run.bat ile yeniden başlatın.",
        "err_pip_install_failed": "Gerekli kütüphaneler kurulamadı ({packages}): {detail}",
    },
    "en": {
        "app_title": "MarkItDown",
        "window_title": "MarkItDown - Desktop Document Converter v2.0",
        "err_startup_title": "Startup Error",
        "menu_file": "File",
        "menu_view": "View",
        "menu_tools": "Tools",
        "menu_help": "Help",
        "lbl_language": "Language",
        "sec_source_file": "Source File",
        "sec_source_sub": "File Name",
        "col_size": "Size",
        "col_status": "Status",
        "sec_options": "Conversion Settings",
        "sec_output": "Output Summary",
        "sec_output_sub": "Converted Document Statistics",
        "no_file_selected": "No file selected yet",
        "no_file_hint": "Click here to browse for a file",
        "drop_zone_prompt": "Click here to select a file\n(PDF, Word, Excel, PowerPoint, HTML, CSV, ZIP)",
        "drop_zone_change_prompt": "Click here to replace with a different file",
        "file_meta_single": "Type: {ext}   •   Size: {size}   •   Folder: {folder}",
        "file_folder_label": "Location: {folder}",
        "file_default_ext": "File",
        "files_selected_count": "{count} Files Selected ({size})",
        "files_selected_extra": " (+{count} more)",
        "files_selected_list": "Selected: {names}{extra}",
        "btn_select": "Select File",
        "btn_change": "Change File",
        "btn_clear": "Clear",
        "btn_remove_file": "✕ Remove",
        "opt_pdf_plain_title": "Plain Text Mode (PDF)",
        "opt_pdf_plain_desc": "Disables table parser in PDFs and extracts content as a clean text stream",
        "opt_pdf_plain_tooltip": (
            "Extracts PDF text directly as a continuous stream instead of trying to reconstruct "
            "table borders and multi-column grids.\n\n"
            "When it is recommended to enable:\n"
            "• Two-column academic papers, lecture notes, books, and text-heavy PDFs "
            "(prevents broken Markdown tables and up to 60% token waste).\n\n"
            "When it is recommended to disable:\n"
            "• PDFs containing actual data tables, price lists, or financial schedules "
            "where table structure must be preserved."
        ),
        "opt_clean_llm_title": "Advanced Text Cleanup",
        "opt_clean_llm_desc": "Removes broken font codes (cid:...), line-break hyphens, and extra blank lines",
        "opt_clean_llm_tooltip": (
            "Cleans unreadable font artifacts (e.g. cid:123), fixes hyphenated word breaks at line ends, "
            "and compacts excessive empty lines.\n\n"
            "When it is recommended to enable:\n"
            "• Whenever you plan to feed the output into AI models like ChatGPT, Claude, or Gemini "
            "(improves text quality and reduces token usage).\n\n"
            "When it is recommended to disable:\n"
            "• When you need strict 1:1 preservation of raw spacing and original line breaks."
        ),
        "toggle_on": "✓ On",
        "toggle_off": "Off",
        "btn_convert": "▷  Convert",
        "btn_reconvert": "▷  Convert Again",
        "btn_converting": "⏳  Converting...",
        "badge_ready": "Ready",
        "badge_converting": "Processing...",
        "badge_done": "Completed",
        "badge_error": "Error",
        "row_ready": "Ready",
        "row_working": "Running...",
        "row_done": "Done ✓",
        "row_error": "Failed",
        "progress_idle": "0% / Ready",
        "progress_running": "{pct}% / Running",
        "progress_finished": "100% / Finished",
        "progress_finished_time": "100% / Finished ({time})",
        "progress_failed": "0% / Failed",
        "progress_tooltip": (
            "Shows the current conversion progress and the total execution time "
            "taken to convert and save the document."
        ),
        "status_ready": "Ready to convert",
        "status_options_updated": "Settings updated — ready to reconvert",
        "status_converting": "Converting...",
        "status_installing_deps": "Installing missing libraries...",
        "status_converting_file": "Converting: {name}",
        "status_completed_file": "Completed: {name}",
        "status_saved_file": "Saved: {name}",
        "status_saved_count": "Saved: {count} files",
        "status_partial": "Partially Completed: {succeeded} succeeded, {failed} failed",
        "status_file_missing": "Error: '{name}' no longer exists!",
        "status_error_prefix": "Error: {error}",
        "metric_tokens": "Est. AI Tokens",
        "metric_tokens_tooltip": (
            "Estimated number of tokens the generated Markdown text will consume in AI (LLM) "
            "models such as ChatGPT, Claude, or Gemini (1 token ≈ 4 characters).\n\n"
            "Why does it matter?\n"
            "• Every AI model has a maximum context window limit.\n"
            "• This estimate helps you verify whether the document fits in a prompt and how much quota it uses."
        ),
        "metric_words": "Word Count",
        "metric_words_tooltip": (
            "Total number of words in the generated Markdown output.\n\n"
            "Helps you quickly verify document length and text extraction completeness."
        ),
        "metric_chars": "Character Count",
        "metric_chars_tooltip": (
            "Total character length of the generated output, including spaces, "
            "punctuation, and Markdown formatting syntax."
        ),
        "metric_time": "Execution Time",
        "metric_error": "Error",
        "unit_sec": "s",
        "unit_ms": "ms",
        "btn_copy": "📋  Copy to Clipboard",
        "btn_copied": "✔  Copied",
        "btn_open": "↗  Open File",
        "btn_reveal": "📁  Show in Folder",
        "dialog_select_title": "Select File to Convert",
        "filetype_supported": "Supported Files",
        "filetype_pdf": "PDF Files",
        "filetype_office": "Office Documents",
        "filetype_web_data": "Web & Data Files",
        "filetype_all": "All Files",
        "combined_file_header": "<!-- File: {name} -->",
        "err_file_not_found": "Selected file not found: {name}",
        "err_pdf_no_text_layer": "Could not extract text from file (Image/scanned PDF, no text layer).",
        "err_no_text_extracted": "Could not extract text from file (May be an image/scanned PDF or empty file).",
        "err_unknown_conversion": "Unknown conversion error.",
        "err_missing_dependency": "Required sub-library for this file type is missing. Please restart the application via run.bat.",
        "err_pip_install_failed": "Failed to install required libraries ({packages}): {detail}",
    },
    "ru": {
        "app_title": "MarkItDown",
        "window_title": "MarkItDown - Конвертер документов v2.0",
        "err_startup_title": "Ошибка запуска",
        "menu_file": "Файл",
        "menu_view": "Вид",
        "menu_tools": "Инструменты",
        "menu_help": "Справка",
        "lbl_language": "Язык",
        "sec_source_file": "Исходный файл",
        "sec_source_sub": "Имя файла",
        "col_size": "Размер",
        "col_status": "Статус",
        "sec_options": "Настройки конвертации",
        "sec_output": "Сводка документа",
        "sec_output_sub": "Статистика полученного текста",
        "no_file_selected": "Файл ещё не выбран",
        "no_file_hint": "Нажмите здесь для выбора файла",
        "drop_zone_prompt": "Нажмите здесь для выбора файла\n(PDF, Word, Excel, PowerPoint, HTML, CSV, ZIP)",
        "drop_zone_change_prompt": "Нажмите здесь, чтобы выбрать другой файл",
        "file_meta_single": "Тип: {ext}   •   Размер: {size}   •   Папка: {folder}",
        "file_folder_label": "Папка: {folder}",
        "file_default_ext": "Файл",
        "files_selected_count": "Выбрано файлов: {count} ({size})",
        "files_selected_extra": " (+ещё {count})",
        "files_selected_list": "Выбраны: {names}{extra}",
        "btn_select": "Выбрать файл",
        "btn_change": "Изменить файл",
        "btn_clear": "Очистить",
        "btn_remove_file": "✕ Удалить",
        "opt_pdf_plain_title": "Режим чистого текста (PDF)",
        "opt_pdf_plain_desc": "Извлекает текст потоком, отключая разбор таблиц в PDF",
        "opt_pdf_plain_tooltip": (
            "Извлекает текст из PDF напрямую сплошным потоком, не пытаясь строить таблицы "
            "из колонок и рамок.\n\n"
            "В каких случаях рекомендуется включать:\n"
            "• Двухколоночные научные статьи, конспекты, книги и текстовые PDF "
            "(предотвращает поломку разметки и экономит до 60% токенов).\n\n"
            "В каких случаях рекомендуется отключать:\n"
            "• PDF-файлы с реальными таблицами данных, прайс-листами или отчётами, "
            "где важно сохранить структуру ячеек."
        ),
        "opt_clean_llm_title": "Глубокая очистка текста",
        "opt_clean_llm_desc": "Удаляет артефакты шрифтов (cid:...), переносы и лишние пробелы",
        "opt_clean_llm_tooltip": (
            "Удаляет нечитаемые коды шрифтов (например, cid:123), склеивает переносы слов "
            "и убирает лишние пустые строки.\n\n"
            "В каких случаях рекомендуется включать:\n"
            "• Во всех случаях, когда текст передаётся в ИИ-модели (ChatGPT, Claude, Gemini) — "
            "это повышает чистоту текста и экономит токены.\n\n"
            "В каких случаях рекомендуется отключать:\n"
            "• Когда требуется сохранить исходные отступы и переносы строк без изменений."
        ),
        "toggle_on": "✓ Вкл",
        "toggle_off": "Выкл",
        "btn_convert": "▷  Конвертировать",
        "btn_reconvert": "▷  Повторить",
        "btn_converting": "⏳  Конвертация...",
        "badge_ready": "Готов",
        "badge_converting": "Обработка...",
        "badge_done": "Завершено",
        "badge_error": "Ошибка",
        "row_ready": "Готов",
        "row_working": "В работе...",
        "row_done": "Готово ✓",
        "row_error": "Сбой",
        "progress_idle": "0% / Готов",
        "progress_running": "{pct}% / В работе",
        "progress_finished": "100% / Завершено",
        "progress_finished_time": "100% / Завершено ({time})",
        "progress_failed": "0% / Ошибка",
        "progress_tooltip": (
            "Показывает прогресс конвертации и общее время выполнения (execute time), "
            "затраченное на обработку и сохранение файла."
        ),
        "status_ready": "Готов к конвертации",
        "status_options_updated": "Настройки обновлены — можно повторить",
        "status_converting": "Конвертация...",
        "status_installing_deps": "Установка недостающих библиотек...",
        "status_converting_file": "Конвертация: {name}",
        "status_completed_file": "Готово: {name}",
        "status_saved_file": "Сохранено: {name}",
        "status_saved_count": "Сохранено файлов: {count}",
        "status_partial": "Частично завершено: успешно {succeeded}, ошибок {failed}",
        "status_file_missing": "Ошибка: «{name}» больше не существует!",
        "status_error_prefix": "Ошибка: {error}",
        "metric_tokens": "Токены ИИ (оценка)",
        "metric_tokens_tooltip": (
            "Примерное количество токенов, которое сгенерированный Markdown-текст займёт "
            "в ИИ-моделях ChatGPT, Claude или Gemini (1 токен ≈ 4 символа).\n\n"
            "Зачем это нужно?\n"
            "• У каждой языковой модели есть лимит контекстного окна.\n"
            "• Оценка позволяет заранее понять, поместится ли документ в запрос к ИИ."
        ),
        "metric_words": "Количество слов",
        "metric_words_tooltip": (
            "Общее количество слов в полученном Markdown-документе.\n\n"
            "Позволяет быстро оценить объём и полноту извлечённого текста."
        ),
        "metric_chars": "Количество символов",
        "metric_chars_tooltip": (
            "Общая длина полученного текста в символах, включая пробелы, знаки препинания "
            "и разметку Markdown."
        ),
        "metric_time": "Время выполнения",
        "metric_error": "Ошибка",
        "unit_sec": "с",
        "unit_ms": "мс",
        "btn_copy": "📋  Скопировать",
        "btn_copied": "✔  Скопировано",
        "btn_open": "↗  Открыть файл",
        "btn_reveal": "📁  Показать в папке",
        "dialog_select_title": "Выберите файл для конвертации",
        "filetype_supported": "Поддерживаемые файлы",
        "filetype_pdf": "Файлы PDF",
        "filetype_office": "Документы Office",
        "filetype_web_data": "Веб и файлы данных",
        "filetype_all": "Все файлы",
        "combined_file_header": "<!-- Файл: {name} -->",
        "err_file_not_found": "Выбранный файл не найден: {name}",
        "err_pdf_no_text_layer": "Не удалось извлечь текст (скан/изображение PDF без текстового слоя).",
        "err_no_text_extracted": "Не удалось извлечь текст (возможно, скан PDF или пустой файл).",
        "err_unknown_conversion": "Неизвестная ошибка конвертации.",
        "err_missing_dependency": "Отсутствует необходимая библиотека для этого типа файла. Перезапустите через run.bat.",
        "err_pip_install_failed": "Не удалось установить библиотеки ({packages}): {detail}",
    },
}

_current_lang: str = DEFAULT_LANGUAGE


def get_language() -> str:
    """Aktif dil kodunu döndürür."""
    return _current_lang


def load_language() -> str:
    """settings.json dosyasından dil tercihini yükler; yoksa varsayılan 'tr' döner."""
    global _current_lang
    lang = DEFAULT_LANGUAGE
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            candidate = str(data.get("lang", "")).strip().lower()
            if candidate in TRANSLATIONS:
                lang = candidate
        except Exception as exc:
            logger.warning("settings.json okunamadı, varsayılan dil (%s) kullanılacak: %s", DEFAULT_LANGUAGE, exc)
    _current_lang = lang
    return _current_lang


def save_language(lang_code: str) -> str:
    """Seçilen dili aktif dil olarak ayarlar ve settings.json dosyasına kaydeder."""
    global _current_lang
    normalized = lang_code.strip().lower()
    if normalized not in TRANSLATIONS:
        logger.warning("Desteklenmeyen dil kodu '%s', varsayılan '%s' kullanılıyor.", lang_code, DEFAULT_LANGUAGE)
        normalized = DEFAULT_LANGUAGE
    _current_lang = normalized
    try:
        SETTINGS_FILE.write_text(
            json.dumps({"lang": normalized}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("Dil ayarı kaydedildi: %s -> %s", normalized, SETTINGS_FILE)
    except Exception as exc:
        logger.warning("settings.json yazılamadı: %s", exc)
    return _current_lang


def t(key: str, **kwargs: Any) -> str:
    """Aktif dildeki çeviri metnini döndürür ve varsa yer tutucuları doldurur."""
    lang_dict = TRANSLATIONS.get(_current_lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    template = lang_dict.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


def get_supported_filetypes() -> list[tuple[str, str]]:
    """Dosya seçme penceresi için aktif dile göre filtrelenmiş dosya türlerini döndürür."""
    return [(t(key), pattern) for key, pattern in FILETYPE_PATTERNS]


load_language()
