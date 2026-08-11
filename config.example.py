import os

# Malli config.py:stä, joka ei ole versionhallinnassa. Kopioi tämä
# config.py:ksi ja täytä oikeat arvot.
#
# Merkinnät:
#   [PAKOLLINEN]  puuttuminen kaataa sovelluksen tai reitin
#   [valinnainen] luetaan getattr(Config, 'NIMI', oletus) -tyyliin, ja
#                 oletus on sama kuin alla oleva arvo. Voi jättää pois.
#   [käyttämätön] mikään koodissa ei lue tätä; perua vanhasta versiosta.
#
# Kun päivität tuotannon vanhemmasta versiosta, uusia ovat kaikki
# "Pesäpalloliiton pesistulokset-API" -otsikosta alaspäin. Niistä vain
# PESISTULOKSET_API_KEY on pakko asettaa.


class Config:
    # Database configuration
    # Tietokantaa tarvitaan enää vain manuaalisesti päivitettävään tulostauluun.
    # Livetaulu hakee kaiken pesistulokset-API:sta eikä käytä kantaa lainkaan.
    #
    # [PAKOLLINEN, jos MANUAALITAULU_KAYTOSSA = True] Luetaan app/db.py:ssä
    # suoraan Config.SQLALCHEMY_DATABASE_URI:na vasta kun kantaa tarvitaan,
    # joten pelkkää livetaulua ajava asennus ei tarvitse tätä lainkaan.
    SQLALCHEMY_DATABASE_URI = 'mysql://<username>:<password>@127.0.0.1:3306/jpp-tulostaulu?charset=utf8mb4&binary_prefix=true'
    # [käyttämätön]
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for sessions
    # [käyttämätön] Sovelluksessa ei ole istuntoja eikä sisäänkirjautumista.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'

    # Activate debug mode
    # DEBUG_LEVEL = 1 näytä kaikki debug-viestit
    # DEBUG_LEVEL = 2 näytä vain info ja korkeammat viestit
    # DEBUG_LEVEL = 3 näytä vain varoitus ja korkeammat viestit
    # DEBUG_LEVEL = 4 näytä vain virheviestit
    #
    # [PAKOLLINEN] app/functions.py: debug_message lukee molemmat suoraan.
    # DEBUG_LEVEL luetaan vain jos DEBUG on tosi.
    DEBUG = True
    DEBUG_LEVEL = 1

    # --- Pesäpalloliiton pesistulokset-API ---------------------------------
    # Tästä alaspäin kaikki on uutta 3.0-versiossa (API-toteutus).

    # [PAKOLLINEN] Ilman avainta jokainen livetaulu palauttaa 503:n.
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

    # --- Manuaalitaulu -----------------------------------------------------
    # Aseta False, jos haluat ajaa pelkkää livetaulua ilman tietokantaa.
    # [valinnainen]
    MANUAALITAULU_KAYTOSSA = True

    # Kuinka kauan muistetaan, onko ottelunumero manuaali- vai liveottelu.
    # Estää turhat tietokantakyselyt jokaisella tulostaulun päivityksellä.
    # [valinnainen]
    REITITYS_TTL = 60
