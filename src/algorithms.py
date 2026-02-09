from map import maping
from map import maping_test

from localisation import localisation_ville
from localisation import localisation_ville_test

import math
import numpy as np

User_Départ = "Toulouse_26686518"
User_Destination = "Tarbes_26691527"


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

## premier test pour voir le format de chemin
# 1. Fonction permettant de trier les villles dans la liste ville départ par rapport distance orthodromique
# 2. Fonction permettant de connaitre la ville suivante la plus proche de la ville d'arrivée si destination pas dans voisines directes
# 3. Calcul de la distance en fonction du parcours obtenu

## Trouver les 3 chemins les plus courts en distance orthodromique
dico={}
liste = []
visited_global = set() # Ajout d'une mémoire globale des villes visitées

def parcours_dist_orth(ville, villeA, chemin, dico):
    i=0
    visited_global.add(ville) # Marquer la ville courante comme visitée
    if villeA in maping[ville]:
        return chemin+[villeA]        
    voisines=[]
    for voisine in maping[ville] :
        # Le problème est ici : on ne vérifiait que le chemin actuel, pas l'historique global
        if voisine not in chemin and voisine not in visited_global:
            voisines.append([voisine, distance_orthodromique(localisation_ville[voisine][0], localisation_ville[voisine][1], localisation_ville[villeA][0], localisation_ville[villeA][1])])
    voisinestri=trivoisines(voisines)
    for voisine in voisinestri[:3] :
        res = parcours_dist_orth(voisine, villeA, chemin+[voisine], dico)
        if res == "trouvé" : return "trouvé"
        if villeA in res :
            liste.append(res)
            #print(res)
            if len(liste) >= 4 : return "trouvé"
            """
            if len(dico)>1:
                if type(dico[str(i)]) == list:
                    dico[str(i+1)+'-bis']=res
            else: 
                dico[str(i)]=res
            i+=1
            """

    return(chemin) # un chemin a été trouvé : remontée du résultat
parcours_dist_orth(User_Départ, User_Destination, [User_Départ], dico)

    
def liste_to_dico(liste) :
    for i in range (len(liste)) :
        dico[i]=liste[i]
    return(dico)
dico_3_chemins_ortho=liste_to_dico(liste)


## Calcul des distances réelles avec le top 3 orthodromique

def calculer_distance_reelle(tab):
    distance_reelle_totale = 0
    for i in range(len(tab) - 1):
        depart=tab[i]
        arrivee=tab[i+1]
        distance_pair=maping[depart][arrivee]
        km=distance_pair[0]
        print("La distance entre", depart, "et", arrivee, "est de", km)
        distance_reelle_totale += km
        print(distance_reelle_totale)
    return round(distance_reelle_totale, 2)
calculer_distance_reelle(dico_3_chemins_ortho[0])

#print(['Toulouse_26686518', 'Tournefeuille_26691412', 'Plaisance-du-Touch_26691742', 'Fonsorbes_26695118', 'Fontenilles_26697797', 'Bonrepos-sur-Aussonnelle_1574500411', 'Saiguède_244884638', 'Saint-Thomas_244884678', 'Seysses-Savès_390002317', 'Savignac-Mona_389939183', 'Monblanc_389931889', 'Samatan_389988030', 'Lombez_389897832', 'Sauveterre_389893184', 'Sabaillan_389884208', 'Tournan_389905878', "Villefranche-d'Astarac_389904276", 'Betcave-Aguin_389842078', 'Moncorneil-Grazan_389701084', 'Sère_389707247', 'Bézues-Bajon_389712639', 'Panassac_389717652', 'Chélan_389743206', 'Peyret-Saint-André_1706148540', 'Larroque_1361030150', 'Ponsan-Soubiran_389677885', 'Guizerix_1706148419', 'Sadournin_1706148581', 'Puydarrieux_1361030156'])
## Tri du top 3 distances réelles dans l'ordre croissant

def tris_distance_reelle(dico):
    dico_res={}
    for cle in dico:
        res = calculer_distance_reelle(dico[cle])
        dico_res[cle]=res
        print(dico_res)
        print(res)
    return dict(sorted(dico_res.items(), key=lambda item: item[1]))
print(tris_distance_reelle(dico_3_chemins_ortho))

## Calcul des temps réels)
def extract_temps(tab):
    res=0
    villeD=tab[0]
    for ville in tab[1:]:
        res+= maping[villeD][ville][1]
        villeD=ville
    return res                      #return un temps pour un chemin sous forme de [villeD, ville, ville, villeA]
extract_temps(dico_3_chemins_ortho[1])


def tri_temps_reel(dico):
    dico_res={}
    for cle in dico:
        res = extract_temps(dico[cle])
        dico_res[cle]=round(res, 2)
    return dict(sorted(dico_res.items(), key=lambda item: item[1]))
tri_temps_reel(dico_3_chemins_ortho)                    #return un dico trié en fonction du temps sous forme {'0': 11.4, '1-bis': 15.0, '1': 18.0}

## Formulation des données sorties sous format {Chemin}:[Distance_réelle],[Temps réel],[Booléen autoroute]

## Formulation des données sorties sous format sortie_formalisée=[{Chemin:[chemin]:[Distance_réelle],[Temps réel],[Booléen autoroute]}]
def formalisation_donnees(chemin,distance,temps):
    sortie_formalisee = []
    for id_chemin in chemin:
        donnees_chemin = {
            "ID" : id_chemin,
            "Chemin" : chemin[id_chemin],
            "distance" : distance[id_chemin],
            "temps" : temps[id_chemin],
            "Autoroute" : "A" in str(maping.get(chemin[id_chemin][0], {}).get(chemin[id_chemin][1], ""))
        }
        sortie_formalisee.append(donnees_chemin)
    return sortie_formalisee

def test_formalisation():
    return formalisation_donnees(chemin_entree, distance_entree, temps_entree)

chemin_entree = dico_3_chemins_ortho
distance_entree = tris_distance_reelle(dico_3_chemins_ortho)
temps_entree = tri_temps_reel(dico_3_chemins_ortho)

print(test_formalisation())