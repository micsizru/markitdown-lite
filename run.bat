@echo off
setlocal EnableDelayedExpansion
title MarkItDown Hizli Donusturucu - Baslatici

set "SCRIPT_DIR=%~dp0"
set "APP_FILE=%SCRIPT_DIR%converter_app.pyw"
set "LOG_DIR=%SCRIPT_DIR%__pycache__"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "PYTHON_EXE="
set "PYTHONW_EXE="

:: 1. Adim: Sistemde calisan gecerli bir Python yorumlayicisi bul
for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-*") do (
    if exist "%%~fD\python.exe" (
        set "PYTHON_EXE=%%~fD\python.exe"
        set "PYTHONW_EXE=%%~fD\pythonw.exe"
    )
)

if not defined PYTHON_EXE (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%~fD\python.exe" (
            set "PYTHON_EXE=%%~fD\python.exe"
            set "PYTHONW_EXE=%%~fD\pythonw.exe"
        )
    )
)

if not defined PYTHON_EXE (
    py -3 -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)"') do (
            set "PYTHON_EXE=%%P"
        )
    )
)

if not defined PYTHON_EXE (
    python -c "import sys; raise SystemExit(0 if sys.executable else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)"') do (
            set "PYTHON_EXE=%%P"
        )
    )
)

if not defined PYTHON_EXE (
    echo [HATA] Sisteminizde kurulu bir Python 3 yorumlayicisi bulunamadi!
    echo Lutfen https://www.python.org/downloads/ adresinden Python 3 kurun.
    pause
    exit /b 1
)

if not defined PYTHONW_EXE (
    for %%F in ("%PYTHON_EXE%") do (
        if exist "%%~dpFpythonw.exe" (
            set "PYTHONW_EXE=%%~dpFpythonw.exe"
        ) else (
            set "PYTHONW_EXE=%PYTHON_EXE%"
        )
    )
)

:: 2. Adim: __pycache__ altinda tarih + saat + benzersiz ID ile log dosyasi olustur
for /f "usebackq delims=" %%L in (`"%PYTHON_EXE%" -c "import datetime, uuid; print(datetime.datetime.now().strftime('run_%%Y%%m%%d_%%H%%M%%S_') + uuid.uuid4().hex[:8] + '.log')"`) do (
    set "LOG_FILENAME=%%L"
)
if not defined LOG_FILENAME (
    set "LOG_FILENAME=run_session_%RANDOM%%RANDOM%.log"
)
set "MARKITDOWN_LOG_FILE=%LOG_DIR%\%LOG_FILENAME%"

echo [BAT-BOOT] Baslatici calisti: %DATE% %TIME% >> "%MARKITDOWN_LOG_FILE%"
echo [BAT-BOOT] Bulunan PYTHON_EXE : %PYTHON_EXE% >> "%MARKITDOWN_LOG_FILE%"
echo [BAT-BOOT] Bulunan PYTHONW_EXE: %PYTHONW_EXE% >> "%MARKITDOWN_LOG_FILE%"

:: 3. Adim: Gerekli tum pip kutuphanelerinin kurulu olup olmadigini kontrol et
"%PYTHON_EXE%" -c "import markitdown, pdfminer, pdfplumber, mammoth, openpyxl, pandas, xlrd, pptx, lxml, bs4, olefile" >> "%MARKITDOWN_LOG_FILE%" 2>&1
if !errorlevel! neq 0 (
    echo [BAT-PIP] Eksik kutuphane tespit edildi, kurulum baslatiliyor... >> "%MARKITDOWN_LOG_FILE%"
    echo ====================================================================
    echo [BILGI] Eksik Python kutuphaneleri tespit edildi.
    echo Gerekli belge donusturme motorlari otomatik olarak kuruluyor...
    echo ====================================================================
    "%PYTHON_EXE%" -m pip install --upgrade pip >> "%MARKITDOWN_LOG_FILE%" 2>&1
    "%PYTHON_EXE%" -m pip install markitdown pdfminer.six pdfplumber mammoth openpyxl pandas xlrd python-pptx lxml beautifulsoup4 olefile >> "%MARKITDOWN_LOG_FILE%" 2>&1
    if !errorlevel! neq 0 (
        echo [BAT-ERR] Pip kurulumu basarisiz oldu! >> "%MARKITDOWN_LOG_FILE%"
        echo.
        echo [HATA] Kutuphane kurulumu sirasinda bir sorun olustu!
        echo Detaylar icin log dosyasina bakin: "%MARKITDOWN_LOG_FILE%"
        pause
        exit /b 1
    )
    echo [BAT-PIP] Tum kutuphaneler basariyla kuruldu. >> "%MARKITDOWN_LOG_FILE%"
    echo.
    echo [BASARILI] Tum kutuphaneler basariyla kuruldu! Uygulama baslatiliyor...
) else (
    echo [BAT-OK] Tum gerekli Python kutuphaneleri dogrulandi. >> "%MARKITDOWN_LOG_FILE%"
)

:: 4. Adim: Uygulamayi konsolsuz (pythonw.exe) olarak baslat
echo [BAT-LAUNCH] converter_app.pyw baslatiliyor... >> "%MARKITDOWN_LOG_FILE%"
start "" "%PYTHONW_EXE%" "%APP_FILE%"
exit /b 0
