import json
import folium
import os

# ================= CONFIGURATION =================
PATH_JSON = r"src\data\routes_villes_adj.json"
OUTPUT_HTML = "ma_route_test.html"

def charger_donnees():
    if not os.path.exists(PATH_JSON):
        print(f"Erreur : Le fichier {PATH_JSON} est introuvable.")
        print("Avez-vous bien exécuté le script de calcul haute précision avant ?")
        return None
    with open(PATH_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def generer_carte(ville_depart, ville_arrivee, data):
    if data is None: return

    # Vérification de l'existence de la ville de départ
    if ville_depart not in data:
        print(f"Erreur : La ville '{ville_depart}' n'est pas dans la base de données.")
        return

    # Recherche du trajet vers la ville d'arrivée
    trajet = next((adj for adj in data[ville_depart]['adjacents'] if adj['nom'] == ville_arrivee), None)
    
    if not trajet:
        print(f"Erreur : Aucun trajet direct n'a été calculé entre {ville_depart} et {ville_arrivee}.")
        voisins = [v['nom'] for v in data[ville_depart]['adjacents']]
        if voisins:
            print(f"Voisins disponibles pour {ville_depart} : {', '.join(voisins)}")
        else:
            print(f"La ville {ville_depart} n'a aucun voisin enregistré.")
        return

    coords_dep = data[ville_depart]['coords']
    m = folium.Map(location=[coords_dep['lat'], coords_dep['lon']], zoom_start=12)

    try:
        points_route = [[p[1], p[0]] for p in trajet['path_geometry']]
    except KeyError:
        print("Erreur structurelle : La clé 'path_geometry' est absente du JSON.")
        return

    folium.PolyLine(
        points_route, 
        color="blue", 
        weight=5, 
        opacity=0.8,
        tooltip=(f"Distance : {trajet['distance_km']} km | "
                 f"Vitesse moy : {trajet['vitesse_moyenne_kmh']} km/h")
    ).add_to(m)

    folium.Marker(
        [coords_dep['lat'], coords_dep['lon']], 
        popup=f"Départ : {ville_depart}", 
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)

    coords_arr_finale = points_route[-1]
    folium.Marker(
        coords_arr_finale, 
        popup=f"Arrivée : {ville_arrivee}\nDistance : {trajet['distance_km']} km", 
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(m)

    m.save(OUTPUT_HTML)
    
    print("-" * 40)
    print(f"SUCCÈS : Carte générée pour {ville_depart} -> {ville_arrivee}")
    print(f"Distance calculée : {trajet['distance_km']} km")
    print(f"Localisation : {os.path.abspath(OUTPUT_HTML)}")
    print("-" * 40)

# ================= EXÉCUTION =================
if __name__ == "__main__":
    print("--- Visualiseur de Trajets GPS (Haute Précision) ---")
    data_gps = charger_donnees()
    
    if data_gps:
        v_dep = input("Ville de départ : ").strip()
        v_arr = input("Ville d'arrivée : ").strip()
        
        generer_carte(v_dep, v_arr, data_gps)