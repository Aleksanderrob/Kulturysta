# Instalacja na Windows 11

## 1. Wymagania

- Windows 11 (aktualny, 64-bit);
- Bluetooth działający w systemie;
- oryginalna Nintendo Wii Balance Board i sprawne baterie;
- Python 3.12.x, Git oraz PowerShell;
- dostęp do lokalnego katalogu `C:\Projekty\wii-board-module`;
- możliwość zapisu do `C:\Projekty\WBB_Rehab` bez uruchamiania aplikacji jako administrator.

Administrator może być potrzebny tylko do czynności wskazanych przez sterownik Bluetooth lub rzeczywisty moduł WBB. Codzienne uruchamianie aplikacji nie powinno wymagać podwyższonych uprawnień.

## 2. Python 3.12

Pobierz instalator Pythona 3.12 z oficjalnej strony Python Software Foundation. W instalatorze zaznacz `Add python.exe to PATH`. Po instalacji otwórz nowy PowerShell:

```powershell
py -0p
py -3.12 --version
```

Drugie polecenie musi pokazać `Python 3.12.x`. Python 3.14 nie jest wersją rekomendowaną dla stanowiska produkcyjnego, nawet jeśli obecne testy przechodzą na 3.14.

## 3. Katalogi projektu

Zalecany układ:

```text
C:\Projekty\WBB_Rehab
C:\Projekty\wii-board-module
```

Klonowanie aplikacji:

```powershell
New-Item -ItemType Directory -Force C:\Projekty | Out-Null
Set-Location C:\Projekty
git clone https://github.com/Aleksanderrob/Kulturysta.git WBB_Rehab
Set-Location C:\Projekty\WBB_Rehab
```

Repozytorium jest prywatne, więc GitHub może poprosić o zalogowanie. Nie wklejaj tokenu do skryptów ani plików projektu.

## 4. Środowisko wirtualne

Nie kopiuj `.venv` z innego komputera ani katalogu.

```powershell
Set-Location C:\Projekty\WBB_Rehab
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Do testów i budowy EXE:

```powershell
python -m pip install -r requirements-dev.txt
```

## 5. Lokalny `wbb-module`

W środowisku wykonawczym moduł nie był dostępny, dlatego nie potwierdzono żadnego `extra` o nazwie `[windows]`. Nie używaj niesprawdzonego `-e ".[windows]"`.

Bezpieczna instalacja bazowa projektu lokalnego:

```powershell
Set-Location C:\Projekty\wii-board-module
C:\Projekty\WBB_Rehab\.venv\Scripts\python.exe -m pip install -e .
```

Jeżeli rzeczywisty `pyproject.toml` dokumentuje konkretny extra dla Windows, dopiero wtedy użyj dokładnej nazwy z pliku. Sprawdź import:

```powershell
Set-Location C:\Projekty\WBB_Rehab
.\.venv\Scripts\Activate.ps1
python -c "from wbb import BalanceBoard; print('OK', BalanceBoard)"
python tools\inspect_wbb_api.py
```

Zachowaj wynik inspekcji. Jeżeli `connect`, `tare` lub `stream` mają inne nazwy albo parametry, zaktualizuj mapę w `hardware/wii_board_adapter.py` na podstawie faktów z modułu.

## 6. Parowanie Wii Balance Board

Ten projekt celowo nie wymyśla kodu PIN, nazwy skryptu parującego ani sekwencji specyficznej dla nieobecnego `wbb-module`.

1. Przeczytaj `README`, `pyproject.toml` i katalog przykładów w `C:\Projekty\wii-board-module`.
2. Użyj wyłącznie wskazanego tam skryptu lub procedury Windows.
3. Naciśnij czerwony przycisk `SYNC` w komorze baterii dopiero w kroku wymaganym przez procedurę modułu.
4. Jeśli dokumentacja wymaga PowerShell jako administrator, uruchom podwyższone okno tylko dla tego kroku.
5. Nie wpisuj losowego PIN-u i nie zapisuj go w repozytorium.
6. Po parowaniu wróć do zwykłego PowerShell i uruchom diagnostykę.

```powershell
Set-Location C:\Projekty\WBB_Rehab
.\.venv\Scripts\Activate.ps1
python tools\hardware_diagnostics.py --cop-unit unknown --interactive
```

Zastąp `unknown` wyłącznie jednostką potwierdzoną przez kod lub dokumentację sterownika: np. `m`, `cm`, `mm` albo `normalized`.

## 7. Pierwsze uruchomienie i symulator

```powershell
Set-Location C:\Projekty\WBB_Rehab
.\.venv\Scripts\Activate.ps1
python main.py
```

1. Wybierz `Symulator`.
2. Wybierz `Kołysanie sinusoidalne`.
3. Kliknij `Połącz`.
4. Sprawdź ruch COP, masę i częstotliwość.
5. Ustaw identyfikator uczestnika `TEST-SIM` i tryb samego identyfikatora.
6. Ustaw krótki pomiar, wykonaj go i sprawdź `data\sessions`.
7. Otwórz XLSX, Markdown i PDF.

## 8. Test fizycznej platformy

Po poprawnej diagnostyce wybierz `Wii Balance Board` i `Połącz`. Nie rozpoczynaj ćwiczenia bez operatora, asekuracji i stabilnego, płaskiego podłoża. Wykonaj całą listę z `MANUAL_TEST_CHECKLIST.md` i zapisz datę, wersję sterownika, jednostkę COP oraz wynik.

## 9. Testy

```powershell
python -m pytest
python -m pytest -m hardware
python -m ruff check .
```

Pierwsze polecenie nie wymaga sprzętu. Drugie uruchamia odseparowaną grupę sprzętową; główna kontrola sprzętu znajduje się w skrypcie diagnostycznym i checkliście manualnej.

## 10. Rozwiązywanie problemów

### `Fatal error in launcher` albo błędny `pip.exe`

Środowisko prawdopodobnie przeniesiono lub wskazuje stary katalog. Usuń wyłącznie `.venv` projektu i utwórz je ponownie:

```powershell
Set-Location C:\Projekty\WBB_Rehab
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -c "import sys; print(sys.executable)"
python -m pip --version
```

Zawsze używaj `python -m pip`, nie samego `pip`.

### PowerShell blokuje `Activate.ps1`

Sprawdź politykę jednostki. Dla bieżącego procesu, jeśli regulamin na to pozwala:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Alternatywnie nie aktywuj środowiska i wywołuj `.\.venv\Scripts\python.exe` bezpośrednio.

### Brak importu `wbb` lub `hidapi`

```powershell
python -m pip show wbb-module
python -m pip show hidapi
python -c "import sys; print(sys.executable)"
python -c "import wbb; print(wbb.__file__)"
```

Ponownie zainstaluj lokalny moduł w tym samym interpreterze. Nie naprawiaj aplikacji przez kopiowanie pojedynczych plików pakietu.

### Platforma niewidoczna albo rozłącza się

- wymień baterie i powtórz procedurę `SYNC` dokładnie według modułu;
- usuń stare, nieaktywne parowanie tylko po potwierdzeniu, że można je odtworzyć;
- sprawdź logi `data\logs\app.log` i `hardware_diagnostics.log`;
- wyłącz na próbę oszczędzanie energii adaptera Bluetooth zgodnie z polityką IT;
- sprawdź, czy inne narzędzie nie trzyma połączenia.

### Python 3.14 i problemy binarne

Nie mieszaj pakietów z interpreterów. Utwórz nowe `.venv` przez `py -3.12 -m venv .venv` i zainstaluj wymagania od nowa.

### COP poza widokiem albo z błędną jednostką

Nie zmieniaj etykiety na `mm` bez potwierdzenia. Ustal jednostkę w sterowniku, uruchom diagnostykę i dopiero potem ustaw skalę/`cop_unit`. Widget sygnalizuje punkt poza stałą skalą zamiast go cicho ukrywać.

### GUI zamraża się

Odczyt powinien działać w `AcquisitionWorker`. Sprawdź log pod kątem wyjątku w wątku i upewnij się, że nikt nie wywołuje generatora sterownika bezpośrednio z `QTimer` GUI.

### PDF nie powstaje lub polskie znaki są niepoprawne

```powershell
python -m pip install --force-reinstall reportlab openpyxl
python -m pytest tests\test_reports.py tests\test_exports.py
```

CSV używa UTF-8 z BOM i średnika. Nie zmieniaj kodowania na systemowe ANSI.
