import sys
import os
import json
import math
from flask import Flask, render_template, request, jsonify

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    os.chdir(ROOT_DIR)
    print(f"Dossier de travail défini sur : {ROOT_DIR}")
except Exception as e:
    print(f"⚠️ Impossible de changer le dossier de travail : {e}")

try:
    from algorithms import calculer_itineraire
    from map import maping
    from services.routes_geom import extraire_infos_itineraire
    print(f"Modules chargés. Graphe contenant {len(maping)} villes.")

except ImportError as e:
    print(f"\n ⚠️ ERREUR CRITIQUE D'IMPORT : {e}")
    def calculer_itineraire(d, a): return []
    def extraire_infos_itineraire(l): return {"villes": {}, "routes": []}


def supprimer_boucles(chemin):
    """
    Supprime les boucles en aller-retour d'un chemin.
    Si une ville est visitée plusieurs fois, supprime tout ce qui est entre 
    les deux passages et garde le chemin optimisé.
    
    Exemple: [A, B, C, D, B, E, F] -> [A, B, E, F]
    """
    if not chemin or len(chemin) <= 1:
        return chemin
    
    nouveau_chemin = []
    ville_positions = {}
    
    for idx, ville in enumerate(chemin):
        if ville in ville_positions:
            # On a déjà visité cette ville
            # Garder seulement jusqu'au premier passage et continuer à partir de là
            pos_premiere = ville_positions[ville]
            nouveau_chemin = nouveau_chemin[:pos_premiere + 1]
            # Réinitialiser les positions après cette ville
            ville_positions = {v: i for i, v in enumerate(nouveau_chemin)}
        else:
            nouveau_chemin.append(ville)
            ville_positions[ville] = len(nouveau_chemin) - 1
    
    return nouveau_chemin


def calculer_distance_reelle(chemin):
    """
    Calcule la distance réelle pour un chemin donné en km.
    """
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
        print(f"⚠️ Erreur lors du calcul de distance : {e}")
    
    return round(distance_totale, 2)


def calculer_temps_reel(chemin):
    """
    Calcule le temps réel pour un chemin donné en minutes.
    """
    if not chemin or len(chemin) < 2:
        return 0
    
    temps_total = 0
    try:
        for i in range(len(chemin) - 1):
            ville_depart = chemin[i]
            ville_arrivee = chemin[i + 1]
            
            if ville_depart in maping and ville_arrivee in maping[ville_depart]:
                distance_pair = maping[ville_depart][ville_arrivee]
                temps = distance_pair[1]  # Index 1 contient le temps
                temps_total += temps
    except (KeyError, IndexError, TypeError) as e:
        print(f"⚠️ Erreur lors du calcul de temps : {e}")
    
    return round(temps_total, 2)

app = Flask(__name__)

DATA_VILLES = {}
path_coords = os.path.join(ROOT_DIR, "src", "data", "coords_villes.json")

try:
    with open(path_coords, 'r', encoding='utf-8') as f:
        DATA_VILLES = json.load(f)
except FileNotFoundError:
    print(f"⚠️ Fichier coords_villes.json introuvable.")

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
            # Si on atteint la limite de récursion, on essaie dans le sens inverse
            print(f"⚠️ Récursion infinie détectée avec {depart} -> {arrivee}")
            print(f"✓ Tentative en sens inverse : {arrivee} -> {depart}")
            
            # Chercher en sens inverse
            resultats_algo = calculer_itineraire(arrivee, depart)
            
            # Inverser chaque chemin trouvé pour afficher dans le bon sens
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
        print(f"⚠️ Erreur API : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erreur': str(e)}), 500

if __name__ == '__main__':
    print("Serveur lancé : http://127.0.0.1:5000")
    app.run(debug=True, port=5000)