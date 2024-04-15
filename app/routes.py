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

@routes_bp.route("/paivita/<int:ottelunumero>", methods=['GET', 'POST'])
def ottelu(ottelunumero):
    db = get_db()
    if request.method == 'POST':
        db.update_match(ottelunumero, request.form)
    #return str(db.get_match_by_ottelunumero(ottelunumero))
    
    return render_template('update_ottelu.html', ottelu=db.get_match_by_ottelunumero(ottelunumero))