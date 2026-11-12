# MarkItDown Lite

[Türkçe](#-türkçe) | [Русский](#-русский)

---

## 🇹🇷 Türkçe

Üniversite eğitimim süresince, bir yabancı öğrenci olduğum için genellikle yazılı kaynaklar üzerinden çalışıyorum. Doküman halindeki ders materyallerini yapay zeka ile sürekli olarak kullanıyordum, ancak tokenlarımı verimli tüketmek için bir arayışa girme vakti gelmişti. Microsoft'un [MarkItDown](https://github.com/microsoft/markitdown) reposuna rastladım. Fikir hoşuma gitti fakat kullanım şekli hoşuma gitmemişti. Ben de asıl işi yapan kodun üzerine bir kıyafet giydirdim ve günlük hızlı kullanıma müsait hale getirdim.

### Ne İşe Yarar?

PDF, Word, Excel, PowerPoint ve benzeri dokümanları tek tıkla sade ve temiz `.md` (Markdown) dosyalarına dönüştürür. Çıktıyı doğrudan panoya kopyalayabilir, dosyayı açabilir veya üretilen metnin tahmini yapay zeka token maliyetini anında görebilirsiniz.

### Özellikler

- **Geniş Dosya Desteği:** `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.html`, `.htm`, `.csv`, `.json`, `.xml`, `.txt`, `.zip`, `.msg`, `.epub`
- **Saf Metin Modu (PDF):** Karmaşık tablo ayrıştırmasını kapatarak PDF içeriğini düz akış halinde çıkarır; özellikle çok sütunlu ders notları ve kitaplar için uygundur.
- **Gelişmiş Metin Temizliği:** Bozuk font kalıntılarını (`cid:...`), satır sonu tire bölünmelerini ve gereksiz boş satırları temizleyerek token israfını azaltır.
- **Çıktı Özeti:** Oluşturulan Markdown dosyası için tahmini AI tokenı, kelime ve karakter sayısını gösterir.
- **Çoklu Dil Desteği:** Arayüz üzerinden yeniden başlatmaya gerek kalmadan **Türkçe**, **English** ve **Русский** arasında geçiş yapabilirsiniz.

### Kurulum ve Çalıştırma

#### Windows (Tek Tıkla)

[`run.bat`](run.bat) dosyasına çift tıklamanız yeterlidir. Sistemdeki Python 3 kurulumunu bulur, eksik kütüphane varsa `requirements.txt` içindeki paketleri otomatik yükler ve uygulamayı konsol penceresi açmadan başlatır.

#### Manuel Çalıştırma

```bash
pip install -r requirements.txt
python converter_app.pyw
```

> **Gereksinim:** Python 3.10+ (Tkinter dahili olarak gelmelidir)

### Proje Yapısı

```text
markitdown-lite/
├── app/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Ana arayüz penceresi ve kullanıcı etkileşimleri
│   │   └── widgets.py          # Özel arayüz bileşenleri (Buton, Switch, ToolTip, ProgressBar)
│   ├── __init__.py
│   ├── config.py               # Tema renkleri, fontlar, dosya filtreleri ve paket listesi
│   ├── converter_service.py    # Dosyaları Markdown'a dönüştüren servis katmanı
│   ├── env_manager.py          # Çalışma zamanı kütüphane kontrolü
│   ├── i18n.py                 # TR / EN / RU dil sözlükleri ve ayar kaydı
│   ├── logger.py               # Oturum loglama yardımcısı
│   └── text_cleaner.py         # LLM odaklı metin temizleme kuralları
├── run.bat                  # Windows başlatıcı ve otomatik kurulum betiği
├── converter_app.pyw           # Uygulama giriş noktası (High-DPI desteği ile)
└── requirements.txt            # Gerekli Python paketleri
```

## 🇷🇺 Русский

Во время учёбы в университете, будучи иностранным студентом, я в основном занимаюсь по письменным источникам. Я постоянно загружал учебные материалы в виде документов в ИИ, но в какой-то момент решил найти способ расходовать токены более экономно. Так я наткнулся на репозиторий [MarkItDown](https://github.com/microsoft/markitdown) от Microsoft. Сама идея мне понравилась, но формат использования показался неудобным. Поэтому я просто «одел» основной движок в удобную оболочку и адаптировал его для быстрого повседневного использования.

### Зачем это нужно?

Приложение в один клик конвертирует PDF, Word, Excel, PowerPoint и другие документы в чистый формат `.md` (Markdown). Готовый результат можно сразу скопировать в буфер обмена, открыть файл или оценить примерное количество токенов для ИИ.

### Возможности

- **Поддерживаемые форматы:** `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.html`, `.htm`, `.csv`, `.json`, `.xml`, `.txt`, `.zip`, `.msg`, `.epub`
- **Режим чистого текста (PDF):** Отключает разбор таблиц и извлекает текст линейным потоком — удобно для лекций, книг и многоколоночных PDF.
- **Глубокая очистка текста:** Удаляет артефакты шрифтов (`cid:...`), переносы слов на концах строк и лишние пустые строки, снижая расход токенов.
- **Сводка документа:** Показывает примерное количество токенов для LLM, число слов и символов.
- **Мультиязычность:** Мгновенное переключение интерфейса между **Türkçe**, **English** и **Русский** без перезапуска.

### Установка и запуск

#### Windows (в один клик)

Просто запустите [`run.bat`](run.bat). Скрипт сам найдёт установленный Python 3, при необходимости установит недостающие библиотеки и запустит программу без окна консоли.

#### Ручной запуск

```bash
pip install -r requirements.txt
python converter_app.pyw
```

> **Требования:** Python 3.10+ (со встроенным Tkinter)

### Структура проекта

```text
markitdown-lite/
├── app/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Главное окно интерфейса и обработка событий
│   │   └── widgets.py          # Пользовательские виджеты (кнопки, переключатели, подсказки)
│   ├── __init__.py
│   ├── config.py               # Цвета темы, шрифты, фильтры файлов и список зависимостей
│   ├── converter_service.py    # Сервис конвертации документов в Markdown
│   ├── env_manager.py          # Проверка зависимостей во время запуска
│   ├── i18n.py                 # Словари TR / EN / RU и сохранение выбранного языка
│   ├── logger.py               # Логирование сессии
│   └── text_cleaner.py         # Постобработка текста для ИИ
├── run.bat                  # Лаунчер для Windows с автоустановкой пакетов
├── converter_app.pyw           # Точка входа в приложение (с поддержкой High-DPI)
└── requirements.txt            # Список необходимых библиотек Python
```
