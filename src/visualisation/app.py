import sys
import os
import json
import math
from flask import Flask, render_template_string, request, jsonify

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
    print(f"✅ Modules chargés. Graphe contenant {len(maping)} villes.")

except ImportError as e:
    print(f"\n❌ ERREUR CRITIQUE D'IMPORT : {e}")
    def calculer_itineraire(d, a): return []

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
# 5. FRONTEND (HTML + JAVASCRIPT)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPS Python - Calculateur</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }
        
        #sidebar { 
            width: 320px; 
            background: #ffffff; 
            padding: 20px; 
            box-shadow: 2px 0 10px rgba(0,0,0,0.1); 
            z-index: 1000; 
            display: flex; 
            flex-direction: column; 
        }
        
        h2 { color: #2c3e50; margin-top: 0; text-align: center; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; color: #34495e; }
        input[type="text"] { width: 93%; padding: 10px; border: 1px solid #bdc3c7; border-radius: 6px; }
        
        button#btn-calcul { 
            width: 100%; padding: 12px; background: #27ae60; color: white; 
            border: none; border-radius: 6px; font-size: 16px; font-weight: bold; 
            cursor: pointer; margin-top: 10px; 
        }
        button#btn-calcul:hover { background: #2ecc71; }
        
        .status { font-size: 0.85em; margin-top: 4px; min-height: 20px; color: #7f8c8d; }
        
        #resultats { 
            margin-top: 25px; padding-top: 20px; border-top: 1px solid #ecf0f1; display: none; 
        }
        .res-card {
            background: #f8f9fa; border-left: 5px solid #3498db; padding: 15px; border-radius: 4px;
        }
        .res-value { font-size: 1.4rem; font-weight: bold; color: #2c3e50; display: block; }
        
        #map { flex-grow: 1; height: 100%; }
        .btn-select { background: #3498db; color: white; border: none; padding: 5px 10px; cursor: pointer; margin-top: 5px; border-radius: 3px;}
    </style>
</head>
<body>

<div id="sidebar">
    <h2>📍 Mon GPS</h2>
    
    <div class="input-group">
        <label>Ville de Départ</label>
        <input type="text" id="depart_input" placeholder="Ex: Toulouse" onblur="rechercher('depart')" autocomplete="off">
        <input type="hidden" id="depart_id">
        <div id="depart_status" class="status"></div>
    </div>

    <div class="input-group">
        <label>Ville d'Arrivée</label>
        <input type="text" id="arrivee_input" placeholder="Ex: Tarbes" onblur="rechercher('arrivee')" autocomplete="off">
        <input type="hidden" id="arrivee_id">
        <div id="arrivee_status" class="status"></div>
    </div>

    <button id="btn-calcul" onclick="lancerCalcul()">Voir l'itinéraire</button>

    <div id="resultats">
        <div class="res-card">
            <div style="margin-bottom:10px;">
                <span style="color:#7f8c8d; font-size:0.9em;">DISTANCE</span><br>
                <span id="res_dist" class="res-value">-</span>
            </div>
            <div>
                <span style="color:#7f8c8d; font-size:0.9em;">TEMPS ESTIMÉ</span><br>
                <span id="res_temps" class="res-value">-</span>
            </div>
        </div>
    </div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
<script>
    var map = L.map('map').setView([43.604, 1.444], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    var layerMarkers = L.layerGroup().addTo(map);

    // Fonction de recherche (points bleus pour choisir la ville)
    function rechercher(type) {
        var nom = document.getElementById(type + '_input').value;
        if(!nom) return;
        
        var statusDiv = document.getElementById(type + '_status');
        statusDiv.innerText = "Recherche...";
        
        fetch('/api/recherche_ville', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nom: nom})
        })
        .then(r => r.json())
        .then(data => {
            layerMarkers.clearLayers();
            if(data.length === 0) {
                statusDiv.innerHTML = "<span style='color:red'>❌ Introuvable</span>";
            } else if(data.length === 1) {
                validerSelection(type, data[0]);
            } else {
                statusDiv.innerHTML = "<span style='color:blue'>⚠️ " + data.length + " choix. Cliquez sur la carte.</span>";
                afficherHomonymes(type, data);
            }
        });
    }

    function afficherHomonymes(type, villes) {
        var bounds = L.latLngBounds();
        villes.forEach(v => {
            var m = L.marker([v.lat, v.lon])
                .bindPopup(`<div style="text-align:center"><b>${v.nom}</b><br><small>${v.id}</small><br><button class="btn-select" onclick='validerSelection("${type}", ${JSON.stringify(v)})'>Choisir</button></div>`);
            layerMarkers.addLayer(m);
            bounds.extend([v.lat, v.lon]);
        });
        map.fitBounds(bounds, {padding:[50,50]});
    }

    window.validerSelection = function(type, ville) {
        document.getElementById(type + '_id').value = ville.id;
        document.getElementById(type + '_input').value = ville.nom;
        document.getElementById(type + '_status').innerHTML = "<span style='color:green'>✅ Validé</span>";
        layerMarkers.clearLayers();
        map.closePopup();
        map.setView([ville.lat, ville.lon], 10);
    }

    // Calcul de l'itinéraire (Affichage TEXTUEL uniquement)
    function lancerCalcul() {
        var d = document.getElementById('depart_id').value;
        var a = document.getElementById('arrivee_id').value;

        if(!d || !a) { alert("Veuillez choisir les villes."); return; }

        document.getElementById('btn-calcul').innerText = "Calcul...";
        
        fetch('/api/calculer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({depart: d, arrivee: a})
        })
        .then(r => r.json())
        .then(data => {
            document.getElementById('btn-calcul').innerText = "Voir l'itinéraire";
            
            if(data.erreur) { alert(data.erreur); return; }

            // Affichage uniquement des résultats textuels
            document.getElementById('resultats').style.display = 'block';
            document.getElementById('res_dist').innerText = data.itineraire.distance + " km";
            document.getElementById('res_temps').innerText = data.itineraire.temps_formate;
            
            // Aucune modification de la carte ici (pas de lignes, pas de points rouges)
        })
        .catch(e => {
            alert("Erreur: " + e);
            document.getElementById('btn-calcul').innerText = "Voir l'itinéraire";
        });
    }
</script>
</body>
</html>
"""

# ==========================================
# 6. ROUTES API
# ==========================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

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
        
        # 2. Formatage des données
        dist = best.get('distance') or best.get('Distance_reelle') or 0
        tps_raw = best.get('temps') or best.get('Temps_reel') or 0
        
        # On ne renvoie PLUS de 'cartographie'
        return jsonify({
            'itineraire': {
                'distance': dist,
                'temps_raw': tps_raw,
                'temps_formate': formatter_temps(tps_raw)
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