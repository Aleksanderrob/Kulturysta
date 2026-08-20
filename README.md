# Kulturysta

Kulturysta to całkowicie offline'owa aplikacja desktopowa do edukacyjnych pomiarów posturograficznych, treningu równowagi, biofeedbacku i demonstracji przenoszenia ciężaru z Nintendo Wii Balance Board. Interfejs jest po polsku, a pełny tryb symulacyjny działa bez sprzętu.

> **Narzędzie edukacyjne i treningowe. Wyniki nie stanowią diagnozy medycznej.**

## Funkcje wersji pilotażowej 0.1

- trzy tryby: pomiar, trening i demonstracja z minigrą „Zbieranie gwiazdek”;
- wspólny interfejs sprzętowy oraz adapter `wbb-module` odseparowany od GUI;
- osiem scenariuszy symulatora, w tym zejście, utrata połączenia, artefakt i nieregularne próbkowanie;
- strumieniowanie w `QThread`; blokujący odczyt nie działa w głównym wątku Qt;
- płynny widget COP z ograniczoną ścieżką, stałą lub łagodną autoskalą, celem i sygnalizacją wyjścia poza skalę;
- formularz uczestnika z trybem samego identyfikatora;
- pomiar 30 s, protokoły wielokrotnych prób z przerwami, odliczanie, automatyczne zakończenie i bezpieczny Stop;
- prowadzona kalibracja zerowa z opcjonalnym znanym obciążeniem i zachowaniem wartości surowych;
- wybór braku filtra, średniej kroczącej lub dolnoprzepustowego filtra Butterwortha;
- trening z siedmioma ćwiczeniami, opcjonalnym sygnałem celu i jawną regułą adaptacji;
- metryki bazujące na rzeczywistych timestampach i jawnej jednostce COP;
- kontrola jakości, która zachowuje dane i flagi zamiast je usuwać;
- CSV (`;`, UTF-8 BOM), XLSX (5 arkuszy), JSON, Markdown i PDF z wykresami;
- lokalne porównania sesji tej samej osoby, nałożone stabilogramy, trend oraz zmiany bezwzględne i procentowe;
- opcjonalny drugi ekran do pełnoekranowego feedbacku;
- notebook analityczny oraz diagnostyka sprzętu;
- 55 automatycznych testów niezależnych od sprzętu i oddzielny marker `hardware`.

## Szybkie uruchomienie symulatora

Python 3.12 jest wersją zalecaną na Windows 11.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python main.py
```

W aplikacji pozostaw `Symulator`, wybierz scenariusz, kliknij `Połącz`, a następnie wejdź na ekran pomiaru, treningu albo demo.

## Testy

```powershell
python -m pytest
python -m pytest -m hardware
python -m ruff check .
```

Domyślne `pytest` wyłącza testy wymagające fizycznej platformy.

## Najważniejsze katalogi

```text
app/          modele, konfiguracja, logowanie
hardware/     kontrakt, symulator, adapter wbb-module
acquisition/  worker Qt, recorder, kalibracja, filtry, jakość
analysis/     COP, metryki, porównania
biofeedback/  ćwiczenia, scoring i adaptacja
games/        minigry
ui/           polski interfejs PySide6
storage/      zapis, eksporty i raporty
tools/        diagnostyka sprzętu i inspekcja API
tests/        testy automatyczne i sprzętowe
```

## Prywatność i bezpieczeństwo

Dane są przechowywane lokalnie w `data/`. Projekt nie zapewnia szyfrowania, logowania użytkowników ani bazy danych. Administrator jednostki odpowiada za uprawnienia do katalogu, kopie zapasowe, retencję i zgodność z obowiązującymi zasadami prywatności. Na pokazach używaj trybu samego identyfikatora i nie zapisuj imienia, nazwiska ani uwag.

Ćwiczenia powinny odbywać się pod nadzorem, na stabilnym i płaskim podłożu, z asekuracją. Należy je przerwać przy bólu, zawrotach głowy lub utracie równowagi.

Szczegóły: [instalacja Windows](INSTALL_WINDOWS.md), [instrukcja użytkownika](USER_GUIDE_PL.md), [budowanie EXE](BUILD_EXE.md), [test manualny](MANUAL_TEST_CHECKLIST.md) i [stan techniczny](PROJECT_STATUS.md).
