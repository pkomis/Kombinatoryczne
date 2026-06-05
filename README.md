
# Bamboo Garden Trimming Simulator

Interaktywny symulator problemu Bamboo Garden Trimming (BGT), przepisany z React/Vite na aplikacje Python/Streamlit.

## Funkcje

* **Sandbox Mode:** eksperymentowanie z wlasnymi tempami wzrostu i algorytmami ciecia.
* **Compare Mode:** porownanie Reduce-Max, Reduce-Fastest(x) oraz Makespan-2 oracle na tym samym ogrodzie.
* **Game Mode:** gra przeciwko botowi Reduce-Max, z jednym cieciem na dzien.

## Tech stack

* Python
* Streamlit
* SVG generowane po stronie Pythona

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
