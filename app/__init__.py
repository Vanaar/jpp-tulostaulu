# app/__init__.py
"""Sovellustehdas.

Sovellus rakennetaan yhdessä paikassa, jotta käynnistystiedosto, testit ja
tools/esikatselu.py saavat varmasti identtisen sovelluksen. Aiemmin
`jpp-tulostaulu.py` ja `tests/test_reitit.py` rakensivat sen kumpikin omalla
koodillaan, ja uusi reitti piti muistaa lisätä molempiin.

Manuaalitaulun reitit rekisteröidään vain jos manuaalitaulu on käytössä. Kun
MANUAALITAULU_KAYTOSSA on False, sovelluksessa ei ole yhtään reittiä, joka
koskisi tietokantaan.
"""


def luo_sovellus():
    from flask import Flask

    from app.asetukset import asetus
    from app.routes import routes_bp

    sovellus = Flask(__name__, static_folder="../static")
    sovellus.register_blueprint(routes_bp)

    if asetus("MANUAALITAULU_KAYTOSSA", True):
        from app.manuaali import manuaali_bp

        sovellus.register_blueprint(manuaali_bp)

    return sovellus
