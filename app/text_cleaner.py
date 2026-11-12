"""AI/LLM için Markdown metin temizleme, (cid) kalıntılarını silme ve token hesaplama modülü."""

import re

from app.logger import get_logger

logger = get_logger("text_cleaner")

# LaTeX/PDF fontlarında Unicode karşılığı olmayan (cid:112) vb. kalıntılar
_CID_PATTERN = re.compile(r"\(cid:\d+\)")

# Satır sonlarındaki gereksiz boşluk ve sekmeler
_TRAILING_SPACE_PATTERN = re.compile(r"[ \t]+$", re.MULTILINE)

# Satır içindeki 3+ ardışık boşluk (tablo olmayan düz metinlerde)
_MULTI_SPACE_PATTERN = re.compile(r"(?<!\|)[ \t]{3,}(?!\|)")

# 3 veya daha fazla ardışık yeni satır
_EXCESS_NEWLINES_PATTERN = re.compile(r"\n{3,}")

# PDF'lerde kelimelerin satır sonunda tire ile bölünmesi (ör. "алгеб-\nра" -> "алгебра")
_HYPHENATED_LINEBREAK_PATTERN = re.compile(r"([a-zA-Zа-яА-ЯёЁğüşıöçĞÜŞİÖÇ])-\r?\n([a-zA-Zа-яА-ЯёЁğüşıöçĞÜŞİÖÇ])")


def strip_cid_artifacts(text: str) -> tuple[str, int]:
    """Metindeki (cid:NNN) kalıntılarını temizler ve silinen eşleşme sayısını döndürür."""
    matches = _CID_PATTERN.findall(text)
    count = len(matches)
    if count > 0:
        text = _CID_PATTERN.sub("", text)
        logger.debug("%d adet (cid:NNN) font kalıntısı temizlendi.", count)
    return text, count


def dehyphenate_lines(text: str) -> str:
    """PDF satır sonu tirelemelerini (kelime bölünmelerini) birleştirir."""
    return _HYPHENATED_LINEBREAK_PATTERN.sub(r"\1\2", text)


def compact_whitespace(text: str) -> str:
    """Fazla boşlukları, form feed (\\x0c) karakterlerini ve ardışık boş satırları sıkıştırır."""
    # Form feed (sayfa sonu) karakterlerini temiz satır geçişine çevir
    text = text.replace("\x0c", "\n\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_SPACE_PATTERN.sub("", text)
    text = _MULTI_SPACE_PATTERN.sub(" ", text)
    text = _EXCESS_NEWLINES_PATTERN.sub("\n\n", text)
    return text.strip() + "\n"


def estimate_tokens(text: str) -> int:
    """Metnin yaklaşık LLM token sayısını hesaplar.

    Standart BPE tokenizer'larda (GPT-4o / Claude / Gemini):
    - İngilizce/Türkçe/Rusça ve matematiksel sembol karışık metinlerde ortalama ~3.6-4.0 karakter ≈ 1 token.
    """
    if not text or not text.strip():
        return 0
    char_count = len(text)
    word_count = len(text.split())
    # Karakter tabanlı ve kelime tabanlı tahminin ağırlıklı ortalaması
    by_chars = char_count / 3.8
    by_words = word_count * 1.45
    estimated = int(round((by_chars * 0.65) + (by_words * 0.35)))
    return max(1, estimated)


def clean_markdown_for_llm(text: str, remove_cid: bool = True, dehyphenate: bool = True) -> str:
    """AI/LLM token tüketimini azaltmak ve okunabilirliği artırmak için metni optimize eder."""
    if not text:
        return ""

    original_len = len(text)
    original_tokens = estimate_tokens(text)

    cid_removed = 0
    if remove_cid:
        text, cid_removed = strip_cid_artifacts(text)

    if dehyphenate:
        text = dehyphenate_lines(text)

    text = compact_whitespace(text)

    final_len = len(text)
    final_tokens = estimate_tokens(text)
    saved_chars = original_len - final_len
    saved_tokens = original_tokens - final_tokens

    logger.info(
        "Metin temizleme tamamlandı: %d -> %d karakter (%d karakter tasarruf), "
        "~%d -> ~%d token (%d token tasarruf), silinen (cid): %d",
        original_len,
        final_len,
        saved_chars,
        original_tokens,
        final_tokens,
        saved_tokens,
        cid_removed,
    )
    print(
        f"[CLEANER] Temizlik özeti: {saved_chars} karakter / ~{saved_tokens} token kazanıldı "
        f"(silinen cid={cid_removed})"
    )
    return text
