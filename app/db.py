# db.py
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, ResourceClosedError
from sqlalchemy.pool import QueuePool
from app.loki import DEBUG_MESSAGE_LEVEL_ERROR, debug_message
from app.manuaali import JAKSOJA, VUOROPAREJA
from app.models import Otteludata
from flask import g
from config import Config

import inspect

def get_db():
    """
    Palauttaa tietokanta-instanssin. Luo uuden, jos sitä ei ole olemassa.

    Palauttaa:
        Database: tietokanta-instanssi

    Nostaa:
        RuntimeError: Jos tietokanta-instanssia ei voida luoda
    """
    # Tarkistetaan, onko tietokanta-instanssi jo olemassa
    # 'g' on globaali muuttuja, joka on käytettävissä koko pyyntöjen elinkaaren ajan
    # Jos 'db' ei ole 'g':ssä, luodaan uusi tietokanta-instanssi ja tallennetaan se 'g':hen
    if 'db' not in g:
        try:
            # Luodaan uusi tietokanta-instanssi
            g.db = Database(Config.SQLALCHEMY_DATABASE_URI)
        except Exception as e:
            # Jos tietokanta-instanssia ei voida luoda, nostetaan RuntimeError
            raise RuntimeError("Tietokantayhteyttä ei voitu luoda") from e
    return g.db

class Database:
    def __init__(self, database_uri):
        debug_message(f"Connecting to database: {database_uri}")
        self.engine = create_engine(database_uri, poolclass=QueuePool, echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        debug_message("Connected to database")

    def close_connection(self):
        debug_message("Closing database connection")
        if self.session:
            debug_message("Closing session")
            self.session.close()
        debug_message("Disposing engine")
        self.engine.dispose()

    def commit(self, ottelu):
        try:
            self.engine.echo = False
            self.session.commit()
            return ottelu
        except IntegrityError as e:
            self.session.rollback()
            print(e)
            return False
        except Exception as e:
            print(e)
            return False
        
    def get_match_by_ottelunumero(self, ottelunumero):
        # Close the existing session if it's active
        if self.session:
            self.session.close()

        # Create a new session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        try:
            debug_message(f"get_match_by_ottelunumero({ottelunumero}) called by: {inspect.stack()[1].function}")
            ottelu = self.session.query(Otteludata).filter_by(ottelunumero=ottelunumero).first()
            if ottelu is None:
                debug_message(f"Ottelua {ottelunumero} ei löytynyt kannasta")
            return ottelu
        except ResourceClosedError as e:
            debug_message(f"ResourceClosedError: {e}", DEBUG_MESSAGE_LEVEL_ERROR)
            return None
        except Exception as e:
            debug_message(f"Error: {e}", DEBUG_MESSAGE_LEVEL_ERROR)
            return None
        
    def uusi_ottelu(self, pesistulokset=0, ottelunumero=0):
        if pesistulokset == 1 and ottelunumero > 0:
            ottelu = Otteludata(ottelunumero=ottelunumero, pesistulokset=pesistulokset)
        else:
            max_ottelunumero = self.session.query(func.max(Otteludata.ottelunumero)).scalar()
            ottelu = Otteludata(ottelunumero=max_ottelunumero + 1, pesistulokset=pesistulokset)
            
        self.session.add(ottelu)
        self.session.commit()
        return ottelu.ottelunumero

    def update_match(self, ottelunumero, params):
        ottelu = self.get_match_by_ottelunumero(ottelunumero)

        if ottelu is not None:
            if 'kotijoukkue' in params:
                if ottelu.kotijoukkue == ottelu.nykyinen_lyontivuoro:
                    ottelu.nykyinen_lyontivuoro = params['kotijoukkue']
                ottelu.kotijoukkue = params['kotijoukkue']
            if 'vierasjoukkue' in params:
                if ottelu.vierasjoukkue == ottelu.nykyinen_lyontivuoro:
                    ottelu.nykyinen_lyontivuoro = params['vierasjoukkue']
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

                # jakso_txt- ja vuoropari_txt-sarakkeita ei enää kirjoiteta.
                # Näkyvä teksti muodostetaan numeroista renderöintihetkellä
                # (app/manuaali.py), jotta molemmat taulut käyttävät samoja
                # tekstejä. Sarakkeet on jätetty kantaan koskematta.
                if params['action'] == 'jakso_taakse':
                    if ottelu.jakso_nro > 1:
                        ottelu.jakso_nro = ottelu.jakso_nro - 1
                        ottelu.vuoropari_nro = 1

                if params['action'] == 'jakso_eteenpain':
                    if ottelu.jakso_nro < JAKSOJA:
                        ottelu.jakso_nro = ottelu.jakso_nro + 1
                        ottelu.vuoropari_nro = 1

                if params['action'] == 'vuoropari_taakse':
                    if ottelu.vuoropari_nro > 1:
                        ottelu.vuoropari_nro = ottelu.vuoropari_nro - 1
                        self.vaihda_lyontivuoro(ottelu)

                if params['action'] == 'vuoropari_eteenpain':
                    if ottelu.vuoropari_nro < VUOROPAREJA:
                        ottelu.vuoropari_nro = ottelu.vuoropari_nro + 1
                        self.vaihda_lyontivuoro(ottelu)

                if params['action'] == 'vaihda_lyontivuoro':
                    self.vaihda_lyontivuoro(ottelu)
            try:
                self.engine.echo = False
                self.session.commit()
                return True
            except IntegrityError as e:
                self.session.rollback()
                print(e)
                return False
            except Exception as e:
                print(e)
            
            finally:
                self.close_connection()
        return False

    def vaihda_lyontivuoro(self, ottelu):
        if ottelu:
            if ottelu.nykyinen_lyontivuoro == ottelu.kotijoukkue:
                ottelu.nykyinen_lyontivuoro = ottelu.vierasjoukkue
            else:
                ottelu.nykyinen_lyontivuoro = ottelu.kotijoukkue
