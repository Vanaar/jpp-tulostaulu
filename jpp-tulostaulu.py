from flask import Flask
from app.routes import routes_bp
from app.models import Otteludata

app = Flask(__name__, template_folder='./app/templates', static_folder='static')
app.register_blueprint(routes_bp)

otteludata = Otteludata()

@app.route("/")
def jpp_tulostaulu():
    return "<p>JunnutPelaaPesistä-tulostaulu</p>"