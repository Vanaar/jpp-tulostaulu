# pesistulokset_api.py
"""
Pesäpalloliiton pesistulokset-API:n asiakas.

Korvaa aiemman www-scrapen. Tarjoaa kaksi hakua:

    hae_ottelu(ottelunumero)      -> /public/match
    hae_live_tulos(ottelunumero)  -> /public/match-live-result

Molemmat käyttävät prosessin sisäistä välimuistia, jotta katsojien määrä ei
vaikuta API-kutsujen määrään: sata samaa tulostaulua katsovaa selainta
aiheuttaa saman määrän API-kutsuja kuin yksi.

Välimuistin elinajat tulevat config.py:stä (ks. config.example.py).
"""

from threading import RLock
from app.functions import debug_message
from config import Config

import requests
import time
import constants


API_BASE_URL = getattr(
    Config, "PESISTULOKSET_API_URL", "https://api.pesistulokset.fi/api/v1/public"
)

# Kuinka kauan käynnissä olevan ottelun live-tulos on tuoretta (sekuntia)
LIVE_TTL = getattr(Config, "PESISTULOKSET_LIVE_TTL", 10)

# Päättyneen ottelun tulos ei enää muutu -> haetaan harvoin
FINISHED_TTL = getattr(Config, "PESISTULOKSET_FINISHED_TTL", 60)

# Ottelun perustiedot (joukkueet, sarja, kentät) muuttuvat harvoin
MATCH_TTL = getattr(Config, "PESISTULOKSET_MATCH_TTL", 300)

# Kuinka kauan vanhaa dataa tarjoillaan, jos API ei vastaa (sekuntia)
STALE_TTL = getattr(Config, "PESISTULOKSET_STALE_TTL", 300)

REQUEST_TIMEOUT = getattr(Config, "PESISTULOKSET_TIMEOUT", 5)


class ApiVirhe(Exception):
    """API-kutsu epäonnistui eikä välimuistissa ollut käyttökelpoista dataa."""


class _Valimuisti:
    """Yksinkertainen säieturvallinen TTL-välimuisti.

    Tallentaa myös vanhentuneen arvon, jotta se voidaan tarjoilla
    varmuuskopiona, jos API on hetkellisesti pois pelistä.
    """

    def __init__(self):
        self._data = {}
        self._lukko = RLock()

    def hae(self, avain, ttl):
        """Palauttaa (arvo, tuore) tai (None, False), jos avainta ei ole."""
        with self._lukko:
            merkinta = self._data.get(avain)
        if merkinta is None:
            return None, False
        arvo, tallennettu = merkinta
        return arvo, (time.monotonic() - tallennettu) < ttl

    def hae_vanhentunut(self, avain, max_ika):
        """Palauttaa arvon, jos se on korkeintaan max_ika sekuntia vanha."""
        with self._lukko:
            merkinta = self._data.get(avain)
        if merkinta is None:
            return None
        arvo, tallennettu = merkinta
        if (time.monotonic() - tallennettu) < max_ika:
            return arvo
        return None

    def aseta(self, avain, arvo):
        with self._lukko:
            self._data[avain] = (arvo, time.monotonic())

    def tyhjenna(self, avain=None):
        with self._lukko:
            if avain is None:
                self._data.clear()
            else:
                self._data.pop(avain, None)


_valimuisti = _Valimuisti()
# Estää saman ottelun rinnakkaiset yhtäaikaiset haut (thundering herd)
_hakulukot = {}
_hakulukot_lukko = RLock()


def _hakulukko(avain):
    with _hakulukot_lukko:
        if avain not in _hakulukot:
            _hakulukot[avain] = RLock()
        return _hakulukot[avain]


def _api_avain():
    avain = getattr(Config, "PESISTULOKSET_API_KEY", None)
    if not avain:
        raise ApiVirhe(
            "PESISTULOKSET_API_KEY puuttuu config.py:stä. "
            "Katso malli config.example.py:stä."
        )
    return avain


def _kutsu(polku, ottelunumero):
    """Tekee varsinaisen HTTP-kutsun ja palauttaa vastauksen sanakirjana."""
    url = f"{API_BASE_URL}/{polku}"
    params = {"id": ottelunumero, "apikey": _api_avain()}

    debug_message(
        f"API-kutsu: {url}?id={ottelunumero}", constants.DEBUG_MESSAGE_LEVEL_INFO
    )

    vastaus = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

    if vastaus.status_code == 404:
        return None

    vastaus.raise_for_status()
    return vastaus.json()


def _hae_valimuistista(polku, ottelunumero, ttl):
    """Hakee polun datan välimuistista tai API:sta.

    Palauttaa API:n vastauksen (dict) tai None, jos ottelua ei ole.
    """
    avain = f"{polku}:{ottelunumero}"

    arvo, tuore = _valimuisti.hae(avain, ttl)
    if tuore:
        return arvo

    with _hakulukko(avain):
        # Toinen säie saattoi ehtiä päivittää välimuistin odottaessamme lukkoa
        arvo, tuore = _valimuisti.hae(avain, ttl)
        if tuore:
            return arvo

        try:
            data = _kutsu(polku, ottelunumero)
        except Exception as e:
            debug_message(
                f"API-kutsu epäonnistui ({polku}, {ottelunumero}): {e}",
                constants.DEBUG_MESSAGE_LEVEL_ERROR,
            )
            vanha = _valimuisti.hae_vanhentunut(avain, STALE_TTL)
            if vanha is not None:
                debug_message(
                    "Tarjoillaan vanhentunutta välimuistidataa",
                    constants.DEBUG_MESSAGE_LEVEL_WARN,
                )
                return vanha
            raise ApiVirhe(f"Pesistulokset-API ei vastaa: {e}") from e

        _valimuisti.aseta(avain, data)
        return data


def hae_ottelu(ottelunumero):
    """Ottelun perustiedot: joukkueet, sarja, kenttä, aika, lopputulos.

    Palauttaa dictin tai None, jos ottelua ei ole olemassa.
    """
    data = _hae_valimuistista("match", ottelunumero, MATCH_TTL)
    if not data or not data.get("id"):
        return None
    return data


def hae_live_tulos(ottelunumero):
    """Ottelun senhetkinen tulos.

    Palauttaa result-osan dictinä tai None, jos ottelu ei ole vielä alkanut
    (API palauttaa tällöin {"result": null}).
    """
    # Ensimmäinen kevyt kurkistus: onko ottelu jo päättynyt? Jos on, riittää
    # harvempi päivitystahti.
    avain = f"match-live-result:{ottelunumero}"
    edellinen, _ = _valimuisti.hae(avain, 0)
    ttl = LIVE_TTL
    if edellinen and isinstance(edellinen.get("result"), dict):
        if edellinen["result"].get("finished"):
            ttl = FINISHED_TTL

    data = _hae_valimuistista("match-live-result", ottelunumero, ttl)
    if not data:
        return None
    return data.get("result")


def tyhjenna_valimuisti(ottelunumero=None):
    """Tyhjentää välimuistin. Käytetään lähinnä testeissä."""
    if ottelunumero is None:
        _valimuisti.tyhjenna()
    else:
        _valimuisti.tyhjenna(f"match:{ottelunumero}")
        _valimuisti.tyhjenna(f"match-live-result:{ottelunumero}")
