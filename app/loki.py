# loki.py
"""Debug-tulostus. Ainoa apumoduuli, jota molemmat tulostaulut käyttävät.

Korvaa aiemmat app/functions.py:n ja constants.py:n. Niissä oli sekaisin
lokitusta, manuaalitaulun tekstitaulukoita ja livetaulun palomuotoilua, mikä
piti taulut kiinni toisissaan. Tekstit ovat nyt app/tulostaulu.py:ssä ja
manuaalitaulun omat app/manuaali.py:ssä.
"""

import datetime

from app.asetukset import asetus


DEBUG_MESSAGE_LEVEL_ALL = 1
DEBUG_MESSAGE_LEVEL_INFO = 2
DEBUG_MESSAGE_LEVEL_WARN = 3
DEBUG_MESSAGE_LEVEL_ERROR = 4


def debug_message(viesti, taso=DEBUG_MESSAGE_LEVEL_ALL):
    if asetus("DEBUG", False) and taso >= asetus("DEBUG_LEVEL", 1):
        aikaleima = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{aikaleima}] {viesti}")
