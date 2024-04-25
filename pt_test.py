import time
from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
from app.functions import parsi_x_palot

url = f"https://www.pesistulokset.fi/ottelut/76285#live"

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.get(url)
time.sleep(1)
page_content = driver.page_source
driver.quit()

soup = BeautifulSoup(page_content, "html.parser")

kotijoukkue = soup.find_all('div', {'class': 'match-detail-team'})[0].find_all('a')[1].text.strip()
vierasjoukkue = soup.find_all('div', {'class': 'match-detail-team'})[1].find('a').text.strip()

tulostaulu = soup.find('div', {'class': 'live-result-board'})
j1_koti = tulostaulu.find_next('div', {'class': 'innings home d-flex'})
j1_koti_pisteet = j1_koti.find_all('a', {'class': 'inning'})
j1_koti_yht = j1_koti.find('div', {'class': 'inning'}).text.strip()

j1_vieras = tulostaulu.find_next('div', {'class': 'innings away d-flex'})
j1_vieras_pisteet = j1_vieras.find_all('a', {'class': 'inning'})
j1_vieras_yht = j1_vieras.find('div', {'class': 'inning'}).text.strip()

j2_koti = j1_koti.find_next('div', {'class': 'innings home d-flex'})
j2_koti_pisteet = j2_koti.find_all('a', {'class': 'inning'})
j2_koti_yht = j2_koti.find('div', {'class': 'inning'}).text.strip()

j2_vieras = j1_vieras.find_next('div', {'class': 'innings away d-flex'})
j2_vieras_pisteet = j2_vieras.find_all('a', {'class': 'inning'})
j2_vieras_yht = j2_vieras.find('div', {'class': 'inning'}).text.strip()


j3_koti = j2_koti.find_next('div', {'class': 'innings home d-flex'})
j3_koti_yht = j3_koti.find('a', {'class': 'inning'}).text.strip()

j3_vieras = j2_vieras.find_next('div', {'class': 'innings away d-flex'})
j3_vieras_yht = j3_vieras.find('a', {'class': 'inning'}).text.strip()

j4_koti = j3_koti.find_next('div', {'class': 'innings home d-flex'})
j4_koti_yht = j4_koti.find('a', {'class': 'inning'}).text.strip()

j4_vieras = j3_vieras.find_next('div', {'class': 'innings away d-flex'})
j4_vieras_yht = j4_vieras.find('a', {'class': 'inning'}).text.strip()

jaksovoitot = tulostaulu.find('div', {'class': 'period-total'}).find_all('div', {'class': 'inning'})
koti_jaksovoitot = jaksovoitot[0]
vieras_jaksovoitot = jaksovoitot[1]

#nykyinen vuoropari
vuoropari_txt = soup.find('div', {'class': 'text-muted font-weight-bold text-center'}).text.strip()

#Etsitään lyöntivuoro ja aktiivinen jakso

jakso = 0
for i, (j_koti, j_vieras) in enumerate(zip([j1_koti, j2_koti, j3_koti, j4_koti], [j1_vieras, j2_vieras, j3_vieras, j4_vieras]), start=1):
    if j_koti.find('a', {'class': 'bg-orange'}):
        print(f"bg-orange has been found in j{i}_koti")
        print(j_koti.find('a', {'class': 'bg-orange'}).text.strip())
        jakso = i
        break
    elif j_vieras.find('a', {'class': 'bg-orange'}):
        print(f"bg-orange has been found in j{i}_vieras")
        print(j_vieras.find('a', {'class': 'bg-orange'}).text.strip())
        jakso = i
        break


    
    palot = soup.find('div', {'class': ['out', 'text-danger']}).text.strip()

print(j1_koti_yht)
print(j1_vieras_yht)
print(j3_koti_yht)
print(j3_vieras_yht)
print(j4_koti_yht)
print(j4_vieras_yht)
print(koti_jaksovoitot.text.strip())
print(vieras_jaksovoitot.text.strip())
print(vuoropari_txt)
print("Tutkitaan palot...")
if palot.islower():
    print("Palot ({palot}) is fully lowercase")
    palot = palot.upper()
    if palot.upper():
        print(f"Palot ({palot}) is now uppercase")
    else:
        print(f"Palot ({palot}) is still not uppercase")
    print(f"Palot: {palot}")
else:
    print("Palot is not fully lowercase")
    if palot.isupper():
        print("Palot is fully uppercase")
        palot = palot.lower()
        if palot.lower():
            print(f"Palot ({palot}) is now lowercase")
        else:
            print(f"Palot ({palot}) is still not lowercase")
    else:
        print("Palot is not fully uppercase")
        palot = palot.lower()
        if palot.lower():
            print(f"Palot ({palot}) is now lowercase")
        else:
            print(f"Palot ({palot}) is still not lowercase")
            
print("Palo length:")
print(len(palot))
print(parsi_x_palot(len(palot)))

