from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Otteludata(Base):
    __tablename__ = 'otteludata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ottelunumero = Column(Integer)
    kotijoukkue = Column(String(255), default ="Koti")
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
    nykyinen_lyontivuoro = Column(String(10), default="Koti")
    jakso_nro = Column(Integer, default=1)
    jakso_txt = Column(String(20), default='J1')
    vuoropari_nro = Column(Integer, default=1)
    vuoropari_txt = Column(String(5), default="1. aloittava")
    palot = Column(String(10), default="")
    luotu = Column(TIMESTAMP, server_default='CURRENT_TIMESTAMP')