# Ocena zastanego środowiska i stan weryfikacji

## Audyt wejściowy

- katalog projektu był pusty i nie był lokalnym repozytorium Git;
- utworzono prywatne repozytorium `Aleksanderrob/Kulturysta`;
- na komputerze wykonawczym nie znaleziono `wii-board-module`, `wbb-module` ani `WBB_Rehab`;
- lokalny interpreter to Python 3.14.5 na macOS, nie docelowy Windows 11/Python 3.12;
- fizyczna Wii Balance Board nie była dostępna;
- lokalnie zainstalowano zależności w `.venv` i potwierdzono zgodność testowanego stosu także z Pythonem 3.14.5; nie zastępuje to testu na Windows/Python 3.12.

## Rzeczywiste API `wbb-module`

Nie było możliwe uczciwe opisanie rzeczywistych sygnatur, ponieważ kod i pakiet `wbb-module` nie są dostępne na tym komputerze. Z wymagań wejściowych potwierdzone są wyłącznie wskazówki: import `from wbb import BalanceBoard` oraz nazwy `connect()`, `tare()`, `stream()` i pola `weight`, `cop_x`, `cop_y`.

`WiiBoardAdapter`:

- domyślnie używa tylko tych trzech wskazanych operacji;
- przed wywołaniem sprawdza, czy metoda istnieje;
- wykrywa opcjonalne zatrzymanie/rozłączenie bez uznawania go za gwarantowane;
- pozostawia jednostkę COP jako `unknown`, dopóki dokumentacja sterownika jej nie potwierdzi;
- przyjmuje `driver_factory` i mapę metod, dlatego może być testowany mockiem i dostosowany po audycie sterownika bez zmian GUI.

Na komputerze docelowym najpierw uruchom:

```powershell
python tools\inspect_wbb_api.py
python tools\hardware_diagnostics.py --cop-unit unknown --interactive
```

Wynik pierwszego polecenia jest źródłem faktów do ostatecznej konfiguracji adaptera i instrukcji parowania.

## Stan potwierdzony automatycznie

- 55 testów zaliczonych, 1 test sprzętowy odseparowany przez marker;
- tworzenie głównego okna i wszystkich pięciu ekranów;
- strumień symulatora przez `QThread`;
- krótka sesja od startu do automatycznego zakończenia i zapisu oraz sekwencja dwóch oddzielnych prób;
- CSV, XLSX, JSON, Markdown i PDF;
- wszystkie scenariusze symulatora, metryki, filtracja, jakość, kalibracja zerowa/referencyjna, porównanie stabilogramów i mock adaptera;
- uruchomienie `main.py --smoke-test` w trybie offscreen.

## Niepotwierdzone poza tym środowiskiem

- fizyczne połączenie i kierunki COP na Wii Balance Board;
- jednostka i zakres COP z lokalnego `wbb-module`;
- dokładne skrypty i procedura parowania tego modułu;
- zachowanie na dwóch fizycznych monitorach;
- Windows 11 i wynikowy plik EXE.

EXE nie może zostać zbudowany wiarygodnie na macOS. Dostarczono deterministyczny skrypt Windows, który najpierw wymaga 100% przejścia testów i dopiero wtedy tworzy preferowaną dystrybucję one-folder.
