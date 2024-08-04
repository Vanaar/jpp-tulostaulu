# db.py
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, ResourceClosedError
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import Session
from app.functions import debug_message
from app.functions import lataa_www_sivu
from app.functions import vuoropari_int_to_str
from app.functions import jakso_into_to_str
from app.functions import parsi_x_palot
from app.functions import parsi_jaksonumero
from app.models import Otteludata
from flask import g, current_app
from config import Config
from bs4 import BeautifulSoup

import inspect
import time
import constants

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

        
        url = f"https://v2.pesistulokset.fi/ottelut/{ottelunumero}#live"
        
        tulossivu = lataa_www_sivu(url)

        soup = BeautifulSoup(tulossivu, "html.parser")
        kotijoukkue = soup.find_all("div", class_="match-team team-home flexbox")[0].find("h3").text.strip()
        vierasjoukkue = soup.find_all("div", class_="match-team team-away flexbox")[0].find("h3").text.strip()

        ottelun_kirjaus_on_alkanut = False
        ottelu_on_jaksopeli = False

        tulostaulu = soup.find('div', {'class': 'match-online-result content-box'})
        
        if tulostaulu is not None:
            ottelun_kirjaus_on_alkanut = True
                 
        if not ottelun_kirjaus_on_alkanut:
            ottelu.kotijoukkue = kotijoukkue
            ottelu.vierasjoukkue = vierasjoukkue
            ottelu.otteluinfo = "Ottelu ei ole alkanut"
            return self.commit(ottelu)
            

        #Alustetaan jaksomuuttujat
        j1_koti_yht = 0
        j1_vieras_yht = 0
        j2_koti_yht = None
        j2_vieras_yht = None
        sv_koti_yht = None
        sv_vieras_yht = None
        k_koti_yht = None
        k_vieras_yht = None
        koti_jaksovoitot = None
        vieras_jaksovoitot = None
        
        if ottelun_kirjaus_on_alkanut:
        
            try:
                
                jaksovoitot = tulostaulu.find_all('div', {'class': 'period period-total'})                
                koti_jaksovoitot = jaksovoitot[0].find('div', {'class': 'inning total'}).text.strip()
                vieras_jaksovoitot = jaksovoitot[1].find('div', {'class': 'inning total'}).text.strip()
                ottelu_on_jaksopeli = True
            
            except (AttributeError, IndexError):
                koti_jaksovoitot = None
                vieras_jaksovoitot = None
                ottelu_on_jaksopeli = False

            koti_tulokset = tulostaulu.find('div', {'class': 'home team'})
            vieras_tulokset = tulostaulu.find('div', {'class': 'away team'})

            # Jakso 1 löytyy aina
            j1_koti_yht = koti_tulokset.find('div', {'class': 'period period-0'}).find('div', {'class': 'inning total'}).text.strip()
            if j1_koti_yht == '':
                j1_koti_yht = None

            j1_vieras_yht = vieras_tulokset.find('div', {'class': 'period period-0'}).find('div', {'class': 'inning total'}).text.strip()
            if j1_vieras_yht == '':
                j1_vieras_yht = None

            if ottelu_on_jaksopeli:
                
                ottelu.otteluinfo = ""

                j2_koti_yht = koti_tulokset.find('div', {'class': 'period period-1'}).find('div', {'class': 'inning total'}).text.strip()
                if j2_koti_yht == '':
                    j2_koti_yht = None
                
                j2_vieras_yht = vieras_tulokset.find('div', {'class': 'period period-1'}).find('div', {'class': 'inning total'}).text.strip()
                if j2_vieras_yht == '':
                    j2_vieras_yht = None
                
                #Supervuoro    
                if koti_tulokset.find('div', {'class': 'period period-2'}):
                    if koti_tulokset.find('div', {'class': 'period period-2'}).find('a', {'class': 'inning'}):
                        sv_koti_yht = koti_tulokset.find('div', {'class': 'period period-2'}).find('a', {'class': 'inning'}).text.strip()
                        sv_vieras_yht = vieras_tulokset.find('div', {'class': 'period period-2'}).find('a', {'class': 'inning'}).text.strip()
                    if sv_koti_yht == '':
                        sv_koti_yht = None
                    if sv_vieras_yht == '':
                        sv_vieras_yht = None

                #Kotari
                if koti_tulokset.find('div', {'class': 'period period-3'}).find('a', {'class': 'inning'}):
                    k_koti_yht = koti_tulokset.find('div', {'class': 'period period-3'}).find('a', {'class': 'inning'}).text.strip()
                    k_vieras_yht = vieras_tulokset.find('div', {'class': 'period period-3'}).find('a', {'class': 'inning'}).text.strip()
                    if k_koti_yht == '':
                        k_koti_yht = None
                    if k_vieras_yht == '':
                        k_vieras_yht = None
                                
            else:
                ottelu.otteluinfo = "Junioriottelu"
                    
        ottelu.kotijoukkue = kotijoukkue
        ottelu.vierasjoukkue = vierasjoukkue
        ottelu.jakso_1_koti_juoksut = j1_koti_yht
        ottelu.jakso_1_vieras_juoksut = j1_vieras_yht
        ottelu.jakso_2_koti_juoksut = j2_koti_yht
        ottelu.jakso_2_vieras_juoksut = j2_vieras_yht
        ottelu.jakso_3_koti_juoksut = sv_koti_yht
        ottelu.jakso_3_vieras_juoksut = sv_vieras_yht
        ottelu.jakso_4_koti_juoksut = k_koti_yht
        ottelu.jakso_4_vieras_juoksut = k_vieras_yht
        ottelu.koti_jaksovoitot = koti_jaksovoitot
        ottelu.vieras_jaksovoitot = vieras_jaksovoitot
        
        #nykyinen vuoropari
        if soup.find('div', {'class': 'online-match-current-inning-events'}):
            vuoropari_element = soup.find('div', {'class': 'online-match-current-inning-events'})
            first_span = vuoropari_element.find_all('span')[0]
            last_span = vuoropari_element.find_all('span')[-1]
            vuoropari_txt = last_span.text
            if first_span.text.strip() == "Ottelu päättyi":
                vuoropari_txt = "Ottelu päättynyt"
        else:
            vuoropari_txt = "-"
        ottelu.vuoropari_txt = vuoropari_txt
 
 
        ottelu.nykyinen_lyontivuoro = "-"
        if koti_tulokset.find('a', {'class': 'inning current'}):
            ottelu.nykyinen_lyontivuoro = ottelu.kotijoukkue
            jakso_div = koti_tulokset.find('a', {'class': 'inning current'}).parent.parent
            
        elif vieras_tulokset.find('a', {'class': 'inning current'}):
            ottelu.nykyinen_lyontivuoro = ottelu.vierasjoukkue
            jakso_div = vieras_tulokset.find('a', {'class': 'inning current'}).parent.parent
       
        jakso = parsi_jaksonumero(jakso_div)
            
        ottelu.jakso_nro = jakso
        ottelu.jakso_txt = jakso_into_to_str(jakso)        
        
        #palot
#        try:
#            palot = soup.find('div', {'class': 'outs'})
#            palot = len(palot.find_all('span'))
#            ottelu.palot = parsi_x_palot(palot)
#        except AttributeError:
#            ottelu.palot = ""


### Haetaan palot uudella tavalla

        try:
            palot = soup.find('div', {'class': 'right-side out'})
            paloja = palot.text.count('×')
            ottelu.palot = parsi_x_palot(paloja)
        except AttributeError:
            ottelu.palot = ""
        
        debug_message("Data parsittu. Päivitetään kantarivi...", constants.DEBUG_MESSAGE_LEVEL_INFO)
        return self.commit(ottelu)
        
