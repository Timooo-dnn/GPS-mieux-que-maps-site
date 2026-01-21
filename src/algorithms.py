"""
algorithms.py
Implémentation des algorithmes de recherche de chemin.

Responsabilité :
- Calculer le plus court chemin
- Ne PAS stocker les données du graphe

{"Toulouse":{"Blagnac":[10,A], "Colomiers":[15, N],"Tournefeuille":[8, A]},
"Blagnac":{"Toulouse":[10, A], "Aussonne":[9,D], "Colomiers":[7, V]},
"Colomiers":{"Toulouse":[15, N], "Blagnac":[7, V],"Tournefeuille":[5,D], "Aussonne":[12,N]},
"Tournefeuille":{"Toulouse":[8,A], "Colomiers":[5, D]},
"Aussonne":{"Blagnac":[9,D], "Colomiers":[12, N]}
}
"""
##Importer les données d'entrées contenues sur les fichiers map.py et localisation.py
from map import maping
from localisation import localisation_ville
import math

'''
insertion des données
tri orthodromique (prioriser les villes étant les plus proches de la ville d'arrivée)
calcul du parcours avec + petite distance (distances réelles entre les villes)
définition du temps de parcours en fonction de la vitesse moyenne des routes utilisées (distance, type de route)
tri et appel calcul parcours avec + petit temps
+ possibilité calcul cout (péages, carburant, etc.)'''

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

#Définition de la fonction de tri ortho 
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
'''
#Jeu de test
voisines_test=[['A', 10],['B', 23],['C', 2], ['D', 42]]
print(trivoisines(voisines_test))'''

## premier test pour voir le format de chemin
# 1. Fonction permettant de trier les villles dans la liste ville départ par rapport distance orthodromique
# 2. Fonction permettant de connaitre la ville suivante la plus proche de la ville d'arrivée si destination pas dans voisines directes
# 3. Calcul de la distance en fonction du parcours obtenu

def parcours_dist_orth(ville, villeA, chemin, tab_final):
    if villeA in maping[ville]:
        print(chemin)
        return chemin+[villeA]         #[['Toulouse', 0], ['Blagnac', 10]]
    voisines=[]
    for voisine in maping[ville] :
        if voisine not in chemin :
            voisines.append([voisine, distance_orthodromique(localisation_ville[voisine][0], localisation_ville[voisine][1], localisation_ville[villeA][0], localisation_ville[villeA][1])])
        voisinestri=trivoisines(voisines)
        print(voisinestri)
    for voisine in voisinestri :
        res = parcours_dist_orth(voisine, villeA, chemin+[voisine], tab_final)
        if villeA in res : return(res) # un chemin a été trouvé : remontée du résultat
    return []


print(parcours_dist_orth('Toulouse', 'Aussonne', ['Toulouse'], ['sdvsvsv']))


chemin_trouve=['Toulouse', 'Colomiers', 'Aussonne']
def calculer_distance_reelle(chemin_trouve):
    """
    Prend une liste de villes ex: ['Toulouse', 'Colomiers', 'Aussonne']
    Et calcule la somme des distances réelles dans 'maping'.
    """
    distance_totale = 0
    # On boucle de la première ville jusqu'à l'avant-dernière
    # Si le chemin a 3 villes, on fait 2 trajets (0->1 et 1->2)
    for i in range(len(chemin_trouve) - 1):
        depart = chemin_trouve[i]
        arrivee = chemin_trouve[i+1]
        # On va chercher l'info dans le graphe
        # Exemple: maping['Toulouse']['Colomiers'] donne [15, 'Nationale']
        infos_arete = maping[depart][arrivee]
        # La distance est le premier élément de la liste (index 0)
        km = infos_arete[0]
        #print(f"Trajet {depart} -> {arrivee} : {km} km ({infos_arete[1]})")
        distance_totale += km
    return distance_totale