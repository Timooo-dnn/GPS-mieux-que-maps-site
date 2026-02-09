import json
import heapq
from typing import Dict, List, Optional


# ----------------------------------
# Chargement du graphe depuis JSON
# ----------------------------------
def charger_graphe_json(
    path: str,
    cout_index: int = 0
) -> Dict[str, List[Dict[str, float]]]:
    """
    Charge un graphe depuis un fichier JSON de type GPS.

    cout_index :
        0 -> distance
        1 -> temps
        2 -> vitesse (peu logique pour Dijkstra)
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    except json.JSONDecodeError:
        raise ValueError("Fichier JSON invalide")

    graphe: Dict[str, List[Dict[str, float]]] = {}

    for ville, voisins in data.items():
        graphe.setdefault(ville, [])

        if not isinstance(voisins, dict):
            continue

        for voisin, valeurs in voisins.items():
            if not isinstance(valeurs, list) or len(valeurs) < 1:
                continue

            try:
                cout = float(valeurs[cout_index])
            except (ValueError, IndexError):
                continue

            if cout < 0:
                raise ValueError("Dijkstra ne supporte pas les coûts négatifs")

            graphe[ville].append({
                "to": voisin,
                "weight": cout
            })

    return graphe


# ----------------------------------
# Dijkstra (dict-based robuste)
# ----------------------------------
def dijkstra(
    graph: Dict[str, List[Dict[str, float]]],
    start: str,
    end: Optional[str] = None
):
    if start not in graph:
        raise ValueError(f"Nœud de départ '{start}' absent du graphe")

    distances = {node: float("inf") for node in graph}
    predecesseurs = {node: None for node in graph}

    distances[start] = 0
    pq = [(0, start)]

    while pq:
        dist_actuelle, noeud_actuel = heapq.heappop(pq)

        if dist_actuelle > distances[noeud_actuel]:
            continue

        if end is not None and noeud_actuel == end:
            break

        for arc in graph[noeud_actuel]:
            voisin = arc["to"]
            poids = arc["weight"]

            nouvelle_distance = dist_actuelle + poids

            if nouvelle_distance < distances.get(voisin, float("inf")):
                distances[voisin] = nouvelle_distance
                predecesseurs[voisin] = noeud_actuel
                heapq.heappush(pq, (nouvelle_distance, voisin))

    return distances, predecesseurs


# ----------------------------------
# Reconstruction du chemin
# ----------------------------------
def reconstruire_chemin(
    predecesseurs: Dict[str, Optional[str]],
    start: str,
    end: str
) -> List[str]:
    chemin = []
    noeud = end

    while noeud is not None:
        chemin.append(noeud)
        noeud = predecesseurs.get(noeud)

    chemin.reverse()

    if chemin and chemin[0] == start:
        return chemin
    return []


# ----------------------------------
# Lancement automatique avec fichier
# ----------------------------------
if __name__ == "__main__":
    chemin_json = r"C:\Users\Axelm\Desktop\ENAC\Programmation\GPS-mieux-que-maps\src\data\dico_final.json"

    # 0 = distance | 1 = temps
    graphe = charger_graphe_json(chemin_json, cout_index=0)

    depart = "Toulouse_26686518"
    arrivee = "Tarbes_26691527"

    distances, predecesseurs = dijkstra(graphe, depart, arrivee)
    chemin = reconstruire_chemin(predecesseurs, depart, arrivee)

    if chemin:
        print(" -> ".join(chemin))
        print(f"Coût total en km: {distances[arrivee]:.2f}")
    else:
        print("Aucun chemin trouvé")


# ------------------------------
# Performance Tracking Dijkstra
# ------------------------------
import time

def dijkstra_with_stats(graph, start, end=None):
    start_time = time.perf_counter()

    nb_pop_pq = 0
    nb_relaxations = 0
    nb_arcs_testes = 0
    noeuds_visites = set()


    distances = {node: float("inf") for node in graph}
    predecesseurs = {node: None for node in graph}

    distances[start] = 0
    pq = [(0, start)]

    while pq:
        dist_actuelle, noeud_actuel = heapq.heappop(pq)
        nb_pop_pq += 1

        if dist_actuelle > distances[noeud_actuel]:
            continue
        noeuds_visites.add(noeud_actuel)

        if end is not None and noeud_actuel == end:
            break

        for arc in graph[noeud_actuel]:
            nb_arcs_testes += 1

            voisin = arc["to"]
            poids = arc["weight"]
            nouvelle_distance = dist_actuelle + poids

            if nouvelle_distance < distances[voisin]:
                distances[voisin] = nouvelle_distance
                predecesseurs[voisin] = noeud_actuel
                heapq.heappush(pq, (nouvelle_distance, voisin))
                nb_relaxations += 1

    temps_execution = time.perf_counter() - start_time

    stats = {
        "temps_execution (s)": temps_execution,
        "arcs_testes": nb_arcs_testes,
        "relaxations": nb_relaxations,
        "extractions_pq": nb_pop_pq,
        "noeuds_visites": len(noeuds_visites),
    }

    return distances, predecesseurs, stats


# -------------------------------
# Lancement automatique des stats
# -------------------------------
if __name__ == "__main__":
    _, _, stats = dijkstra_with_stats(graphe, depart, arrivee)

    print("\n--- Statistiques de performance ---")
    for k, v in stats.items():
        print(f"{k} : {v}")