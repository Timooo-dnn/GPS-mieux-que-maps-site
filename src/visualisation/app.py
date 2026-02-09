import sys
import os
import json
import math
from flask import Flask, render_template, request, jsonify

# ==========================================
# 1. CONFIGURATION DU PROJET & CHEMINS
# ==========================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)

# On ajoute 'src' au path
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# On force le dossier de travail à la racine
try:
    os.chdir(ROOT_DIR)
    print(f"📂 Dossier de travail défini sur : {ROOT_DIR}")
except Exception as e:
    print(f"⚠️ Impossible de changer le dossier de travail : {e}")

# ==========================================
# 2. IMPORTS
# ==========================================
try:
    # On importe uniquement l'algo de calcul (plus besoin de la géométrie)
    from algorithms import calculer_itineraire
    from map import maping
    from services.routes_geom import extraire_infos_itineraire
    print(f"✅ Modules chargés. Graphe contenant {len(maping)} villes.")

except ImportError as e:
    print(f"\n❌ ERREUR CRITIQUE D'IMPORT : {e}")
    def calculer_itineraire(d, a): return []
    def extraire_infos_itineraire(l): return {"villes": {}, "routes": []}

app = Flask(__name__)

# ==========================================
# 3. CHARGEMENT DES DONNÉES (AUTOCOMPLÉTION)
# ==========================================
DATA_VILLES = {}
path_coords = os.path.join(ROOT_DIR, "src", "data", "coords_villes.json")

try:
    with open(path_coords, 'r', encoding='utf-8') as f:
        DATA_VILLES = json.load(f)
except FileNotFoundError:
    print(f"⚠️ ATTENTION : Fichier coords_villes.json introuvable.")

# ==========================================
# 4. FONCTION FORMATAGE TEMPS
# ==========================================
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

# ==========================================
# 5. ROUTES API
# ==========================================

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
        print(f"🔄 Calcul demandé : {data['depart']} -> {data['arrivee']}")

        # 1. Calcul mathématique uniquement
        resultats_algo = calculer_itineraire(data['depart'], data['arrivee'])
        
        if not resultats_algo:
            return jsonify({'erreur': 'Aucun chemin trouvé.'}), 404

        best = resultats_algo[0]
        chemin = best.get('Chemin', [])
        
        # 2. Formatage des données
        dist = best.get('distance') or best.get('Distance_reelle') or 0
        tps_raw = best.get('temps') or best.get('Temps_reel') or 0
        
        # 3. Récupérer les informations de géométrie des routes
        try:
            geo_infos = extraire_infos_itineraire(chemin)
            print(f"✅ Géométrie récupérée : {len(geo_infos['villes'])} villes, {len(geo_infos['routes'])} routes")
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération de la géométrie : {e}")
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
        print(f"❌ Erreur API : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erreur': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Serveur lancé : http://127.0.0.1:5000")
    app.run(debug=True, port=5000)