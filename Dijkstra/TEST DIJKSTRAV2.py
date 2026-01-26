import sys
sys.stdout.reconfigure(encoding='utf-8')

import heapq
from typing import Dict, List, Tuple, Optional


def dijkstra(graph: Dict[str, List[Tuple[str, int]]],
             start: str,
             end: Optional[str] = None) -> Tuple[Dict[str, int], Dict[str, Optional[str]]]:
    """
    Implémentation de l'algorithme de Dijkstra pour trouver le plus court chemin.
   
    Args:
        graph: Dictionnaire représentant le graphe {nœud: [(voisin, poids), ...]}
        start: Nœud de départ
        end: Nœud d'arrivée (optionnel, si None calcule tous les chemins)
   
    Returns:
        distances: Dictionnaire des distances minimales depuis start
        predecesseurs: Dictionnaire pour reconstruire les chemins
    """
    # Initialisation des distances à l'infini sauf pour le nœud de départ
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
   
    # Dictionnaire pour mémoriser le prédécesseur de chaque nœud
    predecesseurs = {node: None for node in graph}
   
    # File de priorité : (distance, nœud)
    # heapq gère automatiquement le tri par distance croissante
    pq = [(0, start)]
   
    # Ensemble des nœuds visités pour éviter les retraitements
    visites = set()
   
    while pq:
        # Extraction du nœud avec la plus petite distance
        dist_actuelle, noeud_actuel = heapq.heappop(pq)
       
        # Si le nœud a déjà été visité, on passe au suivant
        if noeud_actuel in visites:
            continue
       
        # Marquer le nœud comme visité
        visites.add(noeud_actuel)
       
        # Optimisation : si on cherche un nœud spécifique et qu'on l'atteint
        if end is not None and noeud_actuel == end:
            break
       
        # Explorer tous les voisins du nœud actuel
        for voisin, poids in graph.get(noeud_actuel, []):
            # Si le voisin a déjà été visité, on l'ignore
            if voisin in visites:
                continue
           
            # Calcul de la nouvelle distance en passant par le nœud actuel
            nouvelle_distance = dist_actuelle + poids
           
            # Relaxation : mise à jour si on trouve un chemin plus court
            if nouvelle_distance < distances[voisin]:
                distances[voisin] = nouvelle_distance
                predecesseurs[voisin] = noeud_actuel
                heapq.heappush(pq, (nouvelle_distance, voisin))
   
    return distances, predecesseurs


def reconstruire_chemin(predecesseurs: Dict[str, Optional[str]],
                        start: str,
                        end: str) -> List[str]:
    """
    Reconstruit le chemin depuis le nœud de départ jusqu'au nœud d'arrivée.
   
    Args:
        predecesseurs: Dictionnaire des prédécesseurs
        start: Nœud de départ
        end: Nœud d'arrivée
   
    Returns:
        Liste des nœuds formant le chemin
    """
    chemin = []
    noeud_actuel = end
   
    # Remonter de la fin vers le début
    while noeud_actuel is not None:
        chemin.append(noeud_actuel)
        noeud_actuel = predecesseurs[noeud_actuel]
   
    # Inverser pour avoir le chemin de start à end
    chemin.reverse()
   
    # Vérifier que le chemin est valide
    if chemin[0] != start:
        return []  # Aucun chemin n'existe
   
    return chemin


# Exemple d'utilisation
if __name__ == "__main__":
    # Graphe des villes de l'Hérault et du Gard
    # Format: {ville: {voisin: distance_en_km, ...}}
    graphe_villes = {
        'Montpellier': {'Sète': 34, 'Lodève': 56, 'Nîmes': 54, 'Alès': 73},
        'Sète': {'Montpellier': 34, 'Lodève': 65},
        'Lodève': {'Montpellier': 56, 'Sète': 65, 'Anduze': 86},
        'Nîmes': {'Montpellier': 54, 'Alès': 73, 'Anduze': 47},
        'Alès': {'Anduze': 15, 'Nîmes': 49, 'Montpellier': 73},
        'Anduze': {'Alès': 47, 'Nîmes': 47}
    }
   
    # Conversion du format dictionnaire vers liste de tuples
    graphe = {ville: list(voisins.items()) for ville, voisins in graphe_villes.items()}
   
    # Affichage des villes disponibles
    print("=" * 50)
    print("CALCUL DU PLUS COURT CHEMIN - ALGORITHME DE DIJKSTRA")
    print("=" * 50)
    print("\nVilles disponibles:")
    for i, ville in enumerate(sorted(graphe.keys()), 1):
        print(f"  {i}. {ville}")
    
    # Saisie de la ville de départ
    print("\n" + "-" * 50)
    while True:
        depart = input("Entrez la ville de départ: ").strip()
        if depart in graphe:
            break
        print(f"❌ '{depart}' n'existe pas. Veuillez choisir parmi les villes listées.")
    
    # Saisie de la ville d'arrivée
    while True:
        arrivee = input("Entrez la ville d'arrivée: ").strip()
        if arrivee in graphe:
            if arrivee != depart:
                break
            print("❌ La ville d'arrivée doit être différente de la ville de départ.")
        else:
            print(f"❌ '{arrivee}' n'existe pas. Veuillez choisir parmi les villes listées.")
    
    # Exécution de l'algorithme
    print("\n" + "=" * 50)
    distances, predecesseurs = dijkstra(graphe, depart, arrivee)
   
    # Affichage des résultats
    print(f"\n📍 Plus court chemin de {depart} à {arrivee}:")
    chemin = reconstruire_chemin(predecesseurs, depart, arrivee)
    if chemin:
        print(f"  ➜ {' → '.join(chemin)}")
        print(f"  📏 Distance totale: {distances[arrivee]} km")
    else:
        print(f"  ❌ Aucun chemin trouvé")
    
    print("\n" + "=" * 50)
    print(f"Distances minimales depuis {depart}:")
    for ville in sorted(distances.keys()):
        dist = distances[ville]
        if dist == float('inf'):
            print(f"  {ville}: ∞ (non accessible)")
        else:
            print(f"  {ville}: {dist} km")
    print("=" * 50)