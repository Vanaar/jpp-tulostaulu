from flask import request, redirect, render_template, Blueprint
from threading import RLock

from app.functions import debug_message
from app.live import rakenna_ottelu
from app.pesistulokset_api import ApiVirhe, hae_live_tulos, hae_ottelu
from config import Config

import constants
import time


routes_bp = Blueprint('routes', __name__)


# Ottelunumeroiden reitityksen välimuisti: kertoo, onko numero manuaaliottelu.
# Näin livetaulu ei tee tietokantakyselyä joka päivityksellä.
_REITITYS_TTL = getattr(Config, 'REITITYS_TTL', 60)
_reititys = {}
_reititys_lukko = RLock()


def _paivitysvali():
    """Kuinka usein selain hakee tulostaulun palvelimelta (ms)."""
    return getattr(Config, 'TULOSTAULU_PAIVITYSVALI_MS', 5000)


def _manuaalitaulu_kaytossa():
    """Onko manuaalitaulu (ja sitä myöten tietokanta) käytössä.

    Jos asetus on False, sovellus toimii kokonaan ilman tietokantaa ja
    näyttää pelkkiä livetauluja.
    """
    return getattr(Config, 'MANUAALITAULU_KAYTOSSA', True)


def _tyhjenna_reititys(ottelunumero=None):
    with _reititys_lukko:
        if ottelunumero is None:
            _reititys.clear()
        else:
            _reititys.pop(ottelunumero, None)


def _on_manuaaliottelu(ottelunumero):
    """Onko ottelunumero kannassa manuaalisesti päivitettävänä otteluna.

    Vastaus välimuistitetaan lyhyeksi aikaa, koska ottelun tyyppi ei muutu
    kesken ottelun. Kannassa saattaa olla vanhoja rivejä, joita aiemmin
    päivitettiin www-scrapella (pesistulokset = 1); ne eivät ole
    manuaaliotteluita vaan ohjautuvat nykyään API-toteutukseen.
    """
    if not _manuaalitaulu_kaytossa():
        return False

    with _reititys_lukko:
        merkinta = _reititys.get(ottelunumero)
    if merkinta and (time.monotonic() - merkinta[1]) < _REITITYS_TTL:
        return merkinta[0]

    on_manuaali = _hae_manuaaliottelu(ottelunumero) is not None

    with _reititys_lukko:
        _reititys[ottelunumero] = (on_manuaali, time.monotonic())
    return on_manuaali


def _hae_manuaaliottelu(ottelunumero):
    """Palauttaa manuaaliottelun kantarivin tai None."""
    if not _manuaalitaulu_kaytossa():
        return None

    from app.db import get_db

    ottelu = get_db().get_match_by_ottelunumero(ottelunumero)
    if ottelu and not ottelu.pesistulokset:
        return ottelu
    return None


def _hae_liveottelu(ottelunumero):
    """Rakentaa livetulostaulun näkymämallin API:sta. Ei käytä tietokantaa."""
    ottelu_data = hae_ottelu(ottelunumero)
    if not ottelu_data:
        return None

    tulos = hae_live_tulos(ottelunumero)
    return rakenna_ottelu(ottelunumero, ottelu_data, tulos)


@routes_bp.route("/uusi")
def uusi_ottelu():
    if not _manuaalitaulu_kaytossa():
        return "Manuaalitaulu ei ole käytössä.", 404

    from app.db import get_db

    numero = get_db().uusi_ottelu()
    _tyhjenna_reititys(numero)
    return redirect(f'/paivita/{numero}')


@routes_bp.route("/hellurei")
def hellurei():
    return "Oujee!"


@routes_bp.route("/paivita/<int:ottelunumero>/<int:muokattava_osio>", methods=['GET', 'POST'])
@routes_bp.route("/paivita/<int:ottelunumero>", defaults={'muokattava_osio': 1}, methods=['GET', 'POST'])
def paivita_ottelu(ottelunumero, muokattava_osio):
    if not _manuaalitaulu_kaytossa():
        return "Manuaalitaulu ei ole käytössä.", 404

    from app.db import get_db

    if muokattava_osio < 0 or muokattava_osio is None:
        muokattava_osio = 1
    elif muokattava_osio > 4:
        muokattava_osio = 4

    db = get_db()
    if request.method == 'POST':
        db.update_match(ottelunumero, request.form)

    ottelu = db.get_match_by_ottelunumero(ottelunumero)
    if ottelu:
        return render_template('update_ottelu.html', ottelu=ottelu, muokattava_osio=muokattava_osio)
    else:
        return "Ottelua ei löydy tällä numerolla."


@routes_bp.route("/<int:ottelunumero>", methods=['GET'])
def ottelu_tulostaulu(ottelunumero):
    """Widgetin osoite: /<ottelunumero>. Käyttö säilyy ennallaan."""
    debug = request.args.get('debug', 'off')
    style = request.args.get('style', 'default')

    # Manuaalitaulu tunnistetaan kannasta, muuten tiedot haetaan API:sta
    if _on_manuaaliottelu(ottelunumero):
        ottelu = _hae_manuaaliottelu(ottelunumero)
        if ottelu:
            return render_template('ottelu.html', ottelu=ottelu, pesistulokset=False,
                                   debug=debug, style=style,
                                   paivitysvali=_paivitysvali())

    try:
        if hae_ottelu(ottelunumero) is None:
            return "Ottelua ei ole tietokannassa eikä myöskään pesistuloksissa.", 404
    except ApiVirhe as e:
        debug_message(f"ApiVirhe: {e}", constants.DEBUG_MESSAGE_LEVEL_ERROR)
        return "Pesistulokset-palveluun ei juuri nyt saada yhteyttä.", 503

    return render_template('ottelu.html', ottelu={'ottelunumero': ottelunumero},
                           pesistulokset=True, debug=debug, style=style,
                           paivitysvali=_paivitysvali())


@routes_bp.route("/<int:ottelunumero>/tulostaulu", methods=['GET'])
def nayta_tulostaulu(ottelunumero):
    """Selain hakee tämän muutaman sekunnin välein ja korvaa taulun sisällön."""
    debug = request.args.get('debug', 'off')

    if _on_manuaaliottelu(ottelunumero):
        ottelu = _hae_manuaaliottelu(ottelunumero)
        if ottelu:
            return render_template('tulostaulu.html', ottelu=ottelu, debug=debug,
                                   pesistulokset=False, style='default')

    try:
        ottelu = _hae_liveottelu(ottelunumero)
    except ApiVirhe as e:
        debug_message(f"ApiVirhe: {e}", constants.DEBUG_MESSAGE_LEVEL_ERROR)
        return "", 503

    if ottelu is None:
        return "", 404

    return render_template('tulostaulu.html', ottelu=ottelu, debug=debug,
                           pesistulokset=True, style='default')
