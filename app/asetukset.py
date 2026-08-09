# asetukset.py
"""Asetusten luku config.py:stä.

Asetukset luetaan **ajonaikaisesti**, ei importin yhteydessä. Näin testit ja
tools/esikatselu.py voivat vaihtaa asetuksen ilman että moduulit pitää ladata
uudelleen, eikä vanha config.py kaada sovellusta uuden asetuksen puuttuessa.
"""

from config import Config


def asetus(nimi, oletus):
    """Asetuksen arvo config.py:stä tai oletus, jos sitä ei ole määritelty."""
    return getattr(Config, nimi, oletus)
