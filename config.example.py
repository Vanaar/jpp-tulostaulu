import os

# Malli config.py:stä, joka ei ole versionhallinnassa. Kopioi tämä
# config.py:ksi ja täytä oikeat arvot.
#
# Merkinnät:
#   [PAKOLLINEN]  puuttuminen kaataa sovelluksen tai reitin
#   [valinnainen] luetaan getattr(Config, 'NIMI', oletus) -tyyliin, ja
#                 oletus on sama kuin alla oleva arvo. Voi jättää pois.
#
# 4.0:ssa tietokanta ja manuaalitaulu on poistettu. Jos päivität vanhemmasta
# versiosta, vanhat kanta-asetukset (SQLALCHEMY_*), MANUAALITAULU_KAYTOSSA ja
# REITITYS_TTL voi poistaa config.py:stä; ne eivät haittaa, mutta mikään ei
# enää lue niitä.


class Config:
    # Activate debug mode
    # DEBUG_LEVEL = 1 näytä kaikki debug-viestit
    # DEBUG_LEVEL = 2 näytä vain info ja korkeammat viestit
    # DEBUG_LEVEL = 3 näytä vain varoitus ja korkeammat viestit
    # DEBUG_LEVEL = 4 näytä vain virheviestit
    #
    # [valinnainen] oletukset False ja 1.
    DEBUG = True
    DEBUG_LEVEL = 1

    # --- Pesäpalloliiton pesistulokset-API ---------------------------------

    # [PAKOLLINEN] Ilman avainta jokainen tulostaulu palauttaa 503:n.
    # Avain saadaan Pesäpalloliitolta. Älä committaa oikeaa avainta.
    PESISTULOKSET_API_KEY = os.environ.get('PESISTULOKSET_API_KEY') or '<api-avain>'
    # [valinnainen]
    PESISTULOKSET_API_URL = 'https://api.pesistulokset.fi/api/v1/public'

    # HTTP-pyynnön aikakatkaisu sekunteina
    # [valinnainen]
    PESISTULOKSET_TIMEOUT = 5

    # Välimuistin elinajat sekunteina. Nämä ratkaisevat, kuinka usein API:a
    # kutsutaan – katsojien määrä ei vaikuta kutsujen määrään.
    # [valinnainen] kaikki neljä
    PESISTULOKSET_LIVE_TTL = 10       # käynnissä olevan ottelun tulos
    PESISTULOKSET_FINISHED_TTL = 60   # päättyneen ottelun tulos
    PESISTULOKSET_MATCH_TTL = 300     # ottelun perustiedot (joukkueet ym.)
    PESISTULOKSET_STALE_TTL = 300     # kuinka kauan vanhaa dataa saa tarjoilla,
                                      # jos API ei vastaa

    # Kuinka usein selain hakee tulostaulun palvelimelta (millisekuntia)
    # [valinnainen]
    TULOSTAULU_PAIVITYSVALI_MS = 5000
