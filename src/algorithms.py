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
from map import maping
from localisation import localisation_ville
import math

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


