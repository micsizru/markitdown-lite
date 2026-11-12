"""MarkItDown ve doğrudan PDF saf metin çıkarımını yöneten dönüştürme servis katmanı."""

from dataclasses import dataclass
from pathlib import Path
import time

from app.i18n import t
from app.logger import get_logger, log_exception
from app.text_cleaner import clean_markdown_for_llm, estimate_tokens

logger = get_logger("converter_service")


@dataclass
class ConversionOptions:
    """Kullanıcının arayüzden seçtiği dönüştürme ayarları."""

    pdf_plain_text: bool = True
    clean_for_llm: bool = True


@dataclass
class ConversionResult:
    """Tek bir dosyanın dönüştürme çıktısı ve istatistikleri."""

    success: bool
    source_path: Path
    output_path: Path | None = None
    content: str = ""
    char_count: int = 0
    word_count: int = 0
    token_count: int = 0
    elapsed_ms: int = 0
    used_engine: str = ""
    error_message: str = ""


class ConverterService:
    """UI'dan tamamen bağımsız belge dönüştürme servisi.

    - PDF dosyalarında önce '_check_pdf_has_text_layer' ile milisaniyeler içinde
      metin katmanı kontrolü (Fast-Fail) yapar; taranmış/görsel PDF'lerde dakikalarca
      beklemeden anında uyarı verir.
    - PDF dosyalarında 'pdf_plain_text=True' seçiliyse MarkItDown'un bozuk tablo
      üreten katmanını atlayıp doğrudan 'pdfminer.high_level.extract_text' kullanır (Yöntem 1).
    - Diğer tüm dosya türlerinde (veya 'pdf_plain_text=False' olduğunda)
      MarkItDown motorunu lazy-loading ile çalıştırır.
    """

    def __init__(self) -> None:
        self._md_engine = None
        logger.debug("ConverterService nesnesi oluşturuldu (MarkItDown henüz yüklenmedi - Lazy Init).")

    def _get_markitdown_engine(self):
        """MarkItDown nesnesini ilk ihtiyaç duyulduğunda başlatır."""
        if self._md_engine is None:
            t0 = time.perf_counter()
            logger.info("MarkItDown motoru başlatılıyor (Lazy-Loading)...")
            print("[ENGINE] MarkItDown() nesnesi belleğe yükleniyor...")
            from markitdown import MarkItDown

            self._md_engine = MarkItDown()
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.info("MarkItDown motoru %d ms içinde hazır hale geldi.", elapsed)
            print(f"[ENGINE] MarkItDown() {elapsed} ms içinde başlatıldı.")
        return self._md_engine

    @staticmethod
    def resolve_output_path(source_path: Path) -> Path:
        """Kaynak dosyanın üzerine yazmayı önleyecek hedef .md yolunu hesaplar."""
        if source_path.suffix.lower() == ".md":
            return source_path.with_name(f"{source_path.stem}_converted.md")
        return source_path.with_suffix(".md")

    def _check_pdf_has_text_layer(self, source_path: Path) -> bool:
        """PDF'in ilk sayfalarını milisaniyeler içinde kontrol ederek metin katmanı olup olmadığını tespit eder."""
        t0 = time.perf_counter()
        try:
            import pypdfium2 as pdfium

            doc = pdfium.PdfDocument(str(source_path))
            try:
                page_count = len(doc)
                if page_count == 0:
                    return False

                # İlk 3 sayfayı + ortadaki sayfayı örnekle
                sample_indices = sorted(
                    set([idx for idx in (0, 1, 2, page_count // 2, page_count - 1) if 0 <= idx < page_count])
                )
                total_chars = 0
                for idx in sample_indices:
                    page = doc[idx]
                    textpage = page.get_textpage()
                    extracted = textpage.get_text_range().strip()
                    textpage.close()
                    page.close()
                    total_chars += len(extracted)
                    if total_chars > 0:
                        break

                elapsed = int((time.perf_counter() - t0) * 1000)
                logger.info(
                    "PDF erken metin katmanı kontrolü (%d ms): Toplam sayfa=%d, örneklenen=%s, bulunan karakter=%d",
                    elapsed,
                    page_count,
                    sample_indices,
                    total_chars,
                )
                print(
                    f"[PDF-PRECHECK] '{source_path.name}' ({page_count} sayfa) {elapsed} ms içinde kontrol edildi -> "
                    f"karakter={total_chars}"
                )
                return total_chars > 0
            finally:
                doc.close()
        except Exception as exc:
            logger.debug("pypdfium2 ön kontrolü atlandı, pdfminer maxpages=2 ile kontrol edilecek: %s", exc)
            try:
                from pdfminer.high_level import extract_text

                sample = extract_text(str(source_path), maxpages=2)
                return bool(sample and sample.strip())
            except Exception:
                return True

    def _extract_pdf_plain_text(self, source_path: Path) -> str:
        """Yöntem 1: Kütüphane koduna dokunmadan doğrudan pdfminer.six ile saf metin çıkarır."""
        logger.info("PDF Saf Metin Modu aktif: '%s' doğrudan pdfminer.high_level.extract_text ile okunuyor.", source_path.name)
        print(f"[PDF-PLAIN] '{source_path.name}' için tablo algılama devre dışı; saf metin çıkarılıyor...")
        from pdfminer.high_level import extract_text

        raw_text = extract_text(str(source_path))
        logger.debug("pdfminer ham metin çıkarımı tamamlandı (%d karakter).", len(raw_text) if raw_text else 0)
        return raw_text or ""

    def _extract_with_markitdown(self, source_path: Path) -> str:
        """Standart MarkItDown motoru ile dosyayı dönüştürür."""
        engine = self._get_markitdown_engine()
        logger.info("MarkItDown.convert çağrılıyor: '%s'", source_path)
        print(f"[MARKITDOWN] '{source_path.name}' standart motor ile dönüştürülüyor...")
        result = engine.convert(str(source_path))
        content = result.text_content if result and result.text_content else ""
        logger.debug("MarkItDown ham çıktı uzunluğu: %d karakter.", len(content))
        return content

    def convert_file(self, source_path: Path, options: ConversionOptions) -> ConversionResult:
        """Verilen dosyayı belirtilen seçeneklerle Markdown'a dönüştürür ve yanına kaydeder."""
        t_start = time.perf_counter()
        logger.info(
            "Dönüştürme başladı -> Dosya: '%s' | Boyut: %s byte | Ayarlar: pdf_plain_text=%s, clean_for_llm=%s",
            source_path,
            source_path.stat().st_size if source_path.exists() else "YOK",
            options.pdf_plain_text,
            options.clean_for_llm,
        )
        print(f"[CONVERT-START] Dosya: {source_path.name} (pdf_plain={options.pdf_plain_text}, clean={options.clean_for_llm})")

        if not source_path.exists():
            msg = t("err_file_not_found", name=source_path.name)
            logger.error(msg)
            return ConversionResult(
                success=False,
                source_path=source_path,
                error_message=msg,
            )

        try:
            is_pdf = source_path.suffix.lower() == ".pdf"

            # Erken Tespit (Fast-Fail): Taranmış / metin katmanı olmayan PDF'leri dakikalarca bekletmeden yakala
            if is_pdf and not self._check_pdf_has_text_layer(source_path):
                raise ValueError(t("err_pdf_no_text_layer"))

            if is_pdf and options.pdf_plain_text:
                used_engine = "pdfminer (Saf Metin / Tablosuz)"
                content = self._extract_pdf_plain_text(source_path)
            else:
                used_engine = "MarkItDown (Standart)"
                content = self._extract_with_markitdown(source_path)

            if options.clean_for_llm and content:
                content = clean_markdown_for_llm(content)

            if not content or not content.strip():
                raise ValueError(t("err_no_text_extracted"))

            output_path = self.resolve_output_path(source_path)
            output_path.write_text(content, encoding="utf-8")

            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            char_count = len(content)
            word_count = len(content.split())
            token_count = estimate_tokens(content)

            logger.info(
                "Dönüştürme BAŞARILI -> Çıktı: '%s' | Motor: %s | Süre: %d ms | "
                "Karakter: %d | Kelime: %d | Tahmini Token: ~%d",
                output_path,
                used_engine,
                elapsed_ms,
                char_count,
                word_count,
                token_count,
            )
            print(
                f"[CONVERT-OK] '{output_path.name}' kaydedildi ({elapsed_ms} ms, "
                f"{word_count} kelime, ~{token_count} token)"
            )

            return ConversionResult(
                success=True,
                source_path=source_path,
                output_path=output_path,
                content=content,
                char_count=char_count,
                word_count=word_count,
                token_count=token_count,
                elapsed_ms=elapsed_ms,
                used_engine=used_engine,
            )

        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            log_exception(f"convert_file({source_path.name})", exc)
            error_msg = str(exc).strip() or t("err_unknown_conversion")
            if "MissingDependencyException" in error_msg:
                error_msg = t("err_missing_dependency")
            print(f"[CONVERT-FAIL] '{source_path.name}' dönüştürülemedi ({elapsed_ms} ms): {error_msg}")
            return ConversionResult(
                success=False,
                source_path=source_path,
                elapsed_ms=elapsed_ms,
                error_message=error_msg,
            )
