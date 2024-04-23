from flask import request, redirect, render_template, Blueprint
from app.db import Database, get_db
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver

routes_bp = Blueprint('routes', __name__)

@routes_bp.route("/uusi")
def uusi_ottelu():
    db = get_db()
    uusi_ottelu = db.uusi_ottelu()
    return redirect(f'/paivita/{uusi_ottelu}')

@routes_bp.route("/hellurei")
def hellurei():
    return "Oujee!"

@routes_bp.route("/paivita/<int:ottelunumero>/<int:muokattava_osio>", methods=['GET', 'POST'])
@routes_bp.route("/paivita/<int:ottelunumero>", defaults={'muokattava_osio': 0}, methods=['GET', 'POST'])
def paivita_ottelu(ottelunumero, muokattava_osio):
    if muokattava_osio < 0 or muokattava_osio is None:
        muokattava_osio = 0
    elif muokattava_osio > 4:
        muokattava_osio = 4
    
    db = get_db()
    if request.method == 'POST':
        db.update_match(ottelunumero, request.form)
        
    ottelu = db.get_match_by_ottelunumero(ottelunumero)
    if ottelu:
        return render_template('update_ottelu.html', ottelu=ottelu, muokattava_osio=muokattava_osio)
    else:
        return "Ottelua ei löydy tällä numerolla."

@routes_bp.route("/<int:ottelunumero>", methods=['GET'])
def ottelu_tulostaulu(ottelunumero):
    db = get_db()
    
    # Yritetään ensin löytää ottelu tietokannasta
    ottelu = db.get_match_by_ottelunumero(ottelunumero)
    
    if ottelu:
        return render_template('ottelu.html', ottelu=ottelu)   
    else:
     #kirjoitetaan tähän myöhemmin käsittely sille, että haetaan ottelu pesistulokset.fi:stä
     pass

@routes_bp.route("/<int:ottelunumero>/tulostaulu", methods=['GET'])
def nayta_tulostaulu(ottelunumero):  
    db = get_db()
    ottelu = db.get_match_by_ottelunumero(ottelunumero)
    return render_template('tulostaulu.html', ottelu=ottelu)

@routes_bp.route("/pt/<int:ottelunumero>", methods=['GET'])
def tulosta_pt_ottelu(ottelunumero):
    url = f"https://www.pesistulokset.fi/ottelut/{ottelunumero}#live"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(1)
    page_content = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(page_content, "html.parser")
    element = soup.find('div', {'class': 'innings home d-flex'})
    a_elements = element.find_all('a')
    tulos1 = a_elements[0]
    tulos2 = a_elements[1]
    tulos3 = a_elements[2]
    tulos4 = a_elements[3]
    
    return tulos1.text + " - " + tulos2.text + " - " + tulos3.text + " - " + tulos4.text