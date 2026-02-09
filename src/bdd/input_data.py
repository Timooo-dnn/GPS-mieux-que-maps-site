import json
import os

with open(r"src\data\routes_villes_adj.json",encoding="utf-8") as f:
    dico_brut = json.load(f)

dico_final = {}
for ville_id in dico_brut: 
    dico_final[ville_id] = {}

    liste_voisins = dico_brut[ville_id]["adjacents"]
    if len(liste_voisins) > 0 :
    
        for dico_adjacent in liste_voisins :
            nom_voisine = dico_adjacent["nom"]
            dico_final[ville_id][nom_voisine] = [dico_adjacent["distance_km"],dico_adjacent["temps_min"],dico_adjacent["vitesse_moyenne_kmh"],dico_adjacent["autoroute"]]

chemin_entree = r"src\data\dico_final.json"
chemin_sortie = os.path.join(os.path.dirname(chemin_entree), "dico_final.json")

with open(chemin_sortie, "w", encoding="utf-8") as f:
    json.dump(dico_final, f, ensure_ascii=False, indent=4)
    print("fichier créé")
