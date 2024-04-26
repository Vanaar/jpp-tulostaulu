from flask import request, redirect, render_template, Blueprint
from app.db import Database, get_db
from config import Config
from app.functions import debug_message
from bs4 import BeautifulSoup
from selenium import webdriver

import requests
import time


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
    #Onko debug GET-parametreissä päällä?
    debug = request.args.get('debug', 'off')
    
    db = get_db()
    
    # Yritetään ensin löytää ottelu tietokannasta
    ottelu = db.get_match_by_ottelunumero(ottelunumero)
    
    otteluKannassa = False
    
    if ottelu:
        otteluKannassa = True
        if (ottelu.pesistulokset == 1): #Otteludataa päivitetään pesistulokset.fi:stä
            return render_template('ottelu.html', ottelu=ottelu, pesistulokset=True, debug=debug)
        return render_template('ottelu.html', ottelu=ottelu, pesistulokset=False, debug=debug)   
    else:
        #Tarkistaan löytyykö ottelua pesistulokset.fi:stä
        def is_valid_webpage(url):
            response = requests.get(url)
            if response.status_code == 200:
                return True
            else:
                return False

        if is_valid_webpage(f"https://www.pesistulokset.fi/ottelut/{ottelunumero}"):
            #Lisätään ottelu kantaan
            print(f"Lisätään ottelu kantaan pesistuloksista: {ottelunumero}")
            db.uusi_ottelu(pesistulokset=1, ottelunumero=ottelunumero)
            print(f"Ladataan otteludata pesistuloksista: {ottelunumero}")
            uusi_ottelu = db.lataaOtteludataPesistuloksista(ottelunumero)
            return render_template('ottelu.html', ottelu=uusi_ottelu, pesistulokset=True, debug=debug)           
        else:
            return "Ottelua ei ole tietokannassa eikä myöskään ulkoisessa lähteessä."

@routes_bp.route("/<int:ottelunumero>/tulostaulu", methods=['GET'])
def nayta_tulostaulu(ottelunumero):  
    db = get_db()
    ottelu = db.get_match_by_ottelunumero(ottelunumero)
    debug = request.args.get('debug', 'off')  # Get the debug parameter, default to 'off'
    return render_template('tulostaulu.html', ottelu=ottelu, debug=debug)

@routes_bp.route("/pt/<int:ottelunumero>", methods=['GET'])
def lataa_otteludata_pesistuloksista(ottelunumero):
    db = get_db()
    print(f"Route PT: Ladataan otteludata pesistuloksista: {ottelunumero}")
#    try:
    ottelu = db.lataaOtteludataPesistuloksista(ottelunumero)

    return f"Otteludatan lataus ajettu: {time.strftime('%Y-%m-%d %H:%M:%S')}"
#    except Exception as e:
#        return f"Virhedd: {e}"
    
