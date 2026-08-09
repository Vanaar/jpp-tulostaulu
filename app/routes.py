# routes.py
"""Widgetin julkiset osoitteet ja päätös siitä, kumpi taulu näytetään.

    /<ottelunumero>              kehyssivu, joka pollaa alla olevaa osoitetta
    /<ottelunumero>/tulostaulu   itse taulu

URL-sopimus on julkinen eikä sitä saa muuttaa: tauluja on upotettu
ulkopuolisille sivuille. Valinnaiset parametrit ovat `?style=` ja `?debug=on`.

Tässä moduulissa ei ole kummankaan taulun logiikkaa, vain reititys:

    app/live.py      livetaulu, data pesistulokset-API:sta
    app/manuaali.py  manuaalitaulu, data tietokannasta

Reitityssääntö: numero on manuaaliottelu jos ja vain jos se löytyy kannasta
rivinä, jossa `pesistulokset = 0`.
"""

from threading import RLock

from flask import Blueprint, render_template, request

from app import manuaali
from app.asetukset import asetus
from app.live import rakenna_ottelu
from app.loki import DEBUG_MESSAGE_LEVEL_ERROR, debug_message
from app.pesistulokset_api import ApiVirhe, hae_live_tulos, hae_ottelu

import time


routes_bp = Blueprint("routes", __name__)


# Käytettävissä olevat tyylitiedostot: static/css/scoreboard_<nimi>.css.
# Tuntematon arvo palautuu oletukseen, jottei URL-parametri voi osoittaa
# olemattomaan tiedostoon.
TYYLIT = ("default", "siipe")
OLETUSTYYLI = "default"


# Muistetaan, mitkä ottelunumerot EIVÄT ole manuaaliotteluita, jottei livetaulu
# tee kantakyselyä joka päivityksellä. Manuaaliottelun rivi haetaan aina
# kannasta, koska sen tiedot muuttuvat.
_reititys = {}
_reititys_lukko = RLock()


def _reititys_ttl():
    return asetus("REITITYS_TTL", 60)


def paivitysvali():
    """Kuinka usein selain hakee tulostaulun palvelimelta (ms)."""
    return asetus("TULOSTAULU_PAIVITYSVALI_MS", 5000)


def unohda_reititys(ottelunumero=None):
    """Unohtaa reitityspäätöksen. Kutsutaan kun uusi manuaaliottelu luodaan."""
    with _reititys_lukko:
        if ottelunumero is None:
            _reititys.clear()
        else:
            _reititys.pop(ottelunumero, None)


def _valitse_tyyli(arvo):
    return arvo if arvo in TYYLIT else OLETUSTYYLI


def _manuaalirivi(ottelunumero):
    """Manuaaliottelun kantarivi tai None, jos numero ei ole manuaaliottelu.

    Livetaululle tämä on korkeintaan yksi kantakysely per REITITYS_TTL, ei per
    selainpyyntö. Manuaaliottelu haetaan aina kannasta, koska sen tiedot
    muuttuvat. Ilman manuaalitaulua kantaan ei koskettu lainkaan.
    """
    if not manuaali.kaytossa():
        return None

    with _reititys_lukko:
        merkinta = _reititys.get(ottelunumero)

    if merkinta is not None:
        on_manuaali, hetki = merkinta
        if not on_manuaali and (time.monotonic() - hetki) < _reititys_ttl():
            return None

    rivi = manuaali.hae_ottelurivi(ottelunumero)

    with _reititys_lukko:
        _reititys[ottelunumero] = (rivi is not None, time.monotonic())

    return rivi


def _hae_livetaulu(ottelunumero):
    """Livetaulun Tulostaulu API:sta. Ei käytä tietokantaa."""
    ottelu_data = hae_ottelu(ottelunumero)
    if not ottelu_data:
        return None

    tulos = hae_live_tulos(ottelunumero)
    return rakenna_ottelu(ottelunumero, ottelu_data, tulos)


@routes_bp.route("/hellurei")
def hellurei():
    return "Oujee!"


@routes_bp.route("/<int:ottelunumero>", methods=["GET"])
def ottelu_tulostaulu(ottelunumero):
    """Widgetin kehyssivu. Osoite on julkinen sopimus, älä muuta."""
    debug = request.args.get("debug", "off")
    tyyli = _valitse_tyyli(request.args.get("style", OLETUSTYYLI))

    if _manuaalirivi(ottelunumero) is None:
        # Ei manuaaliottelu -> varmistetaan että ottelu on olemassa API:ssa,
        # jottei kehyssivu jää pollaamaan olematonta ottelua.
        try:
            if hae_ottelu(ottelunumero) is None:
                return "Ottelua ei löydy.", 404
        except ApiVirhe as e:
            debug_message(f"ApiVirhe: {e}", DEBUG_MESSAGE_LEVEL_ERROR)
            return "Pesistulokset-palveluun ei juuri nyt saada yhteyttä.", 503

    return render_template(
        "ottelu.html",
        ottelunumero=ottelunumero,
        debug=debug,
        style=tyyli,
        paivitysvali=paivitysvali(),
    )


@routes_bp.route("/<int:ottelunumero>/tulostaulu", methods=["GET"])
def nayta_tulostaulu(ottelunumero):
    """Selain hakee tämän muutaman sekunnin välein ja korvaa taulun sisällön."""
    debug = request.args.get("debug", "off")

    rivi = _manuaalirivi(ottelunumero)
    taulu = manuaali.rakenna_tulostaulu(rivi) if rivi is not None else None

    if taulu is None:
        try:
            taulu = _hae_livetaulu(ottelunumero)
        except ApiVirhe as e:
            debug_message(f"ApiVirhe: {e}", DEBUG_MESSAGE_LEVEL_ERROR)
            return "", 503

    if taulu is None:
        return "", 404

    return render_template("tulostaulu.html", ottelu=taulu, debug=debug)
