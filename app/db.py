# database.py
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models import Otteludata
from flask import current_app
from config import Config
from app.functions import vuoropari_int_to_str
from app.functions import jakso_into_to_str


def get_db():
    if 'db' not in current_app.config:
        current_app.config['db'] = Database(Config.SQLALCHEMY_DATABASE_URI)
    return current_app.config['db']

class Database:
    def __init__(self, database_uri):
        self.engine = create_engine(database_uri, echo=True)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def list_matches(self):
        matches = self.session.query(Otteludata).all()
        return matches
    
    def get_match_by_ottelunumero(self, ottelunumero):
        ottelu = self.session.query(Otteludata).filter_by(ottelunumero=ottelunumero).first()
        if ottelu:
            return ottelu
        else:
            return False

    def uusi_ottelu(self):
        max_ottelunumero = self.session.query(func.max(Otteludata.ottelunumero)).scalar()
        ottelu = Otteludata(ottelunumero=max_ottelunumero + 1)
        self.session.add(ottelu)
        self.session.commit()
        return ottelu.ottelunumero

    def update_match(self, ottelunumero, params):
        ottelu = self.get_match_by_ottelunumero(ottelunumero)  

        if ottelu:
            if 'kotijoukkue' in params:
                ottelu.kotijoukkue = params['kotijoukkue']
            if 'vierasjoukkue' in params:
                ottelu.vierasjoukkue = params['vierasjoukkue']

            if 'update_value' in params and 'action' in params:
                if params['action'] == 'lisaa':
                    setattr(ottelu, params['update_value'], getattr(ottelu, params['update_value']) + 1)
                elif params['action'] == 'vahenna':
                    if int(getattr(ottelu, params['update_value'])) > 0:
                        setattr(ottelu, params['update_value'], getattr(ottelu, params['update_value']) - 1)

            if 'action' in params:
                if params['action'] == 'lisaa_palo':
                    if (len(ottelu.palot)) < 12:
                        ottelu.palot = ottelu.palot + "X"
                        
                if params['action'] == 'poista_palot':
                    ottelu.palot = ''

                if params['action'] == 'jakso_taakse':
                    if ottelu.jakso_nro > 1:
                        ottelu.jakso_nro = ottelu.jakso_nro - 1
                        ottelu.jakso_txt = jakso_into_to_str(ottelu.jakso_nro)
                        ottelu.vuoropari_nro = 1
                        ottelu.vuoropari_txt = vuoropari_int_to_str(ottelu.vuoropari_nro)
                        
                if params['action'] == 'jakso_eteenpain':
                    if ottelu.jakso_nro < 4:
                        ottelu.jakso_nro = ottelu.jakso_nro + 1
                        ottelu.jakso_txt = jakso_into_to_str(ottelu.jakso_nro)
                        ottelu.vuoropari_nro = 1
                        ottelu.vuoropari_txt = vuoropari_int_to_str(ottelu.vuoropari_nro)


                if params['action'] == 'vuoropari_taakse':
                    if ottelu.vuoropari_nro > 1:
                        ottelu.vuoropari_nro = ottelu.vuoropari_nro - 1
                        ottelu.vuoropari_txt = vuoropari_int_to_str(ottelu.vuoropari_nro)
                        self.vaihda_lyontivuoro(ottelu)
            
                if params['action'] == 'vuoropari_eteenpain':
                    if ottelu.vuoropari_nro < 13:
                        ottelu.vuoropari_nro = ottelu.vuoropari_nro + 1
                        ottelu.vuoropari_txt = vuoropari_int_to_str(ottelu.vuoropari_nro)
                        self.vaihda_lyontivuoro(ottelu)

                if params['action'] == 'vaihda_lyontivuoro':
                    self.vaihda_lyontivuoro(ottelu)
            try:
                self.engine.echo = False
                self.session.commit()
                self.session.close()
                self.engine.dispose()
                return True
            except IntegrityError:
                self.session.rollback()
                self.session.close()
                self.engine.dispose()
                return False
        return False

    def vaihda_lyontivuoro(self, ottelu):
        if ottelu:
            if ottelu.nykyinen_lyontivuoro == ottelu.kotijoukkue:
                ottelu.nykyinen_lyontivuoro = ottelu.vierasjoukkue
            else:
                ottelu.nykyinen_lyontivuoro = ottelu.kotijoukkue                

                