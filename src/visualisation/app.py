import sys
import os
from flask import Flask, render_template, request, jsonify
from services.routes_geom import extraire_infos_itineraire
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from algorithms import test_formalisation
from algorithms import calculer_itineraire

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculer', methods=['POST'])
def calculer_itineraire_route():
    data = request.get_json()
    ville_depart = data.get('depart')
    ville_arrivee = data.get('arrivee')

    if not ville_depart or not ville_arrivee:
        return jsonify({"erreur": "Veuillez remplir les deux villes"}), 400

    # Appeler l'algorithme avec les données du HTML
    resultats = calculer_itineraire(ville_depart, ville_arrivee)
    
    if not resultats:
        return jsonify({"erreur": "Aucun itinéraire trouvé"}), 404
    
    chemin = resultats[0]["Chemin"]
    carto_data = extraire_infos_itineraire(chemin)

    return jsonify({
        "itineraire": resultats[0],
        "cartographie": carto_data
    })

# Code par défaut (optionnel)
if __name__ == "__main__":
    User_Départ = "Toulouse_26686518"
    User_Destination = "Tarbes_26691527"
    resultats = calculer_itineraire(User_Départ, User_Destination)
    print(resultats)
    app.run(debug=True, port=5000)