import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from localisation import localisation_ville
from map import maping
import math


## Fonctionnement de l'algo:
#1. Entrée utilisateur : ville de départ, ville d'arrivée
#2. Vérification si ville d'arrivée dans les voisines directes de la ville de départ
#3. Si non, trier les villes voisines en fonction de la distance orthodromique à la ville d'arrivée
#4. Calcul des 3 chemins les plus courts en distance orthodromique et les sortirs sous le format:
Chemina=["Toulouse", "Colomiers", "Tournefeuille", "Aussonne"]
Cheminb=["Toulouse", "Blagnac", "Aussonne"]
Cheminc=["Toulouse", "Colomiers", "Aussonne"]
#5. Calcul de la distance réelle pour chaque chemin
#6. Trie du plus court au plus long chemin en distance réelle 
#7. Calcul du temps réelle pour chaque chemin (en prenant en compte la vitesse moyenne des routes entre chaque)
#8. Trie du plus rapide au plus lent chemin en temps réelle
#9. Affichage des résultats
print("Statut: Lancement Algo")
## Calcul Othodromique entre 2 points
def distance_orthodromique(lat1, lng1, lat2, lng2) :
    # angles en degrés
    lat1 *= math.pi / 180
    lng1 *= math.pi / 180
    lat2 *= math.pi / 180
    lng2 *= math.pi / 180
    v = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(lng1 - lng2)
    # Gestion des dépassements de flottants
    if v > 1: v = 1
    elif v < -1: v = -1
    return (6371000 * math.acos(v)) / 1000

## Tri des villes en fonction de la distance orthodromique
def trivoisines(voisines):
    voisinestriées = []
    while len(voisines) > 0 :
        if len(voisines) == 1 :
            voisinestriées.append(voisines[0][0])
            del voisines[0]
        else :
            imin=0; i=1
            while i < len(voisines) :
                if voisines[imin][1] > voisines[i][1] :
                    imin = i
                i += 1
            voisinestriées.append(voisines[imin][0])
            del voisines[imin]
    return voisinestriées


## premier test pour voir le format de chemin
# 1. Fonction permettant de trier les villles dans la liste ville départ par rapport distance orthodromique
# 2. Fonction permettant de connaitre la ville suivante la plus proche de la ville d'arrivée si destination pas dans voisines directes
# 3. Calcul de la distance en fonction du parcours obtenu

## Trouver les 3 chemins les plus courts en distance orthodromique
global dico
dico={}
def parcours_dist_orth(ville, villeA, chemin):
    if villeA in maping[ville]:
        return chemin+[villeA]        
    voisines=[]
    for voisine in maping[ville] :
        if voisine not in chemin :
            voisines.append([voisine, distance_orthodromique(localisation_ville[voisine][0], localisation_ville[voisine][1], localisation_ville[villeA][0], localisation_ville[villeA][1])])
    voisinestri=trivoisines(voisines)
    for voisine in voisinestri :
        res = parcours_dist_orth(voisine, villeA, chemin+[voisine])
        if villeA in res:
            dico['chemin1']=res
            return(res) # un chemin a été trouvé : remontée du résultat
    return []

def calculer_distance_reelle(chemin):
    distance_reelle_totale = 0
    for i in range(len(chemin) - 1):
        depart=chemin[i]
        arrivee=chemin[i+1]
        if arrivee in maping[depart]:
            distance_pair=maping[depart][arrivee]
            km=distance_pair[0]
            distance_reelle_totale += km
        else:
            return "Introuvable (route manquante)"
    return distance_reelle_totale

chemins_a_tester = {"Chemina": Chemina, "Cheminb": Cheminb, "Cheminc": Cheminc}
for nom, chemin in chemins_a_tester.items():
    print(f"{nom} distance en km is {calculer_distance_reelle(chemin)}")

def tri_distance_reelle(chemin):
    