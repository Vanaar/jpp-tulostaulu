from flask import request, redirect, render_template, Blueprint
from app.db import Database, get_db

routes_bp = Blueprint('routes', __name__)

@routes_bp.route("/uusi")
def uusi_ottelu():
    db = get_db()
    uusi_ottelu = db.uusi_ottelu()
    return redirect(f'/paivita/{uusi_ottelu}')

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
        return render_template('tulostaulu.html', ottelu=ottelu)   
    else:
     #kirjoitetaan tähän myöhemmin käsittely sille, että haetaan ottelu pesistulokset.fi:stä
     pass
    
