# Budowanie wersji Windows EXE

## Stan

Plik EXE nie został zbudowany w środowisku wykonawczym, ponieważ było to macOS z Pythonem 3.14. PyInstaller nie tworzy wiarygodnego Windows EXE w trybie cross-build. To konkretny blokujący warunek; kod, specyfikacja i skrypt Windows są gotowe.

## Dlaczego one-folder

Wersja pilotażowa używa `one-folder`. Ułatwia to dołączanie pluginów Qt, lokalnego `wbb`, konfiguracji i zasobów oraz diagnostykę na stanowisku. `one-file` nie jest zalecane przed testem sprzętu i czystej instalacji.

## Wymagania

- Windows 11;
- Python 3.12 w `.venv`;
- zainstalowane `requirements-dev.txt`;
- lokalny `wbb-module` zainstalowany editable w tym samym środowisku;
- przechodzące testy i poprawna diagnostyka sprzętu.

## Budowa

```powershell
Set-Location C:\Projekty\WBB_Rehab
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
.\build_windows.ps1
```

Skrypt:

1. potwierdza Python 3.12;
2. uruchamia testy i przerywa przy pierwszym niepowodzeniu;
3. czyści wyłącznie lokalne `build` i `dist`;
4. buduje `Kulturysta.spec`;
5. kopiuje konfigurację i własny placeholder logo;
6. tworzy puste katalogi danych bez prawdziwych danych osobowych;
7. podaje ścieżkę `dist\Kulturysta\Kulturysta.exe`.

## Test czystego katalogu

1. Skopiuj cały `dist\Kulturysta` do nowego katalogu, np. `C:\TestKulturysta`.
2. Upewnij się, że nie zawiera żadnych plików z `data\participants` ani `data\sessions`.
3. Uruchom `Kulturysta.exe` bez aktywnego środowiska Python.
4. Połącz symulator, wykonaj krótki pomiar i otwórz wszystkie zakładki.
5. Sprawdź CSV/XLSX/JSON/MD/PDF.
6. Sprawdź log w `data\logs\app.log`.
7. Dopiero potem przeprowadź checklistę fizycznej platformy.

## Typowe problemy

- `ModuleNotFoundError: wbb`: zainstaluj lokalny moduł w `.venv` przed budową; sprawdź `python -c "import wbb; print(wbb.__file__)"`.
- brak pluginu Qt: zachowaj cały folder dystrybucji; nie kopiuj samego EXE.
- zasób niewidoczny: sprawdź `dist\Kulturysta\assets\logo_placeholder.png` i `config\default_config.json`.
- alarm antywirusowy: podpisz wynik zgodnie z procesem IT jednostki; nie wyłączaj ochrony systemu.
- błąd tylko na innym komputerze: zapisz wersję Windows, architekturę, log i pełny komunikat; nie uznawaj budowy za zweryfikowaną bez tego testu.
