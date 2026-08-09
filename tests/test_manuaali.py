# tests/test_manuaali.py
"""Manuaalitaulun sovittimen testit.

Sovitin `app.manuaali.rakenna_tulostaulu` muuntaa kantarivin samaksi
`Tulostaulu`-olioksi kuin livetaulu rakentaa API-vastauksesta. Se on puhdas
funktio, joten testit eivät tarvitse tietokantaa - `tekaistu_rivi` jäljittelee
`Otteludata`-riviä.

Aja projektin juuresta:

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.manuaali import (  # noqa: E402
    VUOROPARI_JATKOPARIT,
    VUOROPARI_PAATTYNYT,
    rakenna_tulostaulu,
    vuoroparin_teksti,
)
from app.tulostaulu import KOTI, VIERAS  # noqa: E402


class TekaistuRivi:
    """Otteludata-rivin kaltainen olio ilman tietokantaa."""

    def __init__(self, **kentat):
        oletukset = {
            "ottelunumero": 512345,
            "pesistulokset": 0,
            "kotijoukkue": "Siilinjärven Pesis",
            "vierasjoukkue": "Puijon Pesis",
            "koti_jaksovoitot": 1,
            "vieras_jaksovoitot": 2,
            "jakso_1_koti_juoksut": 3,
            "jakso_1_vieras_juoksut": 4,
            "jakso_2_koti_juoksut": 5,
            "jakso_2_vieras_juoksut": 6,
            "jakso_3_koti_juoksut": None,
            "jakso_3_vieras_juoksut": None,
            "jakso_4_koti_juoksut": None,
            "jakso_4_vieras_juoksut": None,
            "nykyinen_lyontivuoro": "Siilinjärven Pesis",
            "jakso_nro": 1,
            "vuoropari_nro": 1,
            "palot": "XX",
            "otteluinfo": "",
        }
        oletukset.update(kentat)
        for nimi, arvo in oletukset.items():
            setattr(self, nimi, arvo)


def tekaistu_rivi(**kentat):
    return TekaistuRivi(**kentat)


class TestJaksot(unittest.TestCase):
    def test_jaksot_tulevat_sarakkeista(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi())
        self.assertEqual([j.otsikko for j in taulu.jaksot], ["1", "2", "S", "K"])
        self.assertEqual([j.koti for j in taulu.jaksot], [3, 5, None, None])
        self.assertEqual([j.vieras for j in taulu.jaksot], [4, 6, None, None])

    def test_aktiivinen_jakso(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi(jakso_nro=2))
        self.assertEqual([j.aktiivinen for j in taulu.jaksot], [False, True, False, False])

    def test_jaksovoitot(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi())
        self.assertEqual(taulu.koti_jaksovoitot, 1)
        self.assertEqual(taulu.vieras_jaksovoitot, 2)


class TestSisavuoro(unittest.TestCase):
    def test_koti_sisalla(self):
        taulu = rakenna_tulostaulu(
            tekaistu_rivi(nykyinen_lyontivuoro="Siilinjärven Pesis")
        )
        self.assertEqual(taulu.sisavuoro, KOTI)

    def test_vieras_sisalla(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi(nykyinen_lyontivuoro="Puijon Pesis"))
        self.assertEqual(taulu.sisavuoro, VIERAS)

    def test_tuntematon_nimi_ei_korosta_kumpaakaan(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi(nykyinen_lyontivuoro="-"))
        self.assertIsNone(taulu.sisavuoro)

    def test_tyhja_ei_korosta_kumpaakaan(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi(nykyinen_lyontivuoro=""))
        self.assertIsNone(taulu.sisavuoro)


class TestPalot(unittest.TestCase):
    def test_palot_ovat_lukumaara_ei_merkkijono(self):
        self.assertEqual(rakenna_tulostaulu(tekaistu_rivi(palot="XXX")).palot, 3)

    def test_tyhja(self):
        self.assertEqual(rakenna_tulostaulu(tekaistu_rivi(palot="")).palot, 0)

    def test_none(self):
        self.assertEqual(rakenna_tulostaulu(tekaistu_rivi(palot=None)).palot, 0)


class TestTilarivi(unittest.TestCase):
    def test_jakso_ja_vuoropari(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi(jakso_nro=1, vuoropari_nro=4))
        self.assertEqual(taulu.tilanne_txt, "1. jakso / 2. lopettava")

    def test_paattynyt_ottelu(self):
        taulu = rakenna_tulostaulu(
            tekaistu_rivi(jakso_nro=2, vuoropari_nro=VUOROPARI_PAATTYNYT)
        )
        self.assertEqual(taulu.tilanne_txt, "Ottelu on päättynyt")

    def test_otteluinfo_menee_omaan_soluunsa(self):
        taulu = rakenna_tulostaulu(tekaistu_rivi(otteluinfo="Sarjaottelu"))
        self.assertEqual(taulu.info_txt, "Sarjaottelu")

    def test_lahde(self):
        self.assertEqual(rakenna_tulostaulu(tekaistu_rivi()).lahde, "manuaali")


class TestVuoroparinTeksti(unittest.TestCase):
    """Manuaalitaulun 14-portainen valitsin käyttää samoja tekstejä kuin live."""

    def test_perusjaksot(self):
        self.assertEqual(vuoroparin_teksti(1), "1. aloittava")
        self.assertEqual(vuoroparin_teksti(2), "1. lopettava")
        self.assertEqual(vuoroparin_teksti(8), "4. lopettava")

    def test_supervuoro_ja_kotari_ilman_jarjestysnumeroa(self):
        # Aiemmin tässä luki "S. aloittava" ja "K. lopettava", vaikka
        # livetaulu näytti samassa tilanteessa pelkän "aloittava".
        self.assertEqual(vuoroparin_teksti(9), "aloittava")
        self.assertEqual(vuoroparin_teksti(10), "lopettava")
        self.assertEqual(vuoroparin_teksti(11), "aloittava")
        self.assertEqual(vuoroparin_teksti(12), "lopettava")

    def test_jatkoparit(self):
        self.assertEqual(vuoroparin_teksti(VUOROPARI_JATKOPARIT), "jatkoparit")

    def test_paattynyt_ei_ole_vuoropari(self):
        self.assertEqual(vuoroparin_teksti(VUOROPARI_PAATTYNYT), "")

    def test_tuntematon(self):
        self.assertEqual(vuoroparin_teksti(99), "")


class TestSamaTekstiKuinLivetaulussa(unittest.TestCase):
    """Sama tilanne näyttää samalta kummassakin taulussa."""

    def test_supervuoron_aloittava(self):
        from app.tulostaulu import vuoroparin_nimi

        self.assertEqual(vuoroparin_teksti(9), vuoroparin_nimi(3, 0, False))

    def test_toisen_jakson_lopettava(self):
        from app.tulostaulu import vuoroparin_nimi

        self.assertEqual(vuoroparin_teksti(4), vuoroparin_nimi(1, 1, True))


if __name__ == "__main__":
    unittest.main()
