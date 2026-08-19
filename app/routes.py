from flask import request, redirect, render_template, Blueprint

from app.functions import debug_message, parsi_koko
from app.live import rakenna_ottelu
from app.pesistulokset_api import ApiVirhe, hae_live_tulos, hae_ottelu
from config import Config

import constants


routes_bp = Blueprint('routes', __name__)


def _paivitysvali():
    """Kuinka usein selain hakee tulostaulun palvelimelta (ms)."""
    return getattr(Config, 'TULOSTAULU_PAIVITYSVALI_MS', 5000)


def _hae_liveottelu(ottelunumero):
    """Rakentaa tulostaulun näkymämallin API:sta. Ei käytä tietokantaa."""
    ottelu_data = hae_ottelu(ottelunumero)
    if not ottelu_data:
        return None

    tulos = hae_live_tulos(ottelunumero)
    return rakenna_ottelu(ottelunumero, ottelu_data, tulos)


@routes_bp.route("/hellurei")
def hellurei():
    return "Oujee!"


@routes_bp.route("/<int:ottelunumero>", methods=['GET'])
def ottelu_tulostaulu(ottelunumero):
    """Widgetin osoite: /<ottelunumero>. Käyttö säilyy ennallaan."""
    debug = request.args.get('debug', 'off')
    style = request.args.get('style', 'default')
    # Valinnainen kokokerroin striimigrafiikkaa varten; oletus 1.0
    koko = parsi_koko(request.args.get('koko'))

    try:
        if hae_ottelu(ottelunumero) is None:
            return "Ottelua ei löydy pesistuloksista.", 404
    except ApiVirhe as e:
        debug_message(f"ApiVirhe: {e}", constants.DEBUG_MESSAGE_LEVEL_ERROR)
        return "Pesistulokset-palveluun ei juuri nyt saada yhteyttä.", 503

    return render_template('ottelu.html', ottelu={'ottelunumero': ottelunumero},
                           debug=debug, style=style, koko=koko,
                           paivitysvali=_paivitysvali())


@routes_bp.route("/<int:ottelunumero>/tulostaulu", methods=['GET'])
def nayta_tulostaulu(ottelunumero):
    """Selain hakee tämän muutaman sekunnin välein ja korvaa taulun sisällön."""
    debug = request.args.get('debug', 'off')

    try:
        ottelu = _hae_liveottelu(ottelunumero)
    except ApiVirhe as e:
        debug_message(f"ApiVirhe: {e}", constants.DEBUG_MESSAGE_LEVEL_ERROR)
        return "", 503

    if ottelu is None:
        return "", 404

    return render_template('tulostaulu.html', ottelu=ottelu, debug=debug,
                           style='default')
