from flask import request, redirect, render_template, Blueprint
from app.db import Database, get_db

routes_bp = Blueprint('routes', __name__)

@routes_bp.route("/hellurei")
def index():
    return "Hei maailma"

@routes_bp.route("/ottelut")
def ottelut():
    db = get_db()
    matches = db.list_matches()
    return str(matches)

@routes_bp.route("/paivita/<int:ottelunumero>/<int:muokattava_osio>", methods=['GET', 'POST'])
@routes_bp.route("/paivita/<int:ottelunumero>", defaults={'muokattava_osio': 0}, methods=['GET', 'POST'])
def paivita_ottelu(ottelunumero, muokattava_osio):
    db = get_db()
    if request.method == 'POST':
        db.update_match(ottelunumero, request.form)
    #return str(db.get_match_by_ottelunumero(ottelunumero))
    
    return render_template('update_ottelu.html', ottelu=db.get_match_by_ottelunumero(ottelunumero), muokattava_osio=muokattava_osio)