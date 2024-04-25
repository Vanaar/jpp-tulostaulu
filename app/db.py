# database.py
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, ResourceClosedError
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import Session
from app.functions import debug_message
from app.functions import lataa_www_sivu
from app.models import Otteludata
from flask import g, current_app
from config import Config
from app.functions import vuoropari_int_to_str
from app.functions import jakso_into_to_str
from bs4 import BeautifulSoup
from selenium import webdriver

import inspect
import time
import constants


#
#def get_db():
#    if 'db' not in current_app.config:
#        current_app.config['db'] = Database(Config.SQLALCHEMY_DATABASE_URI)
#    return current_app.config['db']

#
def get_db():
    if 'db' not in g:
        g.db = Database(Config.SQLALCHEMY_DATABASE_URI)
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
            if ottelu:
                return ottelu
            else:
                debug_message(f"Ottelua {ottelunumero} ei löytynyt kannasta")
                return False
        except ResourceClosedError as e:
            debug_message(f"ResourceClosedError: {e}", constants.DEBUG_MESSAGE_LEVEL_ERROR)
            return False
        except Exception as e:
            debug_message(f"Error: {e}", constants.DEBUG_MESSAGE_LEVEL_ERROR)
            return False
        
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

        if ottelu:
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
                    if ottelu.vuoropari_nro < 14:
                        ottelu.vuoropari_nro = ottelu.vuoropari_nro + 1
                        ottelu.vuoropari_txt = vuoropari_int_to_str(ottelu.vuoropari_nro)
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

    def lataaOtteludataPesistuloksista(self, ottelunumero, ottelu=None):
        debug_message(f"lataaOtteludataPesistuloksista({ottelunumero}) called by: {inspect.stack()[1].function}", constants.DEBUG_MESSAGE_LEVEL_INFO)
        
        if ottelu is None:
            ottelu = self.get_match_by_ottelunumero(ottelunumero)

        
        url = f"https://www.pesistulokset.fi/ottelut/{ottelunumero}#live"
        
        tulossivu = lataa_www_sivu(url)

        soup = BeautifulSoup(tulossivu, "html.parser")
        kotijoukkue = soup.find_all('div', {'class': 'match-detail-team'})[0].find_all('a')[1].text.strip()
        vierasjoukkue = soup.find_all('div', {'class': 'match-detail-team'})[1].find('a').text.strip()

        ottelun_kirjaus_on_alkanut = False
        ottelu_on_jaksopeli = False

        tulostaulu = soup.find('div', {'class': 'live-result-board'})
        
        if tulostaulu is not None:
            ottelun_kirjaus_on_alkanut = True
                 
        if not ottelun_kirjaus_on_alkanut:
            ottelu.kotijoukkue = kotijoukkue
            ottelu.vierasjoukkue = vierasjoukkue
            ottelu.otteluinfo = "Ottelu ei ole alkanut"
            return self.commit(ottelu)
            

        #Alustetaan jaksomuuttujat
        j1_koti = None
        j1_koti_yht = 0
        j1_vieras = None
        j1_vieras_yht = 0
        j2_koti = None
        j2_koti_yht = None
        j2_vieras = None
        j2_vieras_yht = None
        j3_koti = None
        j3_koti_yht = None
        j3_vieras = None
        j3_vieras_yht = None
        j4_koti = None
        j4_koti_yht = None
        j4_vieras = None
        j4_vieras_yht = None
        koti_jaksovoitot = None
        vieras_jaksovoitot = None
        
        if ottelun_kirjaus_on_alkanut:
        
            try:
                
                jaksovoitot = tulostaulu.find('div', {'class': 'period-total'}).find_all('div', {'class': 'inning'})
                koti_jaksovoitot = jaksovoitot[0].text.strip()
                vieras_jaksovoitot = jaksovoitot[1].text.strip()
                ottelu_on_jaksopeli = True
                
            except AttributeError:
                koti_jaksovoitot = None
                vieras_jaksovoitot = None
                ottelu_on_jaksopeli = False

            j1_koti = tulostaulu.find_next('div', {'class': 'innings home d-flex'})
            j1_koti_pisteet = j1_koti.find_all('a', {'class': 'inning'})
            j1_koti_yht = j1_koti.find('div', {'class': 'inning'}).text.strip()
            if j1_koti_yht == '':
                j1_koti_yht = None

            j1_vieras = tulostaulu.find_next('div', {'class': 'innings away d-flex'})
            j1_vieras_pisteet = j1_vieras.find_all('a', {'class': 'inning'})
            j1_vieras_yht = j1_vieras.find('div', {'class': 'inning'}).text.strip()
            if j1_vieras_yht == '':
                j1_vieras_yht = None

            if ottelu_on_jaksopeli:
                
                ottelu.otteluinfo = ""

                j2_koti = j1_koti.find_next('div', {'class': 'innings home d-flex'})
                j2_koti_pisteet = j2_koti.find_all('a', {'class': 'inning'})
                j2_koti_yht = j2_koti.find('div', {'class': 'inning'}).text.strip()
                if j2_koti_yht == '':
                    j2_koti_yht = None

                j2_vieras = j1_vieras.find_next('div', {'class': 'innings away d-flex'})
                j2_vieras_pisteet = j2_vieras.find_all('a', {'class': 'inning'})
                j2_vieras_yht = j2_vieras.find('div', {'class': 'inning'}).text.strip()
                if j2_vieras_yht == '':
                    j2_vieras_yht = None
            

                j3_koti = j2_koti.find_next('div', {'class': 'innings home d-flex'})
                j3_koti_yht = j3_koti.find('a', {'class': 'inning'}).text.strip()
                if j3_koti_yht == '':
                    j3_koti_yht = None

                j3_vieras = j2_vieras.find_next('div', {'class': 'innings away d-flex'})
                j3_vieras_yht = j3_vieras.find('a', {'class': 'inning'}).text.strip()
                if j3_vieras_yht == '': 
                    j3_vieras_yht = None

                j4_koti = j3_koti.find_next('div', {'class': 'innings home d-flex'})
                j4_koti_yht = j4_koti.find('a', {'class': 'inning'}).text.strip()
                if j4_koti_yht == '':    
                    j4_koti_yht = None

                j4_vieras = j3_vieras.find_next('div', {'class': 'innings away d-flex'})
                j4_vieras_yht = j4_vieras.find('a', {'class': 'inning'}).text.strip()
                if j4_vieras_yht == '':
                    j4_vieras_yht = None
            else:
                ottelu.otteluinfo = "Junioriottelu"
                    
        ottelu.kotijoukkue = kotijoukkue
        ottelu.vierasjoukkue = vierasjoukkue
        ottelu.jakso_1_koti_juoksut = j1_koti_yht
        ottelu.jakso_1_vieras_juoksut = j1_vieras_yht
        ottelu.jakso_2_koti_juoksut = j2_koti_yht
        ottelu.jakso_2_vieras_juoksut = j2_vieras_yht
        ottelu.jakso_3_koti_juoksut = j3_koti_yht
        ottelu.jakso_3_vieras_juoksut = j3_vieras_yht
        ottelu.jakso_4_koti_juoksut = j4_koti_yht
        ottelu.jakso_4_vieras_juoksut = j4_vieras_yht
        ottelu.koti_jaksovoitot = koti_jaksovoitot
        ottelu.vieras_jaksovoitot = vieras_jaksovoitot
        
        #nykyinen vuoropari
        vuoropari_txt = soup.find('div', {'class': 'text-muted font-weight-bold text-center'}).text.strip()
        ottelu.vuoropari_txt = vuoropari_txt
        
        #lyöntivuoro
        jakso = 0
        for i, (j_koti, j_vieras) in enumerate(zip([j1_koti, j2_koti, j3_koti, j4_koti], [j1_vieras, j2_vieras, j3_vieras, j4_vieras]), start=1):
            if j_koti.find('a', {'class': 'bg-orange'}):
                ottelu.nykyinen_lyontivuoro = ottelu.kotijoukkue
                jakso = i
                break
            elif j_vieras.find('a', {'class': 'bg-orange'}):
                ottelu.nykyinen_lyontivuoro = ottelu.vierasjoukkue
                jakso = i
                break
            
        ottelu.jakso_nro = jakso
        ottelu.jakso_txt = jakso_into_to_str(jakso)
        
        #palot
        try:
            palot = soup.find('div', {'class': ['out', 'text-danger']}).text.strip()
            ottelu.palot = palot.upper()
        except AttributeError:
            ottelu.palot = ""
        
        return self.commit(ottelu)
        
    def commit(self, ottelu):
        try:
            self.engine.echo = False
            debug_message("Data parsed. Inserting...", constants.DEBUG_MESSAGE_LEVEL_INFO)
            self.session.commit()
            return ottelu
        except IntegrityError as e:
            self.session.rollback()
            print(e)
            return False
        except Exception as e:
            print(e)
            return False