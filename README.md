
# Bamboo Garden Trimming Simulator

Interaktywny symulator problemu Bamboo Garden Trimming (BGT), przepisany z React/Vite na aplikacje Python/Streamlit.

## Funkcje

* **Sandbox Mode:** eksperymentowanie z wlasnymi tempami wzrostu i algorytmami ciecia.
* **Compare Mode:** porownanie Reduce-Max, Reduce-Fastest(x) oraz harmonogramu Makespan-2 na tym samym ogrodzie, z szybkim eksperymentem, wykresem i eksportem CSV/SVG.
* **Game Mode:** gra przeciwko botowi Reduce-Max, z jednym cieciem na dzien.

## Tech stack

* Python
* Streamlit
* SVG generowane po stronie Pythona

## Struktura projektu

```text
app.py                 # punkt wejscia aplikacji
bgt/
  core.py              # model i czysta logika symulacji
  algorithms.py        # algorytmy wyboru bambusa
  config.py            # presety i stale
  visuals.py           # generowanie SVG
  ui/
    theme.py           # konfiguracja strony i CSS
    components.py      # wspolne komponenty Streamlit
    sandbox.py         # tryb Sandbox
    compare.py         # tryb Compare
    game.py            # tryb Game
tests/                 # testy logiki niezaleznej od UI
```

Harmonogram Makespan-2 korzysta z redukcji opisanej przez Bilo i wsp.:
normalizuje tempa wzrostu, zaokragla je w dol do poteg `1/2`, a nastepnie
dopelnia instancje dyadyczna do sumy `1` i buduje drzewo wirtualnych bambusow.
Kazdy wezel wewnetrzny harmonogramuje swoje dzieci jako przeskalowana
instancje regularna. Daje to makespan co najwyzej `2` dla instancji o sumie
temp rownej `1`.

## Uruchomienie lokalne

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Aplikacja bedzie dostepna pod adresem pokazanym przez Streamlit, zwykle `http://localhost:8501`.

## Testy

```bash
python -m unittest
```
