import time
from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
from app.functions import parsi_x_palot
from app.functions import parsi_jaksonumero


#url = f"https://v2.pesistulokset.fi/ottelut/85067"
#url = f"https://v2.pesistulokset.fi/ottelut/61144"
url = f"https://v2.pesistulokset.fi/ottelut/94277"

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.get(url)
time.sleep(1)
page_content = driver.page_source
driver.quit()

soup = BeautifulSoup(page_content, "html.parser")

kotijoukkue = soup.find_all("div", class_="match-team team-home flexbox")[0].find("h3").text.strip()

tulostaulu = soup.find('div', {'class': 'match-online-result content-box'})

jaksovoitot = tulostaulu.find_all('div', {'class': 'period period-total'})
jaksovoitot_koti = jaksovoitot[0].find('div', {'class': 'inning total'}).text.strip()
jaksovoitot_vieras = jaksovoitot[1].find('div', {'class': 'inning total'}).text.strip()

koti_tulokset = tulostaulu.find('div', {'class': 'home team'})
vieras_tulokset = tulostaulu.find('div', {'class': 'away team'})

koti_j1_yht = koti_tulokset.find('div', {'class': 'period period-0'}).find('div', {'class': 'inning total'}).text.strip()
vieras_j1_yht = vieras_tulokset.find('div', {'class': 'period period-0'}).find('div', {'class': 'inning total'}).text.strip()

koti_j2_yht = koti_tulokset.find('div', {'class': 'period period-1'}).find('div', {'class': 'inning total'}).text.strip()
vieras_j2_yht = vieras_tulokset.find('div', {'class': 'period period-1'}).find('div', {'class': 'inning total'}).text.strip()

#koti_sv_yht = koti_tulokset.find('div', {'class': 'period period-2'}).find('div', {'class': 'inning total'}).text.strip()
#vieras_sv_yht = vieras_tulokset.find('div', {'class': 'period period-2'}).find('div', {'class': 'inning total'}).text.strip()

koti_sv_yht = None
vieras_sv_yht = None

if koti_tulokset.find('div', {'class': 'period period-2'}):
    if koti_tulokset.find('div', {'class': 'period period-2'}).find('a', {'class': 'inning'}):
        koti_sv_yht = koti_tulokset.find('div', {'class': 'period period-2'}).find('a', {'class': 'inning'}).text.strip()
        vieras_sv_yht = vieras_tulokset.find('div', {'class': 'period period-2'}).find('a', {'class': 'inning'}).text.strip()

koti_k_yht = None
vieras_k_yht = None

if koti_tulokset.find('div', {'class': 'period period-3'}).find('a', {'class': 'inning'}):
    koti_k_yht = koti_tulokset.find('div', {'class': 'period period-3'}).find('a', {'class': 'inning'}).text.strip()
    vieras_k_yht = vieras_tulokset.find('div', {'class': 'period period-3'}).find('a', {'class': 'inning'}).text.strip()

#palot
palot = soup.find('div', {'class': 'outs'})
palot = len(palot.find_all('span'))

vuoropari_element = soup.find('div', {'class': 'online-match-current-inning-events'})
first_span = vuoropari_element.find_all('span')[0]
last_span = vuoropari_element.find_all('span')[-1]

nykyinen_lyontivuoro = "-"
if koti_tulokset.find('a', {'class': 'inning current'}):
    jakso_div = koti_tulokset.find('a', {'class': 'inning current'}).parent.parent
    nykyinen_lyontivuoro = "Koti"
    
elif vieras_tulokset.find('a', {'class': 'inning current'}):
    jakso_div = vieras_tulokset.find('a', {'class': 'inning current'}).parent.parent
    nykyinen_lyontivuoro = "Vieras"
    
jakso = parsi_jaksonumero(jakso_div)
    
print(f"Jaksot koti: {jaksovoitot_koti}")
print(f"Jaksot vieras: {jaksovoitot_vieras}")
print(f"Koti j1 yht: {koti_j1_yht}")
print(f"Vieras j1 yht: {vieras_j1_yht}")
print(f"Koti j2 yht: {koti_j2_yht}")
print(f"Vieras j2 yht: {vieras_j2_yht}")
print(f"Koti sv yht: {koti_sv_yht}")
print(f"Vieras sv yht: {vieras_sv_yht}")
print(f"Koti k yht: {koti_k_yht}")
print(f"Vieras k yht: {vieras_k_yht}")
palot = parsi_x_palot(palot)
print(f"Palot: {palot}")
print(f"Vuoropari: {last_span.text}")
print(f"Lyöntivuoro: {nykyinen_lyontivuoro}")
print(f"Jakso: {jakso}")
print(f"First span: {first_span.text}")
print("Testataanpa josko ottelu on päättynyt")
if first_span.text.strip() == "Ottelu päättyi":
    print("Ottelu on tosiaankin päättynyt")
else:
    print(f"Ohjelma väittää, että \"Ottelu päättyi\" on eri kuin \"{first_span.text}\"")