from map import maping
from localisation import localisation_ville
import math
import numpy as np

premiere_visite = False

def calculer_itineraire(ville_depart, ville_destination):
    global visited_global, liste, dico, premiere_visite
    
    visited_global = set()
    liste = []
    dico = {}
    premiere_visite= False

    parcours_dist_orth(ville_depart, ville_destination, [ville_depart])
    dico_3_chemins = liste_to_dico(liste)
    
    distance_entree = tris_distance_reelle(dico_3_chemins)
    temps_entree = tri_temps_reel(dico_3_chemins)
    
    return formalisation_donnees(dico_3_chemins, distance_entree, temps_entree)

def distance_orthodromique(lat1, lng1, lat2, lng2):
    # angles en degrés
    lat1 *= math.pi / 180
    lng1 *= math.pi / 180
    lat2 *= math.pi / 180
    lng2 *= math.pi / 180
    v = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(lng1 - lng2)
    v = max(min(v, 1), -1)  # corrige les dépassements flottants
    return (6371000 * math.acos(v)) / 1000

def trivoisines(voisines):
    voisines_triées = []
    while len(voisines) > 0:
        if len(voisines) == 1:
            voisines_triées.append(voisines[0][0])
            del voisines[0]
        else:
            imin=0; i=1
            while i < len(voisines):
                if voisines[imin][1] > voisines[i][1]:
                    imin = i
                i += 1
            voisines_triées.append(voisines[imin][0])
            del voisines[imin]
    return voisines_triées

# ------------------- Parcours -------------------
dico = {}
liste = []
visited_global = set()

def parcours_dist_orth(ville, villeA, chemin):
    global premiere_visite
    visited_global.add(ville)
    
    if villeA in maping.get(ville, {}):
        chemin_final = chemin + [villeA]
        if chemin_final not in liste:
            liste.append(chemin_final)
        return chemin_final

    voisines = []
    for voisine in maping.get(ville, {}):
        if voisine not in chemin and voisine not in visited_global and maping.get(voisine, {}):
            # ACCÈS CORRIGÉ POUR JSON DICT {lat, lon}
            voisines.append([
                voisine,
                distance_orthodromique(
                    localisation_ville[voisine]["lat"],
                    localisation_ville[voisine]["lon"],
                    localisation_ville[villeA]["lat"],
                    localisation_ville[villeA]["lon"]
                )
            ])
    voisines_triées = trivoisines(voisines)
    for voisine in voisines_triées[:2]:
        res = parcours_dist_orth(voisine, villeA, chemin + [voisine])
        if res == "trouvé": return "trouvé"
        if villeA in res:
            liste.append(res)
            if len(liste) >= 3: return "trouvé"
    return chemin

def liste_to_dico(liste):
    for i in range(len(liste)):
        dico[i] = liste[i]
    return dico

# ------------------- Distance réelle -------------------
def calculer_distance_reelle(tab):
    total = 0
    for i in range(len(tab) - 1):
        depart, arrivee = tab[i], tab[i+1]
        km = maping[depart][arrivee][0]
        total += km
    return round(total, 2)

def tris_distance_reelle(dico):
    dico_res = {k: calculer_distance_reelle(v) for k, v in dico.items()}
    return dict(sorted(dico_res.items(), key=lambda item: item[1]))

# ------------------- Temps réel -------------------
def extract_temps(tab):
    res = 0
    villeD = tab[0]
    for ville in tab[1:]:
        res += maping[villeD][ville][1]
        villeD = ville
    return res

def tri_temps_reel(dico):
    dico_res = {k: round(extract_temps(v),2) for k,v in dico.items()}
    return dict(sorted(dico_res.items(), key=lambda item: item[1]))

# ------------------- Autoroute -------------------
def verifier_autoroute(trajet):
    for i in range(len(trajet) - 1):
        u, v = trajet[i], trajet[i+1]
        if u in maping and v in maping[u]:
            infos = maping[u][v]
            if (len(infos) > 3 and (infos[3] is True or infos[3] == 1)) or \
               (len(infos) > 1 and isinstance(infos[1], str) and "Autoroute" in infos[1]):
                return True
    return False

def formalisation_donnees(chemin, distance, temps):
    sortie = []
    for id_chemin in chemin:
        sortie.append({
            "ID": id_chemin,
            "Chemin": chemin[id_chemin],
            "distance": distance[id_chemin],
            "temps": temps[id_chemin],
            "Autoroute": verifier_autoroute(chemin[id_chemin])
        })
    return sortie
