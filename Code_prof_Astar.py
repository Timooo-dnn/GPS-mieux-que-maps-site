import math, sys
## On a pour l'instant qu'une solution de route entre les villes, mais on pourrait imaginer en avoir plusieurs (ex: par l'autoroute, par la nationale, par la départementale, etc.)
## On doit rajouter le prix des péages

graphe = {'Alès':{'Anduze':15, 'Nîmes':43, 'Montpellier':73},
          'Arles':{'Nîmes':36},
          'Anduze':{'Alès':15, 'Nîmes':44},
          'Lodève':{'Montpellier':56, 'Sète':63, 'Anduze':86},
          'Montpellier': {'Sète':34, 'Lodève':56, 'Nîmes':54, 'Alès': 73},
          'Nîmes':{'Montpellier':54, 'Alès':43, 'Anduze':44, 'Arles':36},
          'Sète':{'Montpellier':34, 'Lodève':63},
          }

géo = {'Alès': [44.1231, 4.0803], 'Anduze': [44.0538, 4.0427], 'Arles': [43.666672, 4.63333], 'Lodève': [43.7317, 3.3235], 'Montpellier':[43.610769, 3.876716], 'Nîmes':[43.8367, 4.3601], 'Sète': [43.4045, 3.6934]}

# distance peenant en compte la courbure de la Terre
# On retrie les voisines pour prioriser celles qui sont les plus proches de la ville d'arrivée
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

# mise en oeuvre de l'heuristique :
# les voisines d'une ville vont être parcourues par la fonction récursive
# dans l'ordre de leur proximité avec la ville d'arrivée puisque déjà pré-ordonnées
def triVillesParRapportVilleArrivée(voisines) :
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

# fonction récursive du parcours de graphe
# lors de l'appel initial le paramètre ville est la ville de départ
# puis lors des appels suivants, la ville courante
def parcours(ville, villeA, chemin) :
    if villeA in graphe[ville] : return chemin+[villeA]
    voisines = []
    for voisine in graphe[ville] :
        if voisine not in chemin : # pour ne pas boucler dans le graphe
            print(f"Not in chemin {voisines}")
            voisines.append([voisine, distance_orthodromique(géo[voisine][0], géo[voisine][1], géo[villeA][0], géo[villeA][1])])
    voisinestriées = triVillesParRapportVilleArrivée(voisines)
    print(f"Triée {voisinestriées}")
    for voisine in voisinestriées :
        res = parcours(voisine, villeA, chemin+[voisine])
        if villeA in res : return res # un chemin a été trouvé : remontée du résultat
    return []

print(parcours('Alès', 'Sète', ['Anduze']))