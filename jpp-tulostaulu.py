"""Kehityskäynnistys.

    flask --app jpp-tulostaulu run --debug --host=0.0.0.0

Tiedoston nimessä on väliviiva, joten sitä ei voi importata. Sovellus
rakennetaan siksi tehtaalla app/__init__.py:ssä, jota myös testit ja
tools/esikatselu.py käyttävät - näin reitit ovat varmasti samat kaikkialla.
"""

from app import luo_sovellus

app = luo_sovellus()


if __name__ == "__main__":
    app.run(debug=True)
