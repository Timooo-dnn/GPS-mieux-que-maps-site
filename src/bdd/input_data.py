import json
import os

with open(r"src/data/routes_villes_adj.json",encoding="utf-8") as f:
    dico_brut = json.load(f)

dico_final = {}
for ville_id in dico_brut: 
    dico_final[ville_id] = {}    #création clés premier dico

    liste_voisins = dico_brut[ville_id]["adjacents"]    #vérification que la ville a au moins un voisin
    if len(liste_voisins) > 0 :
    
        for dico_adjacent in liste_voisins :        #création des sous-dictionnaire pour chaque ville, contenant en clés les villes voisines, et en valeur la liste des attributs
            nom_voisine = dico_adjacent["nom"]
            dico_final[ville_id][nom_voisine] = [dico_adjacent["distance_km"],dico_adjacent["temps_min"],dico_adjacent["vitesse_moyenne_kmh"],dico_adjacent["autoroute"]]


chemin_entree = r"src/data/routes_villes_adj.json"
chemin_sortie = os.path.join(os.path.dirname(chemin_entree), "dico_final.json")

with open(chemin_sortie, "w", encoding="utf-8") as f:
    json.dump(dico_final, f, ensure_ascii=False, indent=4)
