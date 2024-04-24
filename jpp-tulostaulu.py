from flask import Flask, g, render_template
from app.routes import routes_bp
from app.models import Otteludata

app = Flask(__name__, template_folder='./app/templates', static_folder='static')
app.register_blueprint(routes_bp)

otteludata = Otteludata()

@app.route("/")
def jpp_tulostaulu():
    return render_template('index.html')

#@app.teardown_appcontext
#def teardown_db(exception):
#    db = g.pop('db', None)
#    if db is not None:
#        db.close()

if __name__ == "__main__":
    app.run(debug=True)