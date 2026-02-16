import sys
import os
import json
import math
import gdown
from flask import Flask, render_template, request, jsonify

# --- GESTION DES CHEMINS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # src/visualisation
SRC_DIR = os.path.dirname(CURRENT_DIR)                  # src
ROOT_DIR = os.path.dirname(SRC_DIR)                     # /

# On ajoute SRC au path pour que "from algorithms import..." fonctionne
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# --- TELECHARGEMENT DES DONNÉES ---
files_to_download = {
    "ma_base.db": "1ZE2ECaY0n_VQ6ACpqtOoOFZCRQRp0MsC",
    "dico_final.json": "1AJp7sN1q8Wnms-yUoZCChZ1jhdvNcCcv",
    "routes_ville_adj.json": "1sl727G5IH2atDdTveCyr4pz7Eb8rPRpW",
    "coords_villes.json": "1or2XZVj59nWH1B95433uUFIFjOU9cjpW"
}

def download_data():
    print("Verification des fichiers de données...")
    for filename, drive_id in files_to_download.items():
        # On force le stockage dans src/visualisation/
        destination = os.path.join(CURRENT_DIR, filename)
        
        if not os.path.exists(destination):
            print(f"Téléchargement de {filename}...")
            gdown.download(id=drive_id, output=destination, quiet=False)
        else:
            print(f"{filename} est déjà présent.")

download_data()

# --- IMPORTS DE VOS MODULES ---
try:
    from algorithms import calculer_itineraire
    from map import maping
    from services.routes_geom import extraire_infos_itineraire
    print(f"Modules chargés avec succès.")
except ImportError as e:
    print(f"\n ERREUR CRITIQUE D'IMPORT : {e}")
    def calculer_itineraire(d, a): return []
    def extraire_infos_itineraire(l): return {"villes": {}, "routes": []}

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

# --- CHARGEMENT DU JSON DES VILLES ---
app = Flask(__name__)

path_coords = os.path.join(os.path.dirname(__file__), "coords_villes.json")
DATA_VILLES = {}

if os.path.exists(path_coords):
    with open(path_coords, 'r', encoding='utf-8') as f:
        DATA_VILLES = json.load(f)
else:
    print(f"ATTENTION : Fichier introuvable à {path_coords}")

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recherche_ville', methods=['POST'])
def api_recherche():
    nom = request.json.get('nom', '').strip().lower()
    res = []
    for kid, v in DATA_VILLES.items():
        v_nom = v.get('nom_affichage', kid.split('_')[0])
        if v_nom.lower() == nom:
            res.append({'id': kid, 'nom': v_nom, 'lat': v['lat'], 'lon': v['lon']})
    return jsonify(res)

@app.route('/api/calculer', methods=['POST'])
def api_calcul():
    data = request.json
    try:
        depart = data['depart']
        arrivee = data['arrivee']
        
        try:
            resultats_algo = calculer_itineraire(depart, arrivee)
        except RecursionError:
            print(f"Récursion infinie détectée avec {depart} -> {arrivee}")
            print(f"Tentative en sens inverse : {arrivee} -> {depart}")
            
            resultats_algo = calculer_itineraire(arrivee, depart)
            
            for result in resultats_algo:
                result['Chemin'] = result['Chemin'][::-1]
        
        if not resultats_algo:
            return jsonify({'erreur': 'Aucun chemin trouvé.'}), 404

        best = resultats_algo[0]
        chemin = best.get('Chemin', [])
        
        dist = best.get('distance') or best.get('Distance_reelle') or 0
        tps_raw = best.get('temps') or best.get('Temps_reel') or 0
        
        try:
            geo_infos = extraire_infos_itineraire(chemin)
            print(f"Géométrie récupérée : {len(geo_infos['villes'])} villes, {len(geo_infos['routes'])} routes")
        except Exception as e:
            print(f"Erreur lors de la récupération de la géométrie : {e}")
            import traceback
            traceback.print_exc()
            geo_infos = {"villes": {}, "routes": []}
        
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
        print(f"Erreur API : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erreur': str(e)}), 500

if __name__ == '__main__':
    print("Serveur lancé : http://127.0.0.1:5000")
    app.run(debug=True, port=5000)