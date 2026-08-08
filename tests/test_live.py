# tests/test_live.py
"""
Livetaulun mappauksen testit.

Aja projektin juuresta:

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.live import (  # noqa: E402
    joukkueen_nimi,
    paattele_lyova_joukkue,
    rakenna_ottelu,
    vuoroparin_teksti,
)


# --- Testidata ---------------------------------------------------------------

# Ottelu 129209, pelattu kokonaan, lopputulos 2-0 (8-3, 6-2)
OTTELU_129209 = {
    "id": 129209,
    "canceled": False,
    "started": True,
    "details": {"inning_count": 4},
    "meta": {"first_bat_turns": [16811, 16810, None, None]},
    "home": {"id": 16810, "name": "Jussittaret, Seinäjoki", "shorthand": "Jussittaret"},
    "away": {"id": 16811, "name": "Lapuan Virkiä", "shorthand": "Virkiä"},
}

TULOS_129209 = {
    "periods": {"home": 2, "away": 0},
    "runs": [
        {"home": [3, 2, 3, None], "away": [0, 1, 2, 0]},
        {"home": [0, 2, 0, 4], "away": [1, 1, 0, 0]},
        {"home": [None], "away": [None]},
        {"home": [None], "away": [None]},
    ],
    "outCount": 3,
    "currentPeriod": 1,
    "currentInning": 3,
    "batTurn": 1,
    "batTurnTeamKey": "away",
    "finished": True,
    "isPeriodMatch": True,
}

# Ottelu 129199, ei ole vielä alkanut -> live-result palauttaa {"result": null}
OTTELU_129199 = {
    "id": 129199,
    "canceled": False,
    "started": False,
    "details": {"inning_count": 4},
    "meta": {"first_bat_turns": [None, None, None, None]},
    "home": {"id": 16807, "name": "Fera, Rauma", "shorthand": "Fera"},
    "away": {"id": 16809, "name": "Jyväskylän Kirittäret", "shorthand": "Kirittäret"},
}


# Ottelu 146541, ratkesi SUPERVUOROON. Oikeaa API-dataa 8.8.2026.
# Jaksot menivät 1-1 (6-4, 2-4), supervuoro 1-0 kotijoukkueelle.
# Kotiutuskisaa ei pelattu, joten runs[3] on tyhjä.
OTTELU_146541 = {
    "id": 146541,
    "canceled": False,
    "started": True,
    "details": {"inning_count": 4, "draw_of_choice_winner": "away"},
    "meta": {
        "first_bat_turns": [16942, 16910, 16942, 16942],
        "super_inning_in_use": True,
    },
    "home": {"id": 16910, "name": "Ikaalisten Tarmo", "shorthand": "Tarmo"},
    "away": {"id": 16942, "name": "Haapajärven Pesä-Kiilat", "shorthand": "Pesä-Kiilat"},
}

TULOS_146541 = {
    "periods": {"home": 2, "away": 1},
    "runs": [
        {"home": [5, 0, 1, None], "away": [1, 1, 2, 0]},
        {"home": [0, 1, 0, 1], "away": [2, 2, 0, None]},
        {"home": [1], "away": [0]},
        {"home": [None], "away": [None]},
    ],
    "outCount": 2,
    "currentPeriod": 2,
    "currentInning": 0,
    "batTurn": 1,
    "batTurnTeamKey": "home",
    "finished": True,
    "isPeriodMatch": True,
}

# Ottelu 127482, ratkesi KOTIUTUSKISAAN. Oikeaa API-dataa 8.8.2026.
# Jaksot 1-1 (4-0, 3-4), supervuoro 0-0 tasan, kotiutuskisa 1-2 vieraalle.
OTTELU_127482 = {
    "id": 127482,
    "canceled": False,
    "started": True,
    "details": {"inning_count": 4, "draw_of_choice_winner": "away"},
    "meta": {
        "first_bat_turns": [14284, 14286, 14286, 14286],
        "super_inning_in_use": True,
    },
    "home": {"id": 14286, "name": "Imatran Pallo-Veikot", "shorthand": "IPV"},
    "away": {"id": 14284, "name": "Haminan Palloilijat", "shorthand": "HaPa"},
}

TULOS_127482 = {
    "periods": {"home": 1, "away": 2},
    "runs": [
        {"home": [3, 0, 1, None], "away": [0, 0, 0, 0]},
        {"home": [0, 0, 2, 1], "away": [0, 3, 1, None]},
        {"home": [0], "away": [0]},
        {"home": [1], "away": [2]},
    ],
    "outCount": 0,
    "currentPeriod": 3,
    "currentInning": 0,
    "batTurn": 1,
    "batTurnTeamKey": "away",
    "finished": True,
    "isPeriodMatch": True,
}


def kaynnissa_oleva_tulos():
    """Keksitty tilanne: 1. jakso, 2. vuoropari, koti lyömässä lopettavana.

    currentPeriod on -1, koska se kertoo viimeksi PÄÄTTYNEEN jakson indeksin:
    1. jaksossa yhtään jaksoa ei ole vielä päättynyt. Todennettu oikealla
    datalla 8.8.2026 (ottelut 130345, 131618, 130446, 130487).
    """
    return {
        "periods": {"home": 0, "away": 0},
        "runs": [
            {"home": [1, None, None, None], "away": [2, None, None, None]},
            {"home": [None, None, None, None], "away": [None, None, None, None]},
            {"home": [None], "away": [None]},
            {"home": [None], "away": [None]},
        ],
        "outCount": 2,
        "currentPeriod": -1,
        "currentInning": 1,
        "batTurn": 1,
        "batTurnTeamKey": "home",
        "finished": False,
        "isPeriodMatch": True,
    }


class TestJoukkueenNimi(unittest.TestCase):
    def test_lyhyt_nimi_kaytetaan_kokonaisena(self):
        # "Lapuan Virkiä" on 13 merkkiä
        self.assertEqual(joukkueen_nimi(OTTELU_129209["away"], "Vieras"), "Lapuan Virkiä")

    def test_pitka_nimi_lyhennetaan(self):
        # "Jussittaret, Seinäjoki" on 22 merkkiä -> mahtuu
        self.assertEqual(
            joukkueen_nimi(OTTELU_129209["home"], "Koti"), "Jussittaret, Seinäjoki"
        )

    def test_yli_25_merkkia_kaytetaan_lyhennetta(self):
        joukkue = {"name": "Kiteen Pallo-90 Junioritiimi", "shorthand": "KiPa-90"}
        self.assertEqual(joukkueen_nimi(joukkue, "Koti"), "KiPa-90")

    def test_puuttuva_joukkue(self):
        self.assertEqual(joukkueen_nimi(None, "Koti"), "Koti")


class TestPaattynytOttelu(unittest.TestCase):
    def setUp(self):
        self.ottelu = rakenna_ottelu(129209, OTTELU_129209, TULOS_129209)

    def test_jaksovoitot(self):
        self.assertEqual(self.ottelu.koti_jaksovoitot, 2)
        self.assertEqual(self.ottelu.vieras_jaksovoitot, 0)

    def test_jaksojen_juoksut(self):
        # Lopputulos API:n mukaan: 2-0 (8-3, 6-2)
        self.assertEqual(self.ottelu.jakso_1_koti_juoksut, 8)
        self.assertEqual(self.ottelu.jakso_1_vieras_juoksut, 3)
        self.assertEqual(self.ottelu.jakso_2_koti_juoksut, 6)
        self.assertEqual(self.ottelu.jakso_2_vieras_juoksut, 2)

    def test_pelaamattomat_jaksot_ovat_tyhjia(self):
        self.assertIsNone(self.ottelu.jakso_3_koti_juoksut)
        self.assertIsNone(self.ottelu.jakso_3_vieras_juoksut)
        self.assertIsNone(self.ottelu.jakso_4_koti_juoksut)
        self.assertIsNone(self.ottelu.jakso_4_vieras_juoksut)

    def test_tilateksti(self):
        self.assertEqual(self.ottelu.jakso_txt, "Ottelu on päättynyt")
        self.assertEqual(self.ottelu.vuoropari_txt, "")

    def test_ei_sisavuoroa_eika_paloja(self):
        # batTurn ja outCount jäävät API:ssa viimeiseen tilaansa, mutta
        # päättyneessä ottelussa ei ole sisävuoroa -> ei korostusta, ei paloja.
        self.assertEqual(self.ottelu.nykyinen_lyontivuoro, "-")
        self.assertEqual(self.ottelu.palot, "")

    def test_joukkueiden_nimet(self):
        self.assertEqual(self.ottelu.kotijoukkue, "Jussittaret, Seinäjoki")
        self.assertEqual(self.ottelu.vierasjoukkue, "Lapuan Virkiä")


class TestAlkamatonOttelu(unittest.TestCase):
    def setUp(self):
        self.ottelu = rakenna_ottelu(129199, OTTELU_129199, None)

    def test_otteluinfo(self):
        self.assertEqual(self.ottelu.otteluinfo, "Ottelu ei ole alkanut")

    def test_nimet_haetaan_silti(self):
        self.assertEqual(self.ottelu.kotijoukkue, "Fera, Rauma")
        self.assertEqual(self.ottelu.vierasjoukkue, "Jyväskylän Kirittäret")

    def test_tulokset_tyhjia(self):
        self.assertIsNone(self.ottelu.jakso_1_koti_juoksut)
        self.assertIsNone(self.ottelu.koti_jaksovoitot)
        self.assertEqual(self.ottelu.palot, "")
        self.assertEqual(self.ottelu.nykyinen_lyontivuoro, "-")


class TestKaynnissaOlevaOttelu(unittest.TestCase):
    def setUp(self):
        self.ottelu = rakenna_ottelu(129209, OTTELU_129209, kaynnissa_oleva_tulos())

    def test_lyova_joukkue(self):
        self.assertEqual(self.ottelu.nykyinen_lyontivuoro, self.ottelu.kotijoukkue)

    def test_jakso_ja_vuoropari(self):
        self.assertEqual(self.ottelu.jakso_nro, 1)
        self.assertEqual(self.ottelu.jakso_txt, "1. jakso")
        self.assertEqual(self.ottelu.vuoropari_txt, "2. lopettava")

    def test_palot(self):
        self.assertEqual(self.ottelu.palot, "XX")

    def test_alkanut_jakso_nollana_alkamaton_tyhjana(self):
        self.assertEqual(self.ottelu.jakso_1_koti_juoksut, 1)
        self.assertEqual(self.ottelu.jakso_1_vieras_juoksut, 2)
        self.assertIsNone(self.ottelu.jakso_2_koti_juoksut)
        self.assertIsNone(self.ottelu.jakso_3_koti_juoksut)


class TestSupervuoroOttelu(unittest.TestCase):
    """Ottelu 146541, oikeaa dataa: jaksot 1-1, supervuoro ratkaisi."""

    def setUp(self):
        self.ottelu = rakenna_ottelu(146541, OTTELU_146541, TULOS_146541)

    def test_jaksojen_juoksut(self):
        self.assertEqual(self.ottelu.jakso_1_koti_juoksut, 6)
        self.assertEqual(self.ottelu.jakso_1_vieras_juoksut, 4)
        self.assertEqual(self.ottelu.jakso_2_koti_juoksut, 2)
        self.assertEqual(self.ottelu.jakso_2_vieras_juoksut, 4)

    def test_supervuoron_juoksut(self):
        self.assertEqual(self.ottelu.jakso_3_koti_juoksut, 1)
        self.assertEqual(self.ottelu.jakso_3_vieras_juoksut, 0)

    def test_pelaamaton_kotiutuskisa_on_tyhja(self):
        # Tämä kaatuisi, jos päättyneessä ottelussa jaksoindeksiin lisättäisiin
        # yksi: kotiutuskisa merkittäisiin alkaneeksi ja näyttäisi nollaa.
        self.assertIsNone(self.ottelu.jakso_4_koti_juoksut)
        self.assertIsNone(self.ottelu.jakso_4_vieras_juoksut)

    def test_jaksovoitot_sisaltavat_supervuoron(self):
        self.assertEqual(self.ottelu.koti_jaksovoitot, 2)
        self.assertEqual(self.ottelu.vieras_jaksovoitot, 1)

    def test_tilateksti(self):
        self.assertEqual(self.ottelu.jakso_txt, "Ottelu on päättynyt")
        self.assertEqual(self.ottelu.nykyinen_lyontivuoro, "-")


class TestKotiutuskisaOttelu(unittest.TestCase):
    """Ottelu 127482, oikeaa dataa: supervuoro 0-0, kotiutuskisa ratkaisi."""

    def setUp(self):
        self.ottelu = rakenna_ottelu(127482, OTTELU_127482, TULOS_127482)

    def test_kaikki_sarakkeet(self):
        self.assertEqual(self.ottelu.jakso_1_koti_juoksut, 4)
        self.assertEqual(self.ottelu.jakso_1_vieras_juoksut, 0)
        self.assertEqual(self.ottelu.jakso_2_koti_juoksut, 3)
        self.assertEqual(self.ottelu.jakso_2_vieras_juoksut, 4)
        self.assertEqual(self.ottelu.jakso_3_koti_juoksut, 0)
        self.assertEqual(self.ottelu.jakso_3_vieras_juoksut, 0)
        self.assertEqual(self.ottelu.jakso_4_koti_juoksut, 1)
        self.assertEqual(self.ottelu.jakso_4_vieras_juoksut, 2)

    def test_tasan_mennyt_supervuoro_naytetaan_nollana(self):
        # 0-0 ei ole sama kuin pelaamaton: sarake ei saa jäädä tyhjäksi
        self.assertIsNotNone(self.ottelu.jakso_3_koti_juoksut)

    def test_jaksovoitot_sisaltavat_kotiutuskisan(self):
        self.assertEqual(self.ottelu.koti_jaksovoitot, 1)
        self.assertEqual(self.ottelu.vieras_jaksovoitot, 2)

    def test_kotiutuskisan_aloittaja_on_supervuoron_aloittaja(self):
        # Pelisäännöt 8 §. Molemmissa oikeissa otteluissa indeksit 2 ja 3 ovat
        # samat, eikä aloittajaa siksi saa päätellä vuorottelemalla.
        listat = (
            OTTELU_127482["meta"]["first_bat_turns"],
            OTTELU_146541["meta"]["first_bat_turns"],
        )
        for lista in listat:
            self.assertEqual(lista[2], lista[3])


class TestKaynnissaOlevaSupervuoro(unittest.TestCase):
    """Supervuoroa ei ole nähty livenä; tämä lukitsee johdetun käytöksen.

    currentPeriod 1 = jakso 2 on päättynyt -> menossa on supervuoro (jakso 3).
    """

    def _tulos(self, super_runs, inning=0, bat_turn=0):
        return {
            "periods": {"home": 1, "away": 1},
            "runs": [
                {"home": [5, 0, 1, None], "away": [1, 1, 2, 0]},
                {"home": [0, 1, 0, 1], "away": [2, 2, 0, None]},
                super_runs,
                {"home": [None], "away": [None]},
            ],
            "outCount": 1,
            "currentPeriod": 1,
            "currentInning": inning,
            "batTurn": bat_turn,
            "batTurnTeamKey": "away",
            "finished": False,
            "isPeriodMatch": True,
        }

    def test_tauko_ennen_supervuoroa(self):
        # Supervuoro ei ole alkanut -> jaksotauko: ei vuoroparia, ei paloja
        tulos = self._tulos({"home": [None], "away": [None]})
        ottelu = rakenna_ottelu(146541, OTTELU_146541, tulos)
        self.assertEqual(ottelu.jakso_txt, "Supervuoro")
        self.assertEqual(ottelu.vuoropari_txt, "")
        self.assertEqual(ottelu.palot, "")

    def test_supervuoro_kaynnissa(self):
        # Supervuorossa on vain yksi vuoropari, joten numeroa ei näytetä
        tulos = self._tulos({"home": [0], "away": [None]}, bat_turn=1)
        ottelu = rakenna_ottelu(146541, OTTELU_146541, tulos)
        self.assertEqual(ottelu.jakso_txt, "Supervuoro")
        self.assertEqual(ottelu.vuoropari_txt, "lopettava")
        self.assertEqual(ottelu.nykyinen_lyontivuoro, ottelu.vierasjoukkue)
        self.assertEqual(ottelu.palot, "X")

    def test_kotiutuskisa_kaynnissa(self):
        # currentPeriod 2 = supervuoro päättyi -> menossa kotiutuskisa
        tulos = self._tulos({"home": [0], "away": [0]})
        tulos["currentPeriod"] = 2
        tulos["runs"][3] = {"home": [1], "away": [None]}
        ottelu = rakenna_ottelu(127482, OTTELU_127482, tulos)
        self.assertEqual(ottelu.jakso_txt, "Kotiutuskisa")


class TestJaksotauko(unittest.TestCase):
    """Jakso on ratkennut, seuraava ei ole vielä alkanut.

    Todennettu otteluissa 130446 ja 130487 8.8.2026: currentInning jää tauon
    ajaksi edellisen jakson viimeiseen vuoropariin eikä nollaudu ennen kuin
    uuden jakson ensimmäinen tulos kirjataan.
    """

    def setUp(self):
        tulos = {
            "periods": {"home": 1, "away": 0},
            "runs": [
                {"home": [2, 0, 0, 1], "away": [0, 1, 0, 0]},
                {"home": [None, None, None, None], "away": [None, None, None, None]},
                {"home": [None], "away": [None]},
                {"home": [None], "away": [None]},
            ],
            "outCount": 3,
            "currentPeriod": 0,
            "currentInning": 3,
            "batTurn": 1,
            "batTurnTeamKey": "away",
            "finished": False,
            "isPeriodMatch": True,
        }
        self.ottelu = rakenna_ottelu(130446, OTTELU_129209, tulos)

    def test_alkava_jakso_naytetaan(self):
        self.assertEqual(self.ottelu.jakso_txt, "2. jakso")

    def test_vuoroparia_ei_nayteta(self):
        # currentInning 3 on edellisen jakson jäänne
        self.assertEqual(self.ottelu.vuoropari_txt, "")

    def test_ei_sisavuoroa_eika_paloja(self):
        self.assertEqual(self.ottelu.nykyinen_lyontivuoro, "-")
        self.assertEqual(self.ottelu.palot, "")

    def test_jakson_alkaminen_palauttaa_vuoroparin(self):
        # Kun uuden jakson ensimmäinen tulos kirjataan, tauko päättyy
        tulos = {
            "periods": {"home": 1, "away": 0},
            "runs": [
                {"home": [2, 0, 0, 1], "away": [0, 1, 0, 0]},
                {"home": [None, None, None, None], "away": [1, None, None, None]},
                {"home": [None], "away": [None]},
                {"home": [None], "away": [None]},
            ],
            "outCount": 0,
            "currentPeriod": 0,
            "currentInning": 0,
            "batTurn": 0,
            "batTurnTeamKey": "home",
            "finished": False,
            "isPeriodMatch": True,
        }
        ottelu = rakenna_ottelu(130446, OTTELU_129209, tulos)
        self.assertEqual(ottelu.jakso_txt, "2. jakso")
        self.assertEqual(ottelu.vuoropari_txt, "1. aloittava")
        self.assertEqual(ottelu.nykyinen_lyontivuoro, ottelu.kotijoukkue)


class TestLyovanJoukkueenPaattely(unittest.TestCase):
    def test_bat_turn_team_key_ensisijainen(self):
        tulos = dict(TULOS_129209)
        self.assertEqual(paattele_lyova_joukkue(tulos, OTTELU_129209), "away")

    def test_paattely_first_bat_turns_listasta_aloittava(self):
        # Jakso 2 = first_bat_turns[1] = 16810 = koti. currentPeriod 0, koska
        # jakso 1 on päättynyt. batTurn 0 = aloittava.
        tulos = dict(TULOS_129209)
        del tulos["batTurnTeamKey"]
        tulos["currentPeriod"] = 0
        tulos["batTurn"] = 0
        self.assertEqual(paattele_lyova_joukkue(tulos, OTTELU_129209), "home")

    def test_paattely_first_bat_turns_listasta_lopettava(self):
        # Sama jakso, batTurn 1 = lopettava -> vieras
        tulos = dict(TULOS_129209)
        del tulos["batTurnTeamKey"]
        tulos["currentPeriod"] = 0
        tulos["batTurn"] = 1
        self.assertEqual(paattele_lyova_joukkue(tulos, OTTELU_129209), "away")

    def test_paattely_jakso_1(self):
        # Jakso 1 = first_bat_turns[0] = 16811 = vieras. currentPeriod -1,
        # koska yhtään jaksoa ei ole vielä päättynyt.
        tulos = dict(TULOS_129209)
        del tulos["batTurnTeamKey"]
        tulos["currentPeriod"] = -1
        tulos["batTurn"] = 0
        self.assertEqual(paattele_lyova_joukkue(tulos, OTTELU_129209), "away")

    def test_lyontijarjestys_vaihtuu_jaksoittain(self):
        # Pelisäännöt 30 §: sama batTurn eri jaksossa -> eri joukkue.
        # Tämä kiinnittää sen, ettei jakson indeksi pääse luistamaan.
        tulos = dict(TULOS_129209)
        del tulos["batTurnTeamKey"]
        tulos["batTurn"] = 0
        tulos["currentPeriod"] = -1
        jakso_1 = paattele_lyova_joukkue(tulos, OTTELU_129209)
        tulos["currentPeriod"] = 0
        jakso_2 = paattele_lyova_joukkue(tulos, OTTELU_129209)
        self.assertEqual(jakso_1, "away")
        self.assertEqual(jakso_2, "home")
        self.assertNotEqual(jakso_1, jakso_2)

    def test_ei_paattelya_ilman_tietoja(self):
        # currentPeriod 2 -> jakso 4 (kotiutuskisa), jonka aloittajaa ei ole
        # vielä päätetty -> first_bat_turns[3] on None.
        tulos = {"currentPeriod": 2, "batTurn": 0}
        self.assertIsNone(paattele_lyova_joukkue(tulos, OTTELU_129209))


class TestJunioriottelu(unittest.TestCase):
    def setUp(self):
        ottelu_data = dict(OTTELU_129209)
        tulos = {
            "periods": {"home": 0, "away": 0},
            "runs": [{"home": [2, 1, 0, 3], "away": [1, 0, 2, None]}],
            "outCount": 1,
            "currentPeriod": -1,
            "currentInning": 3,
            "batTurn": 1,
            "batTurnTeamKey": "away",
            "finished": False,
            "isPeriodMatch": False,
        }
        self.ottelu = rakenna_ottelu(99999, ottelu_data, tulos)

    def test_otteluinfo(self):
        self.assertEqual(self.ottelu.otteluinfo, "Junioriottelu")

    def test_ei_jaksovoittoja(self):
        self.assertIsNone(self.ottelu.koti_jaksovoitot)
        self.assertIsNone(self.ottelu.vieras_jaksovoitot)

    def test_vain_yksi_jaksosarake(self):
        self.assertEqual(self.ottelu.jakso_1_koti_juoksut, 6)
        self.assertEqual(self.ottelu.jakso_1_vieras_juoksut, 3)
        self.assertIsNone(self.ottelu.jakso_2_koti_juoksut)
        self.assertIsNone(self.ottelu.jakso_3_koti_juoksut)
        self.assertIsNone(self.ottelu.jakso_4_koti_juoksut)


class TestPeruttuOttelu(unittest.TestCase):
    def test_peruttu(self):
        ottelu_data = dict(OTTELU_129199)
        ottelu_data["canceled"] = True
        ottelu = rakenna_ottelu(129199, ottelu_data, None)
        self.assertEqual(ottelu.otteluinfo, "Ottelu peruttu")


class TestVuoroparinTeksti(unittest.TestCase):
    def test_perusjakso(self):
        self.assertEqual(vuoroparin_teksti(1, 0, 0), "1. aloittava")
        self.assertEqual(vuoroparin_teksti(2, 3, 1), "4. lopettava")

    def test_supervuoro(self):
        self.assertEqual(vuoroparin_teksti(3, 0, 0), "aloittava")
        self.assertEqual(vuoroparin_teksti(4, 0, 1), "lopettava")
        self.assertEqual(vuoroparin_teksti(4, 1, 0), "2. aloittava")


if __name__ == "__main__":
    unittest.main()
