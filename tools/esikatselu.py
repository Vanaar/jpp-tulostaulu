# tools/esikatselu.py
"""Renderöi tulostaulun eri tiloissa yhdelle HTML-sivulle silmämääräistä
tarkistusta varten. Ei osa sovellusta.

    python tools/esikatselu.py > esikatselu.html

Livetaulut renderöidään testidatasta ja manuaalitaulu tekaistusta kantarivistä,
joten skripti ei tarvitse verkkoyhteyttä eikä tietokantaa.
"""

import os
import re
import sys
from unittest import mock

JUURI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, JUURI)
sys.path.insert(0, os.path.join(JUURI, "tests"))

from config import Config  # noqa: E402

# Esikatselu näyttää pelkkiä tauluja, joten kantaa ei tarvita. Asetettava
# ennen sovelluksen rakentamista, koska tehdas rekisteröi manuaalireitit vain
# jos manuaalitaulu on käytössä.
Config.DEBUG = False
Config.MANUAALITAULU_KAYTOSSA = False

from app import luo_sovellus  # noqa: E402
from app import pesistulokset_api, routes  # noqa: E402
from test_live import (  # noqa: E402
    OTTELU_129199,
    OTTELU_129209,
    TULOS_129209,
    kaynnissa_oleva_tulos,
)
from test_manuaali import tekaistu_rivi  # noqa: E402
from test_reitit import tee_vastaaja  # noqa: E402

_app = luo_sovellus()
_app.config["TESTING"] = True
_client = _app.test_client()


def taulu(ottelut, tulokset, polku):
    pesistulokset_api.tyhjenna_valimuisti()
    routes.unohda_reititys()
    with mock.patch(
        "app.pesistulokset_api.requests.get",
        side_effect=tee_vastaaja(ottelut, tulokset),
    ):
        return _client.get(polku).get_data(as_text=True)


def manuaalitaulu(**kentat):
    """Renderöi manuaalitaulun tekaistusta kantarivistä."""
    rivi = tekaistu_rivi(**kentat)
    pesistulokset_api.tyhjenna_valimuisti()
    routes.unohda_reititys()
    with mock.patch.object(Config, "MANUAALITAULU_KAYTOSSA", True), mock.patch(
        "app.manuaali.hae_ottelurivi", return_value=rivi
    ):
        return _client.get(f"/{rivi.ottelunumero}/tulostaulu").get_data(as_text=True)


def scope(css, valitsin):
    """Rajaa CSS-säännöt annetun valitsimen alle, jotta molemmat tyylit
    voidaan näyttää samalla sivulla."""
    osat = []
    for saanto in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        valitsimet = ", ".join(
            f"{valitsin} {v.strip()}" for v in saanto[0].split(",") if v.strip()
        )
        osat.append(f"{valitsimet} {{{saanto[1]}}}")
    return "\n".join(osat)


JUNIORI_TULOS = {
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

SUPERVUORO_TULOS = {
    "periods": {"home": 1, "away": 1},
    "runs": [
        {"home": [1, 2, 0, 1], "away": [0, 1, 1, 0]},
        {"home": [0, 1, 0, 0], "away": [2, 1, 0, 1]},
        {"home": [1], "away": [None]},
        {"home": [None], "away": [None]},
    ],
    "outCount": 1,
    # currentPeriod 1 = 2. jakso on päättynyt -> menossa on supervuoro.
    "currentPeriod": 1,
    "currentInning": 0,
    "batTurn": 1,
    "batTurnTeamKey": "away",
    "finished": False,
    "isPeriodMatch": True,
}

JAKSOTAUKO_TULOS = {
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


def osio(otsikko, kuvaus, html):
    return (
        f"<section><h2>{otsikko}</h2><p>{kuvaus}</p>"
        f"<div class='taulut'>"
        f"<div><h4>style=default</h4><div class='default'>{html}</div></div>"
        f"<div><h4>style=siipe</h4><div class='siipe'>{html}</div></div>"
        f"</div></section>"
    )


def main():
    paattynyt = taulu({129209: OTTELU_129209}, {129209: TULOS_129209}, "/129209/tulostaulu")
    kaynnissa = taulu({129209: OTTELU_129209}, {129209: kaynnissa_oleva_tulos()}, "/129209/tulostaulu")
    jaksotauko = taulu({129209: OTTELU_129209}, {129209: JAKSOTAUKO_TULOS}, "/129209/tulostaulu")
    supervuoro = taulu({129209: OTTELU_129209}, {129209: SUPERVUORO_TULOS}, "/129209/tulostaulu")
    alkamaton = taulu({129199: OTTELU_129199}, {}, "/129199/tulostaulu")
    juniori = taulu({129209: OTTELU_129209}, {129209: JUNIORI_TULOS}, "/129209/tulostaulu")
    manuaali = manuaalitaulu()
    manuaali_palot = manuaalitaulu(palot="XXXXXXXXXXXX", jakso_nro=2, vuoropari_nro=9)

    with open(os.path.join(JUURI, "static/css/scoreboard_default.css"), encoding="utf-8") as f:
        default_css = f.read()
    with open(os.path.join(JUURI, "static/css/scoreboard_siipe.css"), encoding="utf-8") as f:
        siipe_css = f.read()

    tyylit = scope(default_css, ".default") + "\n" + scope(siipe_css, ".siipe")

    sisalto = "".join([
        osio("Päättynyt ottelu (129209)",
             "Tilarivillä lukee &quot;Ottelu on päättynyt&quot;. Muu taulu näytetään normaalisti. "
             "Lopputulos API:n mukaan 2-0 (8-3, 6-2).", paattynyt),
        osio("Käynnissä oleva ottelu",
             "1. jakso, 2. vuoropari, koti lyömässä lopettavana, 2 paloa. "
             "Sisävuoro on korostettu ja palot näkyvät lyövän joukkueen rivillä.", kaynnissa),
        osio("Jaksotauko",
             "1. jakso on ratkennut eikä 2. ole alkanut. Alkava jakso näytetään ilman "
             "vuoroparia, eikä sisävuoroa tai paloja näytetä.", jaksotauko),
        osio("Supervuoro",
             "Jaksot 1-1, menossa supervuoro. Vieras lyömässä lopettavana.", supervuoro),
        osio("Ottelu ei ole alkanut (129199)",
             "API palauttaa {&quot;result&quot;:null}. Joukkueiden nimet haetaan silti "
             "/match-kutsulla. Taulu on saman levyinen kuin käynnissä olevassa "
             "ottelussa, vain solut ovat tyhjiä.", alkamaton),
        osio("Junioriottelu",
             "isPeriodMatch = false: ei jaksovoittoja, vain yksi tulossarake ja "
             "lisätiedoksi &quot;Junioriottelu&quot;.", juniori),
        osio("Manuaalitaulu",
             "Sama template, eri datalähde: käsin päivitettävä taulu tietokannan rivistä. "
             "Koti sisällä, 2 paloa.", manuaali),
        osio("Manuaalitaulu, supervuoro ja 12 paloa",
             "Palot rivittyvät neljän välein. Manuaalitaulussa niitä voi kertyä 12, "
             "livetaulussa enintään kolme.", manuaali_palot),
    ])

    sivu = f"""<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">
<title>JPP-tulostaulu - esikatselu</title>
<style>
body{{font-family:-apple-system,Segoe UI,Arial,sans-serif;margin:0;padding:32px;background:#f6f7f9;color:#1a1d21}}
h1{{font-size:22px;margin:0 0 6px}}
.ingressi{{color:#5a6169;margin:0 0 28px;max-width:78ch;font-size:14px;line-height:1.6}}
section{{background:#fff;border:1px solid #e3e6ea;border-radius:10px;padding:20px 24px;margin-bottom:20px}}
h2{{font-size:16px;margin:0 0 4px}}
section > p{{margin:0 0 18px;color:#5a6169;font-size:13px;max-width:78ch;line-height:1.5}}
h4{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#8a9099;margin:0 0 10px;font-weight:600}}
.taulut{{display:flex;gap:48px;flex-wrap:wrap}}
{tyylit}
</style>
</head>
<body>
<h1>JPP-tulostaulu &ndash; esikatselu</h1>
<p class="ingressi">Kaikki taulut on renderöity samasta templatesta samasta
n&auml;kym&auml;mallista (app/tulostaulu.py). Livetaulut tulevat pesistulokset-API:n
muotoisesta testidatasta ja manuaalitaulu tekaistusta kantarivist&auml;, joten
sivun tekemiseen ei tarvita verkkoyhteytt&auml; eik&auml; tietokantaa.</p>
{sisalto}
</body>
</html>"""
    sys.stdout.write(sivu)


if __name__ == "__main__":
    main()
