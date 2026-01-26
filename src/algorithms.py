from map import maping
from localisation import localisation_ville
import math
import numpy as np

## Fonctionnement de l'algo:
#1. Entrée utilisateur : ville de départ, ville d'arrivée
#2. Vérification si ville d'arrivée dans les voisines directes de la ville de départ
#3. Si non, trier les villes voisines en fonction de la distance orthodromique à la ville d'arrivée
#4. Calcul des 3 chemins les plus courts en distance orthodromique et les sortirs sous le format:
#5. Calcul de la distance réelle pour chaque chemin
#6. Trie du plus court au plus long chemin en distance réelle 
#7. Calcul du temps réelle pour chaque chemin (en prenant en compte la vitesse moyenne des routes entre chaque)
#8. Trie du plus rapide au plus lent chemin en temps réelle
#9. Affichage des résultats

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
'''
#Jeu de test
voisines_test=[['A', 10],['B', 23],['C', 2], ['D', 42]]
print(trivoisines(voisines_test))'''

## premier test pour voir le format de chemin
# 1. Fonction permettant de trier les villles dans la liste ville départ par rapport distance orthodromique
# 2. Fonction permettant de connaitre la ville suivante la plus proche de la ville d'arrivée si destination pas dans voisines directes
# 3. Calcul de la distance en fonction du parcours obtenu

## Trouver les 3 chemins les plus courts en distance orthodromique
dico={}
liste = []

def parcours_dist_orth(ville, villeA, chemin, dico):
    i=0
    if villeA in maping[ville]:
        return chemin+[villeA]        
    voisines=[]
    for voisine in maping[ville] :
        if voisine not in chemin :
            voisines.append([voisine, distance_orthodromique(localisation_ville[voisine][0], localisation_ville[voisine][1], localisation_ville[villeA][0], localisation_ville[villeA][1])])
    voisinestri=trivoisines(voisines)
    print(voisinestri)
    for voisine in voisinestri[:4] :
        res = parcours_dist_orth(voisine, villeA, chemin+[voisine], dico)
        if villeA in res:
            liste.append(res)
            if len(dico)>1:
                if type(dico[str(i)]) == list:
                    dico[str(i+1)+'-bis']=res
            else: 
                dico[str(i)]=res
            i+=1

    return(dico) # un chemin a été trouvé : remontée du résultat
print(parcours_dist_orth('Toulouse', 'Aussonne', ['Toulouse'], dico))

def calculer_distance_reelle(tab):
    distance_reelle_totale = 0
    for i in range(len(dico) - 1):
        depart=tab[i]
        arrivee=tab[i+1]
        distance_pair=maping[depart][arrivee]
        km=distance_pair[0]
        distance_reelle_totale += km
    return distance_reelle_totale
print(calculer_distance_reelle(['Toulouse', 'Tournefeuille', 'Colomiers', 'Aussonne']))

def tris_distance_reelle(dico):
    dico_res={}
    for cle in dico:
        res = calculer_distance_reelle(dico[cle])
        dico_res[cle]=res
    return dict(sorted(dico_res.items(), key=lambda item: item[1]))
print(tris_distance_reelle(dico))

def extract_temps(tab):
    res=0
    villeD=tab[0]
    for ville in tab[1:]:
        res+= maping[villeD][ville][3]
        villeD=ville
    return res                      #return le temps pour un chemin
print((np.linspace(1,10, 10).tolist()))
print(np.linspace(0,len(dico), len(dico)-1))
def dico_temps(dico):
    dico_res={}
    temps_res=[]
    chemin_res=np.linspace(0,len(dico)-1, len(dico)-1)
    print(chemin_res)
    for cle in dico:
        temps_res+=[extract_temps(dico[cle])]
        for i in range (len(temps_res)-1):
            if temps_res[i+1]<temps_res[i]:
                temps_res[i], temps_res[i+1]=temps_res[i+1], temps_res[i]
                chemin_res[i], chemin_res[i+1]=chemin_res[i+1], chemin_res[i]
    return dico_res

#print(dico_temps(dico))