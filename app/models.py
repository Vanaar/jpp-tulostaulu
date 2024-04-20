from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Otteludata(Base):
    __tablename__ = 'otteludata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ottelunumero = Column(Integer)
    kotijoukkue = Column(String(255))
    vierasjoukkue = Column(String(255))
    jakso_0_koti_juoksut = Column(Integer)
    jakso_0_vieras_juoksut = Column(Integer)
    jakso_1_koti_juoksut = Column(Integer)
    jakso_1_vieras_juoksut = Column(Integer)
    jakso_2_koti_juoksut = Column(Integer)
    jakso_2_vieras_juoksut = Column(Integer)
    jakso_3_koti_juoksut = Column(Integer)
    jakso_3_vieras_juoksut = Column(Integer)
    koti_jaksovoitot = Column(Integer)
    vieras_jaksovoitot = Column(Integer)
    nykyinen_lyontivuoro = Column(String(10))
    nykyinen_jakso = Column(Integer)
    nykyinen_vuoropari = Column(String(50))
    vuoropari_nro = Column(Integer)
    vuoropari_txt = Column(String(5))
    palot = Column(String(10))
    luotu = Column(TIMESTAMP, server_default='CURRENT_TIMESTAMP')