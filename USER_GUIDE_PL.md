# Instrukcja użytkownika — Kulturysta 0.1

## Ważne

Kulturysta jest narzędziem edukacyjnym, demonstracyjnym i treningowym. Wyniki nie stanowią diagnozy medycznej ani zalecenia klinicznego.

Platforma musi leżeć na stabilnym, płaskim podłożu. Każde ćwiczenie wymaga nadzoru i asekuracji. Przerwij ćwiczenie przy bólu, zawrotach głowy lub utracie równowagi. Nie uruchamiaj automatycznie próby jednonóż.

## Szybki start na zajęcia

1. Uruchom `python main.py`.
2. Na pokazie wybierz uczestnika i zaznacz tryb samego identyfikatora.
3. Wybierz `Symulator` → `Kołysanie sinusoidalne` → `Połącz`.
4. Sprawdź masę, COP i status połączenia.
5. Otwórz `Pomiar`, ustaw 30 s i protokół.
6. Kliknij `Start`; po odliczaniu pomiar zakończy się i zapisze automatycznie.
7. Otwórz zakładkę `Wyniki`, a w razie potrzeby utwórz PDF.
8. Po zajęciach kliknij `Rozłącz` i zamknij aplikację.

## Wybór backendu i połączenie

- `Symulator` działa bez platformy. Lista scenariuszy obejmuje stabilne stanie, kołysanie, przenoszenie ciężaru, zakłócenia, zejście, utratę połączenia, artefakt i nieregularne próbkowanie.
- `Wii Balance Board` wymaga zainstalowanego i sprawdzonego `wbb-module`.
- `Połącz` uruchamia połączenie poza głównym wątkiem. `Rozłącz` zatrzymuje worker i sterownik.
- `Zeruj` otwiera prowadzoną kalibrację programową. Najpierw przez 2 sekundy zbierane jest zero z pustej platformy; opcjonalnie można następnie podać znaną masę referencyjną. Aplikacja zapisuje parametry kalibracji i nadal zachowuje wartości surowe.

Start pomiaru jest nieaktywny bez połączenia lub wystarczającego obciążenia. Nie obchodź tej blokady.

## Uczestnik

W menu `Sesja → Uczestnik…` podaj identyfikator oraz wymagane dane. Identyfikator może zawierać litery, cyfry, `_` i `-`.

Na targach i pokazach zaznacz `Używaj wyłącznie identyfikatora`. Nie wpisuj imienia, nazwiska ani uwag. Dane są lokalne, ale nie są szyfrowane; jednostka odpowiada za uprawnienia, retencję i kopie zapasowe.

## Konfiguracja pomiaru

W `Sesja → Konfiguracja pomiaru…` ustaw czas, protokół, liczbę powtórzeń, przerwę, warunek oczu, pozycję stóp, notatkę i filtr. Dostępne są: brak filtra, średnia krocząca i filtr dolnoprzepustowy Butterwortha. Domyślny czas to 30 s.

Dostępne protokoły: stanie swobodne z oczami otwartymi/zamkniętymi, stopy razem, tandem, próba jednonóż z obowiązkowym nadzorem oraz sekwencja trzech prób.

## Pomiar

1. Połącz backend i sprawdź obciążenie.
2. W razie potrzeby opróżnij platformę i kliknij `Zeruj`.
3. Potwierdź instrukcję i bezpieczeństwo uczestnika.
4. Kliknij `Start` i poczekaj na 3–2–1.
5. Obserwuj COP, masę, częstotliwość, timer i jakość.
6. `Stop` lub czerwony `PRZERWIJ` kończy sesję z flagą wcześniejszego zatrzymania.
7. Po pełnym czasie następuje automatyczna analiza i zapis. Przy wielu powtórzeniach każda próba ma osobny katalog sesji, a aplikacja prowadzi przez przerwę i kolejne odliczanie.

Widok COP pokazuje bieżący punkt, ograniczoną ścieżkę, osie, cel, jednostkę i stan braku obciążenia. Pełne próbki nadal są zachowane w recorderze. Pomarańczowy punkt i komunikat oznaczają wyjście poza bieżącą skalę, a nie przycięcie danych w pliku.

## Trening

Wybierz jedno z siedmiu ćwiczeń i kliknij `Rozpocznij trening`. Zaakceptuj komunikat bezpieczeństwa. Domyślny czas to 60 s. Ekran pokazuje cel, COP, czas, procent czasu w celu i liczbę osiągniętych celów. Przycisk `Dźwięk` włącza lub wycisza krótki sygnał wejścia w cel.

Adaptacja jest deterministyczna:

- po wyniku powyżej 85% przez dwie rundy promień zmniejsza się o 10%;
- po wyniku poniżej 50% promień zwiększa się o 10%;
- promień pozostaje w bezpiecznych granicach 0,05–0,40 jednostki.

## Demo i minigra

Kliknij `Start / restart`. Zielony punkt jest sterowany przez COP, a żółty oznacza gwiazdkę. Sterowanie awaryjne działa strzałkami. Minigra działa offline, bez reklam, obcej grafiki i muzyki.

## Stop, Escape i pełny ekran

Czerwony `PRZERWIJ` bezpiecznie zatrzymuje aktywny tryb. `Escape` zatrzymuje pomiar/trening/demo i opuszcza pełny ekran. `F11` przełącza pełny ekran.

## Drugi monitor

Wybierz `Widok → Feedback na drugim ekranie`. Jeśli wykryto drugi ekran, otworzy się pełnoekranowy podgląd COP. Przy jednym ekranie aplikacja wyświetli informację i będzie działać normalnie.

## Wyniki i jakość

Zakładka `Wyniki` pokazuje parametry, ich wartości i jednostki. Klasyfikacja może być: `poprawna`, `poprawna_z_ostrzezeniami` lub `niewazna`. Flaga nie usuwa próby; operator podejmuje decyzję o jej wykorzystaniu.

Przykładowe flagi: brak połączenia, przerwa, zejście, niskie obciążenie, skok masy/COP, NaN/Inf, krótki pomiar, brak sensora, nieregularne próbkowanie i wcześniejszy Stop.

## Pliki i eksport

Każda sesja ma UUID i katalog `data/sessions/<id-sesji>/`:

- `samples.csv` — średnik, UTF-8 BOM, dane surowe i filtrowane;
- `session.xlsx` — Metadane, Dane surowe, Dane przetworzone, Wyniki, Jakość;
- `metadata.json` — pełne metadane;
- `report.md` — raport tekstowy;
- PDF — na żądanie z ekranu wyników, zapisywany również w `data/reports`.

W raportach używane są neutralne określenia. Nie zawierają diagnozy ani automatycznej oceny skuteczności.

## Porównanie sesji

1. Otwórz `Porównanie`.
2. Podaj identyfikator tej samej osoby.
3. Kliknij `Wczytaj sesje`.
4. Zaznacz co najmniej dwie sesje i wybierz `Porównaj zaznaczone`.

Widok nakłada stabilogramy i pokazuje trend długości ścieżki. Tabela pokazuje wartość, zmianę bezwzględną, procentową (gdy mianownik nie jest zerem) oraz neutralny kierunek: wzrost, spadek albo brak istotnej różnicy numerycznej.

## Bezpieczne zakończenie

Najpierw zatrzymaj aktywną sesję, kliknij `Rozłącz`, a następnie zamknij okno. Zamknięcie także próbuje bezpiecznie zatrzymać worker i backend. Nie wyłączaj komputera podczas zapisu XLSX/PDF.
