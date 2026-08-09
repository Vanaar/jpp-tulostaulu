# models.py
"""Manuaalitaulun tietokantataulu. Livetaulu ei käytä tätä lainkaan.

Sarakkeiden mitat vastaavat static/otteludata.sql:ää. Ne olivat aiemmin osin
eri mittaisia kuin kannassa (esim. vuoropari_txt oli mallissa VARCHAR(5),
kannassa VARCHAR(100)), mikä olisi katkonut arvoja, jos malli olisi joskus
luonut taulun.
"""

from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Otteludata(Base):
    __tablename__ = 'otteludata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ottelunumero = Column(Integer)
    # 0 = manuaaliottelu. Vanhoissa riveissä 1 tarkoitti www-scrapen
    # kirjoittamaa ottelua; ne ohjautuvat nykyään API-polulle.
    pesistulokset = Column(Integer, default=0)
    kotijoukkue = Column(String(255), default="Koti")
    vierasjoukkue = Column(String(255), default="Vieras")
    koti_jaksovoitot = Column(Integer, default=0)
    vieras_jaksovoitot = Column(Integer, default=0)
    jakso_1_koti_juoksut = Column(Integer, default=0)
    jakso_1_vieras_juoksut = Column(Integer, default=0)
    jakso_2_koti_juoksut = Column(Integer, default=0)
    jakso_2_vieras_juoksut = Column(Integer, default=0)
    jakso_3_koti_juoksut = Column(Integer, default=0)
    jakso_3_vieras_juoksut = Column(Integer, default=0)
    jakso_4_koti_juoksut = Column(Integer, default=0)
    jakso_4_vieras_juoksut = Column(Integer, default=0)
    # Sisävuoro on joukkueen nimi, koska editori vaihtaa sitä kahden
    # nimimerkkijonon välillä. Muunnos tehdään app/manuaali.py:ssä.
    nykyinen_lyontivuoro = Column(String(50), default="Koti")
    jakso_nro = Column(Integer, default=1)
    vuoropari_nro = Column(Integer, default=1)
    # X-merkkijono, jota editori kasvattaa napilla.
    palot = Column(String(30), default="")
    otteluinfo = Column(String(50), default="")
    luotu = Column(TIMESTAMP, server_default='CURRENT_TIMESTAMP')

    # Vanhat tekstisarakkeet ajalta, jolloin näkyvä teksti tallennettiin.
    # Niitä ei enää kirjoiteta eikä lueta - teksti muodostetaan numeroista
    # app/tulostaulu.py:ssä. Sarakkeet ovat kannassa NOT NULL DEFAULT, joten
    # ne on jätetty tänne, jotta INSERT toimii ilman kantamuutosta.
    jakso_txt = Column(String(20), default='J1')
    vuoropari_txt = Column(String(100), default="1. aloittava")
