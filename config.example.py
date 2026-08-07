import os

class Config:
    # Database configuration
    # Tietokantaa tarvitaan enää vain manuaalisesti päivitettävään tulostauluun.
    # Livetaulu hakee kaiken pesistulokset-API:sta eikä käytä kantaa lainkaan.
    SQLALCHEMY_DATABASE_URI = 'mysql://<username>:<password>@127.0.0.1:3306/jpp-tulostaulu?charset=utf8mb4&binary_prefix=true'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'

    # Activate debug mode
    # DEBUG_LEVEL = 1 näytä kaikki debug-viestit
    # DEBUG_LEVEL = 2 näytä vain info ja korkeammat viestit
    # DEBUG_LEVEL = 3 näytä vain varoitus ja korkeammat viestit
    # DEBUG_LEVEL = 4 näytä vain virheviestit
    DEBUG = True
    DEBUG_LEVEL = 1

    # --- Pesäpalloliiton pesistulokset-API ---------------------------------
    # Avain saadaan Pesäpalloliitolta. Älä committaa oikeaa avainta.
    PESISTULOKSET_API_KEY = os.environ.get('PESISTULOKSET_API_KEY') or '<api-avain>'
    PESISTULOKSET_API_URL = 'https://api.pesistulokset.fi/api/v1/public'

    # HTTP-pyynnön aikakatkaisu sekunteina
    PESISTULOKSET_TIMEOUT = 5

    # Välimuistin elinajat sekunteina. Nämä ratkaisevat, kuinka usein API:a
    # kutsutaan – katsojien määrä ei vaikuta kutsujen määrään.
    PESISTULOKSET_LIVE_TTL = 10       # käynnissä olevan ottelun tulos
    PESISTULOKSET_FINISHED_TTL = 60   # päättyneen ottelun tulos
    PESISTULOKSET_MATCH_TTL = 300     # ottelun perustiedot (joukkueet ym.)
    PESISTULOKSET_STALE_TTL = 300     # kuinka kauan vanhaa dataa saa tarjoilla,
                                      # jos API ei vastaa

    # Kuinka usein selain hakee tulostaulun palvelimelta (millisekuntia)
    TULOSTAULU_PAIVITYSVALI_MS = 5000

    # --- Manuaalitaulu -----------------------------------------------------
    # Aseta False, jos haluat ajaa pelkkää livetaulua ilman tietokantaa.
    MANUAALITAULU_KAYTOSSA = True

    # Kuinka kauan muistetaan, onko ottelunumero manuaali- vai liveottelu.
    # Estää turhat tietokantakyselyt jokaisella tulostaulun päivityksellä.
    REITITYS_TTL = 60
