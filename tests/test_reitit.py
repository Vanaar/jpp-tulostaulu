# tests/test_reitit.py
"""Reittien ja tulostaulun renderöinnin savutestit.

HTTP-kutsut pesistulokset-API:in on korvattu paikallisella vastaajalla ja
manuaalitaulun kantahaku tynkäfunktiolla, joten testit eivät tarvitse
verkkoyhteyttä eivätkä tietokantaa.

`config.py`:ssä on silti oltava `PESISTULOKSET_API_KEY`. Avain luetaan ennen
kuin mockattu `requests.get` ehtii vastata, joten ilman sitä reitit palauttavat
503:n ja testit kaatuvat. Avaimen arvolla ei ole väliä.

Sovellus rakennetaan tehtaalla `app.luo_sovellus`, samalla koodilla kuin
tuotannossa - reittejä ei siis tarvitse enää ylläpitää kahdessa paikassa.

Aja projektin juuresta:

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import luo_sovellus  # noqa: E402
from test_live import (  # noqa: E402
    OTTELU_129199,
    OTTELU_129209,
    TULOS_129209,
    kaynnissa_oleva_tulos,
)
from test_manuaali import tekaistu_rivi  # noqa: E402


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


def aseta_manuaalitaulu(testi, kaytossa):
    """Kytkee manuaalitaulun päälle tai pois testin ajaksi."""
    from config import Config

    alkuperainen = getattr(Config, "MANUAALITAULU_KAYTOSSA", True)
    Config.MANUAALITAULU_KAYTOSSA = kaytossa
    testi.addCleanup(setattr, Config, "MANUAALITAULU_KAYTOSSA", alkuperainen)


def tyhjenna_valimuistit(testi):
    from app import pesistulokset_api, routes

    pesistulokset_api.tyhjenna_valimuisti()
    routes.unohda_reititys()
    testi.addCleanup(routes.unohda_reititys)
    testi.addCleanup(pesistulokset_api.tyhjenna_valimuisti)


class LivetauluTesti(unittest.TestCase):
    """Livetaulu ilman manuaalitaulua: kantaan ei kosketa lainkaan."""

    ottelut = {129209: OTTELU_129209, 129199: OTTELU_129199}
    tulokset = {129209: TULOS_129209}

    def setUp(self):
        tyhjenna_valimuistit(self)
        aseta_manuaalitaulu(self, False)

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

    def test_tuntematon_tyyli_palautuu_oletukseen(self):
        # Tyyli päätyy suoraan <link href>:iin, joten se sallitaan vain
        # tunnetuista arvoista.
        vastaus = self.client.get("/129209?style=../../salainen")
        sisalto = vastaus.get_data(as_text=True)
        self.assertIn("scoreboard_default.css", sisalto)
        self.assertNotIn("salainen", sisalto)

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

    def test_palosarake_on_aina_olemassa(self):
        # Taulun leveys ei saa muuttua sisävuoron mukaan: widget on upotettu
        # ulkopuolisille sivuille, joissa leveyden heittely näkyy nykäyksenä.
        paattynyt = self.client.get("/129209/tulostaulu").get_data(as_text=True)
        self.assertEqual(paattynyt.count("class='palot'"), 2)

        from app import pesistulokset_api

        pesistulokset_api.tyhjenna_valimuisti()
        self.patcher.stop()
        with mock.patch(
            "app.pesistulokset_api.requests.get",
            side_effect=tee_vastaaja(self.ottelut, {129209: kaynnissa_oleva_tulos()}),
        ):
            kaynnissa = self.client.get("/129209/tulostaulu").get_data(as_text=True)
        self.patcher.start()

        self.assertEqual(kaynnissa.count("class='palot'"), 2)

    def test_palot_eivat_ole_html_merkkijono(self):
        # Palot piirretään templatessa X-merkkeinä; mallissa ne ovat luku.
        from app import pesistulokset_api

        pesistulokset_api.tyhjenna_valimuisti()
        self.patcher.stop()
        with mock.patch(
            "app.pesistulokset_api.requests.get",
            side_effect=tee_vastaaja(self.ottelut, {129209: kaynnissa_oleva_tulos()}),
        ):
            sisalto = self.client.get("/129209/tulostaulu").get_data(as_text=True)
        self.patcher.start()

        self.assertIn("<td class='palot'>XX</td>", sisalto)

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

    def test_kantaan_ei_kosketa(self):
        with mock.patch(
            "app.db.get_db", side_effect=AssertionError("kantaa ei saa käyttää")
        ):
            vastaus = self.client.get("/129209/tulostaulu")
        self.assertEqual(vastaus.status_code, 200)
        self.assertIn("Jussittaret", vastaus.get_data(as_text=True))

    def test_manuaalireitit_pois_kaytosta(self):
        self.assertEqual(self.client.get("/").status_code, 404)
        self.assertEqual(self.client.get("/uusi").status_code, 404)
        self.assertEqual(self.client.get("/paivita/512345").status_code, 404)


class ManuaalitauluTesti(unittest.TestCase):
    """Manuaalitaulu renderöityy samasta templatesta kuin livetaulu.

    Kantahaku on korvattu tynkäfunktiolla, joten testi ei tarvitse MySQL:ää.
    """

    def setUp(self):
        tyhjenna_valimuistit(self)
        aseta_manuaalitaulu(self, True)

        self.rivi = tekaistu_rivi()
        self.haut = {"n": 0}

        def hae(ottelunumero):
            self.haut["n"] += 1
            return self.rivi if ottelunumero == self.rivi.ottelunumero else None

        patcher = mock.patch("app.manuaali.hae_ottelurivi", side_effect=hae)
        patcher.start()
        self.addCleanup(patcher.stop)

        app = luo_sovellus()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_manuaalitaulu_renderoityy(self):
        vastaus = self.client.get("/512345/tulostaulu")
        self.assertEqual(vastaus.status_code, 200)
        sisalto = vastaus.get_data(as_text=True)
        self.assertIn("Siilinjärven Pesis", sisalto)
        self.assertIn("Puijon Pesis", sisalto)
        self.assertIn("1. jakso / 1. aloittava", sisalto)

    def test_sisavuoro_korostuu(self):
        sisalto = self.client.get("/512345/tulostaulu").get_data(as_text=True)
        self.assertIn("sisavuoro", sisalto)

    def test_palot_naytetaan_x_merkkeina(self):
        sisalto = self.client.get("/512345/tulostaulu").get_data(as_text=True)
        self.assertIn("<td class='palot'>XX</td>", sisalto)

    def test_debug_rivi_kertoo_lahteen(self):
        sisalto = self.client.get("/512345/tulostaulu?debug=on").get_data(as_text=True)
        self.assertIn("Manuaalinen", sisalto)

    def test_manuaaliottelu_haetaan_joka_pyynnolla(self):
        # Manuaalitaulun tiedot muuttuvat, joten rivi on haettava uudelleen.
        for _ in range(5):
            self.client.get("/512345/tulostaulu")
        self.assertEqual(self.haut["n"], 5)

    def test_liveottelun_reitityspaatos_valimuistitetaan(self):
        # Livetaulun ei pidä kysellä kannasta joka päivityksellä.
        with mock.patch(
            "app.pesistulokset_api.requests.get",
            side_effect=tee_vastaaja({129209: OTTELU_129209}, {129209: TULOS_129209}),
        ):
            for _ in range(20):
                self.client.get("/129209/tulostaulu")
        self.assertEqual(self.haut["n"], 1)

    def test_manuaalireitit_ovat_kaytossa(self):
        self.assertEqual(self.client.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
