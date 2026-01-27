from flask import Flask, render_template, request, jsonify
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from algorithms import test_formalisation
from services.routes_geom import extraire_infos_itineraire

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculer', methods=['POST'])
def calculer_itineraire():
    data = request.get_json()
    ville_depart = data.get('depart')
    ville_arrivee = data.get('arrivee')

    if not ville_depart or not ville_arrivee:
        return jsonify({"erreur": "Veuillez remplir les deux villes"}), 400

    resultats = test_formalisation()

    chemin = resultats[0]["Chemin"]

    carto_data = extraire_infos_itineraire(chemin)

    return jsonify({
        "itineraire": resultats[0],
        "cartographie": carto_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)