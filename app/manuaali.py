# manuaali.py
"""Manuaalitaulu: käsin päivitettävä tulostaulu ja sen omat reitit.

Manuaalitaulu on sekundaarinen ja käytössä hyvin harvoin, mutta se on **ainoa
osa sovellusta, joka tarvitsee tietokannan**. Kaikki sitä koskeva on koottu
tähän moduuliin ja sen käyttämiin `app/db.py`:hyn ja `app/models.py`:hyn:

    hae_ottelurivi()     kantarivin haku
    rakenna_tulostaulu() Otteludata-kantarivi -> Tulostaulu
    manuaali_bp          reitit /, /uusi ja /paivita

Livetaulu ei importtaa tästä mitään. `app.db` importataan vasta funktioiden
sisällä, jotta sovellus toimii kokonaan ilman kantaa, kun asetus
MANUAALITAULU_KAYTOSSA on False.

Editorin vuoroparivalitsin on yksi 14-portainen lista, jota operaattori
askeltaa yhdellä napilla. Se on manuaalitaulun oma käsite - livetaulu päättelee
vuoroparin API:sta - mutta molemmat muodostavat näkyvän tekstin samalla
`vuoroparin_nimi`-funktiolla, jotta sama tilanne näyttää samalta kummassakin
taulussa.
"""

from flask import Blueprint, redirect, render_template, request

from app.asetukset import asetus
from app.tulostaulu import (
    JAKSOJEN_OTSIKOT,
    KOTI,
    VIERAS,
    Jakso,
    Tulostaulu,
    jakson_nimi,
    tilannerivi,
    vuoroparin_nimi,
)


manuaali_bp = Blueprint("manuaali", __name__)


# Editorin vuoroparivalitsimen portaat: numero -> (jakso, vuoropari-indeksi,
# lopettava). Jakso vaikuttaa vain siihen, jätetäänkö järjestysnumero pois
# (supervuoro ja kotiutuskisa ovat yhden vuoroparin mittaisia).
_VUOROPARIT = {
    1: (1, 0, False),
    2: (1, 0, True),
    3: (1, 1, False),
    4: (1, 1, True),
    5: (1, 2, False),
    6: (1, 2, True),
    7: (1, 3, False),
    8: (1, 3, True),
    9: (3, 0, False),
    10: (3, 0, True),
    11: (4, 0, False),
    12: (4, 0, True),
}

VUOROPARI_JATKOPARIT = 13
VUOROPARI_PAATTYNYT = 14
VUOROPAREJA = 14

JAKSOJA = 4


def kaytossa():
    """Onko manuaalitaulu (ja sitä myöten tietokanta) käytössä.

    Jos asetus on False, sovellus toimii kokonaan ilman kantaa ja näyttää
    pelkkiä livetauluja.
    """
    return asetus("MANUAALITAULU_KAYTOSSA", True)


def vuoroparin_teksti(vuoropari_nro):
    """Editorin vuoroparinumero näytettäväksi tekstiksi.

    Palauttaa tyhjän merkkijonon päättyneelle ottelulle: se ei ole vuoropari
    vaan ottelun tila, ja näkyy tilarivillä omana tekstinään.
    """
    if vuoropari_nro == VUOROPARI_JATKOPARIT:
        return "jatkoparit"
    if vuoropari_nro == VUOROPARI_PAATTYNYT:
        return ""

    portaat = _VUOROPARIT.get(vuoropari_nro)
    if portaat is None:
        return ""

    jakso_nro, vuoropari_idx, lopettava = portaat
    return vuoroparin_nimi(jakso_nro, vuoropari_idx, lopettava)


def hae_ottelurivi(ottelunumero):
    """Manuaaliottelun kantarivi tai None.

    Kannassa on vanhoja rivejä ajalta, jolloin www-scrape kirjoitti tuloksia
    kantaan (`pesistulokset = 1`). Ne eivät ole manuaaliotteluita vaan
    ohjautuvat API-polulle, joten ne suodatetaan pois tässä.
    """
    if not kaytossa():
        return None

    from app.db import get_db

    rivi = get_db().get_match_by_ottelunumero(ottelunumero)
    if rivi is not None and not rivi.pesistulokset:
        return rivi
    return None


def _sisavuoro(rivi):
    """Kumpi joukkue on sisällä.

    Kannassa sisävuoro on joukkueen **nimi**, koska editori vaihtaa sitä
    kahden nimimerkkijonon välillä. Vertailu tehdään tässä yhdessä paikassa;
    aiemmin se toistui kahdeksassa kohdassa templatessa, jolloin identtinen
    näyttönimi korosti molemmat rivit.
    """
    nimi = rivi.nykyinen_lyontivuoro
    if not nimi:
        return None
    if nimi == rivi.kotijoukkue:
        return KOTI
    if nimi == rivi.vierasjoukkue:
        return VIERAS
    return None


def rakenna_tulostaulu(rivi):
    """Rakentaa Tulostaulu-olion manuaalitaulun kantarivistä."""
    jaksot = [
        Jakso(
            otsikko=otsikko,
            koti=getattr(rivi, f"jakso_{i + 1}_koti_juoksut"),
            vieras=getattr(rivi, f"jakso_{i + 1}_vieras_juoksut"),
            aktiivinen=(i + 1 == rivi.jakso_nro),
        )
        for i, otsikko in enumerate(JAKSOJEN_OTSIKOT)
    ]

    if rivi.vuoropari_nro == VUOROPARI_PAATTYNYT:
        tilanne_txt = "Ottelu on päättynyt"
    else:
        tilanne_txt = tilannerivi(
            rivi.jakso_nro, vuoroparin_teksti(rivi.vuoropari_nro)
        )

    return Tulostaulu(
        ottelunumero=rivi.ottelunumero,
        kotijoukkue=rivi.kotijoukkue,
        vierasjoukkue=rivi.vierasjoukkue,
        koti_jaksovoitot=rivi.koti_jaksovoitot,
        vieras_jaksovoitot=rivi.vieras_jaksovoitot,
        jaksot=jaksot,
        sisavuoro=_sisavuoro(rivi),
        # Kannassa palot on X-merkkijono, jota editori kasvattaa napilla.
        palot=len(rivi.palot or ""),
        tilanne_txt=tilanne_txt,
        info_txt=rivi.otteluinfo or "",
        lahde="manuaali",
    )


# --- Reitit -----------------------------------------------------------------
# Nämä rekisteröidään vain jos manuaalitaulu on käytössä (ks. app/__init__.py),
# joten erillistä käytössä-tarkistusta ei tarvita reittien sisällä.


@manuaali_bp.route("/")
def etusivu():
    """Manuaalitaulun etusivu: uusi ottelu tai olemassa olevan päivitys."""
    return render_template("index.html")


@manuaali_bp.route("/uusi")
def uusi_ottelu():
    from app.db import get_db
    from app.routes import unohda_reititys

    numero = get_db().uusi_ottelu()
    unohda_reititys(numero)
    return redirect(f"/paivita/{numero}")


@manuaali_bp.route(
    "/paivita/<int:ottelunumero>/<int:muokattava_osio>", methods=["GET", "POST"]
)
@manuaali_bp.route(
    "/paivita/<int:ottelunumero>", defaults={"muokattava_osio": 1},
    methods=["GET", "POST"],
)
def paivita_ottelu(ottelunumero, muokattava_osio):
    from app.db import get_db

    muokattava_osio = max(0, min(muokattava_osio, JAKSOJA))

    db = get_db()
    if request.method == "POST":
        db.update_match(ottelunumero, request.form)

    rivi = db.get_match_by_ottelunumero(ottelunumero)
    if rivi is None:
        return "Ottelua ei löydy tällä numerolla.", 404

    # Jakson ja vuoroparin tekstit lasketaan numeroista, ei lueta kannasta:
    # jakso_txt- ja vuoropari_txt-sarakkeet ovat manuaalitaulun perua ajalta,
    # jolloin teksti tallennettiin. Nyt sen muodostaa app/tulostaulu.py.
    return render_template(
        "update_ottelu.html",
        ottelu=rivi,
        muokattava_osio=muokattava_osio,
        jakso_txt=jakson_nimi(rivi.jakso_nro),
        vuoropari_txt=vuoroparin_teksti(rivi.vuoropari_nro),
    )
