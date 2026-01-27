from flask import Flask, render_template, request, jsonify
import algo_a_star

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

    resultats = algo_a_star.trouver_chemins(ville_depart, ville_arrivee)

    return jsonify({
        "requete": {"de": ville_depart, "vers": ville_arrivee},
        "chemins_trouves": resultats
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)