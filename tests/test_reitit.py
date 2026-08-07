# tests/test_reitit.py
"""
Reittien ja tulostaulun renderöinnin savutestit.

HTTP-kutsut pesistulokset-API:in on korvattu paikallisella vastaajalla, joten
testit eivät tarvitse verkkoyhteyttä.

`config.py`:ssä on silti oltava `PESISTULOKSET_API_KEY`. Avain luetaan ennen
kuin mockattu `requests.get` ehtii vastata, joten ilman sitä reitit palauttavat
503:n ja testit kaatuvat. Avaimen arvolla ei ole väliä.

Aja projektin juuresta:

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_live import (  # noqa: E402
    OTTELU_129199,
    OTTELU_129209,
    TULOS_129209,
    kaynnissa_oleva_tulos,
)


def luo_sovellus():
    """Rakentaa Flask-sovelluksen samoin kuin jpp-tulostaulu.py.

    Varsinaista käynnistystiedostoa ei voi importata, koska sen nimessä on
    väliviiva.
    """
    from flask import Flask, render_template

    from app.routes import routes_bp

    app = Flask(__name__, template_folder='../app/templates', static_folder='../static')
    app.register_blueprint(routes_bp)

    @app.route("/")
    def jpp_tulostaulu():
        return render_template('index.html')

    return app


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def tee_vastaaja(ottelut, tulokset):
    """Palauttaa requests.get-korvaajan annetulla testidatalla."""

    def get(url, params=None, timeout=None):
        ottelunumero = int(params["id"])
        if url.endswith("/match"):
            if ottelunumero not in ottelut:
                return FakeResponse(None, 404)
            return FakeResponse(ottelut[ottelunumero])
        if url.endswith("/match-live-result"):
            return FakeResponse({"result": tulokset.get(ottelunumero)})
        raise AssertionError(f"Odottamaton URL: {url}")

    return get


class ReittiTesti(unittest.TestCase):
    ottelut = {129209: OTTELU_129209, 129199: OTTELU_129199}
    tulokset = {129209: TULOS_129209}

    def setUp(self):
        from app import pesistulokset_api

        pesistulokset_api.tyhjenna_valimuisti()

        # Ladataan sovellus vasta kun requests on korvattu
        self.patcher = mock.patch(
            "app.pesistulokset_api.requests.get",
            side_effect=tee_vastaaja(self.ottelut, self.tulokset),
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        app = luo_sovellus()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_paattynyt_ottelu_renderoityy(self):
        vastaus = self.client.get("/129209/tulostaulu")
        self.assertEqual(vastaus.status_code, 200)
        sisalto = vastaus.get_data(as_text=True)
        self.assertIn("Jussittaret, Seinäjoki", sisalto)
        self.assertIn("Lapuan Virkiä", sisalto)
        self.assertIn("Ottelu on päättynyt", sisalto)
        self.assertIn(">8<", sisalto)
        self.assertIn(">3<", sisalto)

    def test_alkamaton_ottelu_renderoityy(self):
        vastaus = self.client.get("/129199/tulostaulu")
        self.assertEqual(vastaus.status_code, 200)
        sisalto = vastaus.get_data(as_text=True)
        self.assertIn("Fera, Rauma", sisalto)
        self.assertIn("Ottelu ei ole alkanut", sisalto)

    def test_tuntematon_ottelu(self):
        vastaus = self.client.get("/999999")
        self.assertEqual(vastaus.status_code, 404)

    def test_widgetin_sivu_aukeaa(self):
        vastaus = self.client.get("/129209")
        self.assertEqual(vastaus.status_code, 200)
        sisalto = vastaus.get_data(as_text=True)
        self.assertIn("/129209/tulostaulu", sisalto)
        self.assertIn("scoreboard_default.css", sisalto)

    def test_tyyli_parametri(self):
        vastaus = self.client.get("/129209?style=siipe")
        self.assertIn("scoreboard_siipe.css", vastaus.get_data(as_text=True))

    def test_sisavuoro_korostuu_kaynnissa_olevassa_ottelussa(self):
        from app import pesistulokset_api

        pesistulokset_api.tyhjenna_valimuisti()
        self.patcher.stop()
        with mock.patch(
            "app.pesistulokset_api.requests.get",
            side_effect=tee_vastaaja(self.ottelut, {129209: kaynnissa_oleva_tulos()}),
        ):
            sisalto = self.client.get("/129209/tulostaulu").get_data(as_text=True)
        self.patcher.start()

        self.assertIn("sisavuoro", sisalto)
        self.assertIn("1. jakso / 2. lopettava", sisalto)
        self.assertIn("XX", sisalto)

    def test_valimuisti_rajoittaa_api_kutsuja(self):
        from app import pesistulokset_api

        pesistulokset_api.tyhjenna_valimuisti()
        kutsut = {"n": 0}
        vastaaja = tee_vastaaja(self.ottelut, self.tulokset)

        def laskeva(*args, **kwargs):
            kutsut["n"] += 1
            return vastaaja(*args, **kwargs)

        self.patcher.stop()
        with mock.patch("app.pesistulokset_api.requests.get", side_effect=laskeva):
            for _ in range(20):
                self.client.get("/129209/tulostaulu")
        self.patcher.start()

        # 20 selainpyyntöä -> korkeintaan yksi match- ja yksi live-result-kutsu
        self.assertLessEqual(kutsut["n"], 2)


if __name__ == "__main__":
    unittest.main()


class IlmanTietokantaaTesti(unittest.TestCase):
    """Livetaulun on toimittava, vaikka tietokantaa ei olisi lainkaan."""

    def setUp(self):
        from app import pesistulokset_api, routes
        from config import Config

        pesistulokset_api.tyhjenna_valimuisti()
        routes._tyhjenna_reititys()

        self.alkuperainen = getattr(Config, "MANUAALITAULU_KAYTOSSA", True)
        Config.MANUAALITAULU_KAYTOSSA = False
        self.addCleanup(
            setattr, Config, "MANUAALITAULU_KAYTOSSA", self.alkuperainen
        )
        self.addCleanup(routes._tyhjenna_reititys)

        patcher = mock.patch(
            "app.pesistulokset_api.requests.get",
            side_effect=tee_vastaaja(
                {129209: OTTELU_129209}, {129209: TULOS_129209}
            ),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        app = luo_sovellus()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_livetaulu_toimii(self):
        with mock.patch("app.db.get_db", side_effect=AssertionError("kantaa ei saa käyttää")):
            vastaus = self.client.get("/129209/tulostaulu")
        self.assertEqual(vastaus.status_code, 200)
        self.assertIn("Jussittaret", vastaus.get_data(as_text=True))

    def test_manuaalireitit_pois_kaytosta(self):
        self.assertEqual(self.client.get("/uusi").status_code, 404)
        self.assertEqual(self.client.get("/paivita/512345").status_code, 404)
