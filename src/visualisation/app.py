import sys
import os
import json
import math
import gdown
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)

for path in [CURRENT_DIR, SRC_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

files_to_download = {
    "ma_base.db": "1ZE2ECaY0n_VQ6ACpqtOoOFZCRQRp0MsC",
    "dico_final.json": "1AJp7sN1q8Wnms-yUoZCChZ1jhdvNcCcv",
    "routes_ville_adj.json": "1sl727G5IH2atDdTveCyr4pz7Eb8rPRpW",
    "coords_villes.json": "1or2XZVj59nWH1B95433uUFIFjOU9cjpW"
}

def download_data():
    print("Verification des fichiers de données...")
    for filename, drive_id in files_to_download.items():
        destination = os.path.join(CURRENT_DIR, filename)
        
        if not os.path.exists(destination):
            print(f"Téléchargement de {filename}...")
            try:
                gdown.download(id=drive_id, output=destination, quiet=False)
            except Exception as e:
                print(f"Erreur de téléchargement pour {filename}: {e}")
        else:
            print(f"{filename} est déjà présent.")

download_data()

try:
    from algorithms import calculer_itineraire
    from map import maping

    from services.routes_geom import extraire_infos_itineraire
    
    print(f"Modules chargés avec succès. Graphe contenant {len(maping)} entrées.")

except ImportError as e:
    print(f"\n ERREUR CRITIQUE D'IMPORT : {e}")
    print(f"Sys Path actuel : {sys.path}")
    def calculer_itineraire(d, a): return []
    def extraire_infos_itineraire(l): return {"villes": {}, "routes": []}
    maping = {}

def calculer_distance_reelle(chemin):
    if not chemin or len(chemin) < 2:
        return 0
    
    distance_totale = 0
    try:
        for i in range(len(chemin) - 1):
            ville_depart = chemin[i]
            ville_arrivee = chemin[i + 1]
            
            if ville_depart in maping and ville_arrivee in maping[ville_depart]:
                distance_pair = maping[ville_depart][ville_arrivee]
                km = distance_pair[0]
                distance_totale += km
    except (KeyError, IndexError, TypeError) as e:
        print(f"Erreur lors du calcul de distance : {e}")
    
    return round(distance_totale, 2)

def calculer_temps_reel(chemin):
    if not chemin or len(chemin) < 2:
        return 0
    
    temps_total = 0
    try:
        for i in range(len(chemin) - 1):
            ville_depart = chemin[i]
            ville_arrivee = chemin[i + 1]
            
            if ville_depart in maping and ville_arrivee in maping[ville_depart]:
                distance_pair = maping[ville_depart][ville_arrivee]
                temps = distance_pair[1]
                temps_total += temps
    except (KeyError, IndexError, TypeError) as e:
        print(f"Erreur lors du calcul de temps : {e}")
    
    return round(temps_total, 2)

def formatter_temps(minutes):
    try:
        minutes = float(minutes)
        if minutes < 60:
            return f"{int(minutes)} min"
        else:
            heures = int(minutes // 60)
            rest_min = int(minutes % 60)
            return f"{heures} h {rest_min:02d} min"
    except (ValueError, TypeError):
        return "0 min"

app = Flask(__name__, 
            template_folder=os.path.join(CURRENT_DIR, 'templates'),
            static_folder=os.path.join(CURRENT_DIR, 'static'))

CORS(app)

path_coords = os.path.join(CURRENT_DIR, "coords_villes.json")
DATA_VILLES = {}

if os.path.exists(path_coords):
    try:
        with open(path_coords, 'r', encoding='utf-8') as f:
            DATA_VILLES = json.load(f)
    except json.JSONDecodeError:
        print("Erreur de lecture du JSON coords_villes.")
else:
    print(f"ATTENTION : Fichier introuvable à {path_coords}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recherche_ville', methods=['POST'])
def api_recherche():
    nom = request.json.get('nom', '').strip().lower()
    res = []
    if not nom: 
        return jsonify([])

    for kid, v in DATA_VILLES.items():
        v_nom = v.get('nom_affichage', kid.split('_')[0])
        if v_nom.lower().startswith(nom):
             res.append({'id': kid, 'nom': v_nom, 'lat': v['lat'], 'lon': v['lon']})
        elif v_nom.lower() == nom:
             res.append({'id': kid, 'nom': v_nom, 'lat': v['lat'], 'lon': v['lon']})
             
    return jsonify(res[:10])

@app.route('/api/calculer', methods=['POST'])
def api_calcul():
    data = request.json
    try:
        depart = data.get('depart')
        arrivee = data.get('arrivee')
        
        if not depart or not arrivee:
            return jsonify({'erreur': 'Villes de départ ou d\'arrivée manquantes.'}), 400

        try:
            resultats_algo = calculer_itineraire(depart, arrivee)
        except RecursionError:
            print(f"Récursion infinie détectée avec {depart} -> {arrivee}")
            print(f"Tentative en sens inverse : {arrivee} -> {depart}")
            resultats_algo = calculer_itineraire(arrivee, depart)
            for result in resultats_algo:
                if 'Chemin' in result:
                    result['Chemin'] = result['Chemin'][::-1]
        
        if not resultats_algo:
            return jsonify({'erreur': 'Aucun chemin trouvé.'}), 404

        best = resultats_algo[0]
        chemin = best.get('Chemin', [])
        
        dist = best.get('distance') or best.get('Distance_reelle') or 0
        tps_raw = best.get('temps') or best.get('Temps_reel') or 0
        
        geo_infos = {"villes": {}, "routes": []}
        try:
            geo_infos = extraire_infos_itineraire(chemin)
            print(f"Géométrie récupérée : {len(geo_infos.get('villes', {}))} villes")
        except Exception as e:
            print(f"Erreur lors de la récupération de la géométrie : {e}")
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'itineraire': {
                'distance': dist,
                'temps_raw': tps_raw,
                'temps_formate': formatter_temps(tps_raw),
                'chemin': chemin,
                'villes': geo_infos.get('villes', {}),
                'routes': geo_infos.get('routes', [])
            }
        })

    except Exception as e:
        print(f"Erreur API Globale : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erreur': str(e)}), 500

if __name__ == '__main__':
    print("Serveur lancé : http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
