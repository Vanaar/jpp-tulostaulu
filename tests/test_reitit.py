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
    OTTELU_146447,
    TULOS_129209,
    TULOS_146447,
    kaynnissa_oleva_tulos,
)


def luo_sovellus():
    """Rakentaa Flask-sovelluksen samoin kuin jpp-tulostaulu.py.

    Varsinaista käynnistystiedostoa ei voi importata, koska sen nimessä on
    väliviiva. Reitit tulevat blueprintistä, joten niitä ei tarvitse enää
    muistaa määritellä kahteen kertaan; polut sen sijaan pitää.
    """
    from flask import Flask

    from app.routes import routes_bp

    app = Flask(__name__, template_folder='../app/templates', static_folder='../static')
    app.register_blueprint(routes_bp)

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

    def test_kokoparametri(self):
        sisalto = self.client.get("/129209?koko=2").get_data(as_text=True)
        self.assertIn("zoom: 2", sisalto)

    def test_oletuskoossa_ei_zoomia(self):
        for polku in ("/129209", "/129209?koko=1", "/129209?koko=roska"):
            with self.subTest(polku=polku):
                self.assertNotIn("zoom", self.client.get(polku).get_data(as_text=True))

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


class JuurisivuTesti(unittest.TestCase):
    """/ on ottelunumeron avauslomake, ei hallintakäyttöliittymä.

    Tarkistus tehdään palvelimella, jotta lomake toimii myös ilman
    JavaScriptiä.
    """

    def setUp(self):
        app = luo_sovellus()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_lomake_naytetaan(self):
        vastaus = self.client.get("/")
        self.assertEqual(vastaus.status_code, 200)
        sisalto = vastaus.get_data(as_text=True)
        self.assertIn('name="ottelunumero"', sisalto)
        self.assertIn("Avaa tulostaulu", sisalto)

    def test_kelvollinen_numero_ohjaa(self):
        vastaus = self.client.get("/?ottelunumero=129209")
        self.assertEqual(vastaus.status_code, 302)
        self.assertTrue(vastaus.headers["Location"].endswith("/129209"))

    def test_etunollat_karsiutuvat(self):
        vastaus = self.client.get("/?ottelunumero=007")
        self.assertEqual(vastaus.status_code, 302)
        self.assertTrue(vastaus.headers["Location"].endswith("/7"))

    def test_valilyonnit_trimmataan(self):
        vastaus = self.client.get("/?ottelunumero=%20129209%20")
        self.assertEqual(vastaus.status_code, 302)
        self.assertTrue(vastaus.headers["Location"].endswith("/129209"))

    def test_roskasyote_ei_ohjaa(self):
        for syote in ("abc", "", "12a", "-5", "1.5"):
            with self.subTest(syote=syote):
                vastaus = self.client.get(f"/?ottelunumero={syote}")
                self.assertEqual(vastaus.status_code, 200)
                self.assertIn("Anna ottelunumero numeroina.",
                              vastaus.get_data(as_text=True))

    def test_syote_palautetaan_kenttaan_eskaapattuna(self):
        # Virheellinen syöte kaiutetaan takaisin value-attribuuttiin, joten
        # Jinjan autoescapen on hoidettava lainausmerkit.
        vastaus = self.client.get('/?ottelunumero=%22%3E%3Cscript%3E')
        sisalto = vastaus.get_data(as_text=True)
        self.assertIn('value="&#34;&gt;&lt;script&gt;"', sisalto)
        self.assertNotIn('value=""><script>', sisalto)

    def test_lomake_ohittaa_selaimen_oman_tarkistuksen(self):
        # Ilman novalidatea pattern-attribuutti estäisi lähetyksen ennen
        # submit-käsittelijää, jolloin oma suomenkielinen virheviesti ei
        # koskaan näkyisi.
        sisalto = self.client.get("/").get_data(as_text=True)
        self.assertIn("novalidate", sisalto)
        self.assertIn('pattern="[0-9]*"', sisalto)

    def test_manuaalitaulun_linkkeja_ei_ole(self):
        sisalto = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("/uusi", sisalto)
        self.assertNotIn("/paivita", sisalto)


class VuoroparipeliTesti(unittest.TestCase):
    """Taulun muoto tulee datasta: vuoroparipelissä ei piirretä jaksoja."""

    def setUp(self):
        from app import pesistulokset_api

        pesistulokset_api.tyhjenna_valimuisti()

        patcher = mock.patch(
            "app.pesistulokset_api.requests.get",
            side_effect=tee_vastaaja(
                {146447: OTTELU_146447}, {146447: TULOS_146447}
            ),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        app = luo_sovellus()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_sarakkeina_vuoroparit(self):
        sisalto = self.client.get("/146447/tulostaulu").get_data(as_text=True)

        # Kaksi vuoroparisaraketta, ei S- tai K-saraketta
        self.assertIn('class="otsikko">1<', sisalto)
        self.assertIn('class="otsikko">2<', sisalto)
        self.assertNotIn('class="otsikko">S<', sisalto)
        self.assertNotIn('class="otsikko">K<', sisalto)

    def test_juoksut_ja_lopputulos_naytetaan(self):
        sisalto = self.client.get("/146447/tulostaulu").get_data(as_text=True)

        self.assertIn("Kauhajoen Karhu", sisalto)
        # Vuoroparit 8-7 ja 9-7, yhteensä 17-14
        self.assertIn('class="total-points">17<', sisalto)
        self.assertIn('class="total-points">14<', sisalto)
        self.assertIn("Ottelu on päättynyt", sisalto)
        self.assertIn("Vuoroparipeli", sisalto)


class AsetusTesti(unittest.TestCase):
    """Puuttuva config.py-asetus ei saa kaataa sovellusta.

    19.8.2026 tuotannon config.py:stä puuttui DEBUG_LEVEL, jonka
    debug_message luki suoraan Configista. Syntynyt AttributeError kaatoi
    jokaisen tulostaulun. Kaikki asetukset luetaan siksi getattrin läpi.
    """

    def test_debug_message_ilman_debug_levelia(self):
        from app.functions import debug_message
        from config import Config

        alkuperainen_debug = getattr(Config, "DEBUG", False)
        oli_level = hasattr(Config, "DEBUG_LEVEL")
        alkuperainen_level = getattr(Config, "DEBUG_LEVEL", None)

        Config.DEBUG = True
        if oli_level:
            del Config.DEBUG_LEVEL

        def palauta():
            Config.DEBUG = alkuperainen_debug
            if oli_level:
                Config.DEBUG_LEVEL = alkuperainen_level

        self.addCleanup(palauta)

        debug_message("testi")

    def test_debug_message_ilman_debugia(self):
        from app.functions import debug_message
        from config import Config

        oli_debug = hasattr(Config, "DEBUG")
        alkuperainen = getattr(Config, "DEBUG", None)
        if oli_debug:
            del Config.DEBUG

        def palauta():
            if oli_debug:
                Config.DEBUG = alkuperainen

        self.addCleanup(palauta)

        debug_message("testi")


class EiTietokantaaTesti(unittest.TestCase):
    """Regressiovahti: tietokantaa ei ole eikä sitä saa tulla takaisin.

    4.0:ssa manuaalitaulu ja koko kantariippuvuus poistettiin. Aiemmin sama
    testi varmisti vain, ettei kantaa käytetä; nyt varmistetaan ettei sitä
    ole olemassakaan.
    """

    def setUp(self):
        from app import pesistulokset_api

        pesistulokset_api.tyhjenna_valimuisti()

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

    def test_kantamoduulia_ei_ole(self):
        with self.assertRaises(ModuleNotFoundError):
            import app.db  # noqa: F401

    def test_sqlalchemyta_ei_ladata(self):
        vastaus = self.client.get("/129209/tulostaulu")
        self.assertEqual(vastaus.status_code, 200)
        self.assertIn("Jussittaret", vastaus.get_data(as_text=True))
        self.assertNotIn("sqlalchemy", sys.modules)

    def test_manuaalireitteja_ei_ole(self):
        self.assertEqual(self.client.get("/uusi").status_code, 404)
        self.assertEqual(self.client.get("/paivita/512345").status_code, 404)


if __name__ == "__main__":
    unittest.main()
