from flask import Flask, render_template
from app.routes import routes_bp
from app.models import Otteludata

app = Flask(__name__, template_folder='./app/templates', static_folder='static')
app.register_blueprint(routes_bp)

otteludata = Otteludata()

@app.route("/")
def jpp_tulostaulu():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)