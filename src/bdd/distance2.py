#Démarrer le script : python -m src.bdd.distance2
#Démarrer sur Mac : python3 -m src.bdd.distance2

import geopandas as gpd
import pandas as pd
import networkx as nx
import json
from shapely.geometry import Point, LineString
from shapely.ops import linemerge
from scipy.spatial import cKDTree
import warnings
from pyproj import Transformer
import numpy as np
from tqdm import tqdm
import math
import sqlite3
from ..lien_file import PATH_ROUTES, VILLES_ADJACENTS, CHEMIN_COORDS, CHEMIN_SORTIE

warnings.filterwarnings("ignore")

# ================= CONFIGURATION DES PARAMETRES =================
CHEMIN_ROUTES = PATH_ROUTES
VILLES_ADJACENTS = VILLES_ADJACENTS
CHEMIN_COORDS = CHEMIN_COORDS
CHEMIN_SORTIE = CHEMIN_SORTIE

SIN_K = 1.5
SIN_MIN = 0.4
SIN_MAX = 1.0

VITESSE_DEFAULT = {
    "motorway": 130, 
    "motorway_link": 90, 
    "trunk": 110, 
    "trunk_link": 70,
    "primary": 80, 
    "primary_link": 50, 
    "secondary": 80, 
    "secondary_link": 50,
    "tertiary": 50, 
    "tertiary_link": 50, 
    "residential": 50, 
    "living_street": 20,
    "unclassified": 50, 
    "service": 30,
    "path": 20, 
    "footway": 20, 
    "cycleway": 15, 
    "track": 20, 
    "track_grade1": 20,
    "track_grade2": 15, 
    "track_grade3": 10, 
    "track_grade4": 5, 
    "track_grade5": 5
}

POSSIBILITE_RACCORDEMENTS = {
    "service": 1.0, 
    "living_street": 1.0, 
    "residential": 1.0, 
    "unclassified": 1.2,
    "tertiary": 1.5, 
    "secondary": 3.0,
    "primary": 5.0, 
    "trunk": 10.0,
    "motorway": 20.0, 
    "motorway_link": 15.0,
    "path": 0.5, 
    "footway": 0.5, 
    "cycleway": 0.8
}

AUTOROUTES = ["motorway", "motorway_link"]
ROUTES_MAJEURES = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"}

# Pénalités pour optimiser le routage
PENALITE_PETIT_VILLAGE = 1.5
THRESHOLD_GRAND_CARREFOUR = 5

ATTRACTIVITE_ROUTE_FALLBACK = {
    "motorway": 0.1, "trunk": 0.2, "primary": 0.3, "secondary": 0.5,
    "tertiary": 0.8, "residential": 1.2, "service": 2.0, "track": 3.0, "connector": 10.0
}

# ================= FONCTIONS =================

def vitesses(row): #Trouver vitesse associer
    try:
        s = float(row["maxspeed"])
        if s > 0: return s
    except: 
        pass
    return VITESSE_DEFAULT.get(row["fclass"], 50)

def z_level(row): #Association z level
    try:
        layer = int(row["layer"])
        if layer != 0: return layer
    except: 
        pass
    contient_bridge = row.get("bridge", "F") in ["T", "True", True]
    contient_tunnel = row.get("tunnel", "F") in ["T", "True", True]
    return 1 if contient_bridge else (-1 if contient_tunnel else 0)

def indice_sinuosite(geom):
    try:
        longueur = geom.length
        start = Point(geom.coords[0])
        end = Point(geom.coords[-1])
        direct = start.distance(end)

        if direct == 0:
            return 1.0

        return max(1.0, longueur / direct)
    except:
        return 1.0
    
def facteur_sinuosite(sinuosite, fclass):
    if fclass in ["motorway", "motorway_link", "trunk"]:
        return 1.0

    facteur = math.exp(-SIN_K * (sinuosite - 1))
    return max(SIN_MIN, min(SIN_MAX, facteur))

def construction_graph_routes(gdf_roads_projected): #Transforme le fichier de route en graph orienté avec distance et temps
    print("Préparation des arêtes")
    gdf_arretes = gdf_roads_projected.explode(index_parts=False).reset_index(drop=True)
    
    gdf_arretes["weight"] = gdf_arretes.geometry.length
    print("Calcul sinuosité...")
    gdf_arretes["sinuosite"] = gdf_arretes.geometry.apply(indice_sinuosite)

    gdf_arretes["coef_sinuosite"] = gdf_arretes.apply(
        lambda r: facteur_sinuosite(r["sinuosite"], r["fclass"]),
        axis=1
    )

    gdf_arretes["speed_ms"] = (gdf_arretes["final_speed"] * gdf_arretes["coef_sinuosite"]) / 3.6
    
    # Pénalité légère pour routes locales (moins directes)
    gdf_arretes["penalite_locale"] = gdf_arretes["fclass"].apply(
        lambda f: 1.0 if f in ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"] else 1.1
    )
    
    gdf_arretes["time"] = np.where(
        gdf_arretes["speed_ms"] > 0,
        (gdf_arretes["weight"] / gdf_arretes["speed_ms"]) * gdf_arretes["penalite_locale"],
        math.inf
    )
    
    gdf_arretes["u"] = gdf_arretes.geometry.apply(lambda g: g.coords[0])
    gdf_arretes["v"] = gdf_arretes.geometry.apply(lambda g: g.coords[-1])

    cols = ["u", "v", "weight", "time", "geometry", "fclass", "z_level", "penalite_locale"]
    
    routes_direct = gdf_arretes["oneway"].isin(["F", "B", "N", "False", None])
    arrete_direct = gdf_arretes.loc[routes_direct, cols].copy()
    
    routes_inverse = gdf_arretes["oneway"].isin(["B", "N", "False", None])
    arretes_inverse = gdf_arretes.loc[routes_inverse, cols].copy()
    arretes_inverse = arretes_inverse.rename(columns={"u": "v", "v": "u"})
    arretes_inverse["geometry"] = arretes_inverse["geometry"].apply(lambda g: LineString(list(g.coords)[::-1]))
    
    arretes_tot = pd.concat([arrete_direct, arretes_inverse], ignore_index=True)

    G = nx.MultiDiGraph()
    for _, row in tqdm(arretes_tot.iterrows(), total=len(arretes_tot), desc="Construction Graphe"):
        G.add_edge(row["u"], row["v"], 
                   weight=row["weight"], time=row["time"], 
                   geometry=row["geometry"], fclass=row["fclass"], z_level=row["z_level"],
                   penalite_locale=row["penalite_locale"])
    
    if len(G) > 0:
        print("Traitement des composants isolés...")

        composants = list(nx.weakly_connected_components(G))
        composants_tries = sorted(composants, key=len, reverse=True)
        
        print(f"Total de {len(composants_tries)} composants détectés")
        print(f"  - Composant principal : {len(composants_tries[0])} nœuds")
        for i, comp in enumerate(composants_tries[1:], 1):
            print(f"  - Composant {i} : {len(comp)} nœuds")

        composant_principal = composants_tries[0]
        
        if len(composants_tries) > 1:
            print("Création de ponts virtuels vers le composant principal...")
            
            def trouver_hub_composant(G, composant):
                """Trouve le nœud-hub (degré sortant maximal) d'un composant"""
                noeud_hub = None
                max_degree = -1
                for noeud in composant:
                    degree = G.out_degree(noeud) + G.in_degree(noeud)
                    if degree > max_degree:
                        max_degree = degree
                        noeud_hub = noeud
                return noeud_hub if noeud_hub else next(iter(composant))

            hub_principal = trouver_hub_composant(G, composant_principal)

            for idx_comp, composant_isole in enumerate(composants_tries[1:], 1):
                hub_isole = trouver_hub_composant(G, composant_isole)

                hub_principal_coords = hub_principal
                hub_isole_coords = hub_isole
                
                if isinstance(hub_principal_coords, tuple) and isinstance(hub_isole_coords, tuple):
                    dx = hub_principal_coords[0] - hub_isole_coords[0]
                    dy = hub_principal_coords[1] - hub_isole_coords[1]
                    dist_euclidienne = math.sqrt(dx*dx + dy*dy)
                else:
                    dist_euclidienne = 5000

                poids_pont = dist_euclidienne * 1.5
                temps_pont = poids_pont / (100 / 3.6)

                if isinstance(hub_principal_coords, tuple) and isinstance(hub_isole_coords, tuple):
                    pont_geometry = LineString([hub_isole_coords, hub_principal_coords])
                else:
                    pont_geometry = LineString([(0, 0), (1, 1)])

                G.add_edge(hub_isole, hub_principal, 
                          weight=poids_pont, time=temps_pont, 
                          geometry=pont_geometry, fclass="virtual_bridge", z_level=0, penalite_locale=1.5)
                G.add_edge(hub_principal, hub_isole, 
                          weight=poids_pont, time=temps_pont, 
                          geometry=LineString(list(pont_geometry.coords)[::-1]), 
                          fclass="virtual_bridge", z_level=0, penalite_locale=1.5)
                
                print(f"  → Pont virtuel créé : Composant {idx_comp} ({len(composant_isole)} nœuds) ↔ Principal")
        
        print(f"Graphe final : {len(G.nodes)} nœuds, {G.number_of_edges()} arêtes")
        
    return G

def cherche_raccordement_villes_routes(point, gdf_arretes, spatial_index, G_nodes_set, distance_max=3000):
    x, y = point.x, point.y
    bbox = (x - distance_max, y - distance_max, x + distance_max, y + distance_max)
    
    routes_possibles_idx = list(spatial_index.intersection(bbox))
    
    if not routes_possibles_idx:
        return None
    
    arretes_possibles = gdf_arretes.iloc[routes_possibles_idx]
    dists = arretes_possibles.geometry.distance(point)
    mask = dists < distance_max
    
    if not mask.any():
        return None
        
    candidates = arretes_possibles[mask]
    candidate_dists = dists[mask]
    
    meilleur_routes_data = None
    meilleur_score = float('inf')

    for row, dist_geom in zip(candidates.itertuples(index=False), candidate_dists):
        u, v = row.u, row.v
        
        if u not in G_nodes_set and v not in G_nodes_set:
            continue
            
        penalite_z = 5.0 if row.z_level != 0 else 1.0

        fclass = row.fclass
        penalite_type_routes = POSSIBILITE_RACCORDEMENTS.get(fclass, 2.0)
        
        if fclass in ROUTES_MAJEURES:
            penalite_type_routes *= 0.5
        
        score = dist_geom * penalite_type_routes * penalite_z
        
        if score < meilleur_score:
            meilleur_score = score
            geom = row.geometry
            dist_along = geom.project(point)
            dist_along = max(0, min(geom.length, dist_along)) # Clamp
            proj_pt = geom.interpolate(dist_along)
            meilleur_routes_data = (row, proj_pt, dist_geom, dist_along)

    if meilleur_routes_data:
        best_row, proj_pt, dist_geom, dist_along = meilleur_routes_data
        data_dict = best_row._asdict()
        del data_dict['u']
        del data_dict['v']
        
        return {
            'arrete': (best_row.u, best_row.v),
            'données_arretes': data_dict,
            'projection_point': proj_pt,
            'distance': dist_geom,
            'coordonnées_projetes': (proj_pt.x, proj_pt.y),
            'dist_along': dist_along
        }

    return None

def insert_projected_point_in_graph(G, tree, listes_noeud, arrete_infos, point_villes, coord_villes):
    if arrete_infos is None:
        return None, False
    
    u, v = arrete_infos['arrete']
    données_arretes = arrete_infos['données_arretes']
    coordonnées_projetes = arrete_infos['coordonnées_projetes']
    
    distance, idx = tree.query([coordonnées_projetes[0], coordonnées_projetes[1]], k=1)
    
    if distance < 1.0:
        neoud_projeté = listes_noeud[idx]
    else:
        neoud_projeté = coordonnées_projetes
        geometrie_original = données_arretes['geometry']
        
        if 'dist_along' in arrete_infos:
            distance_afaire = arrete_infos['dist_along']
        else:
            projection_point = arrete_infos['projection_point']
            distance_afaire = geometrie_original.project(projection_point)
            
        liste_coordonnées = list(geometrie_original.coords)
        
        distance_tot = 0
        insertion_index = 1
        found = False
        
        for i in range(len(liste_coordonnées) - 1):
            p1 = liste_coordonnées[i]
            p2 = liste_coordonnées[i+1]
            d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            
            if distance_tot <= distance_afaire <= distance_tot + d + 0.01:
                insertion_index = i + 1
                found = True
                break
            distance_tot += d
        
        if not found:
            insertion_index = len(liste_coordonnées) - 1

        coords_ap = liste_coordonnées[:insertion_index] + [coordonnées_projetes]
        coords_pb = [coordonnées_projetes] + liste_coordonnées[insertion_index:]
        
        seg_ap = LineString(coords_ap)
        seg_pb = LineString(coords_pb)
        
        orig_w = données_arretes['weight']
        orig_t = données_arretes['time']
        def get_w_t(geom):
            l = geom.length
            ratio = l / orig_w if orig_w > 0 else 0
            return l, orig_t * ratio

        w_ap, t_ap = get_w_t(seg_ap)
        w_pb, t_pb = get_w_t(seg_pb)

        if G.has_edge(u, v):
            G.remove_edge(u, v)
            
        base_attrs = données_arretes.copy()
        for k in ['geometry', 'weight', 'time']:
            base_attrs.pop(k, None) 
        G.add_edge(u, neoud_projeté, weight=w_ap, time=t_ap, geometry=seg_ap, **base_attrs)
        G.add_edge(neoud_projeté, v, weight=w_pb, time=t_pb, geometry=seg_pb, **base_attrs)

        # Gestion sens inverse
        if G.has_edge(v, u):
            sens_inverse_data = G.get_edge_data(v, u)
            keys = list(sens_inverse_data.keys())
            for k in keys:
                d_inv = sens_inverse_data[k]
                if 'geometry' in d_inv:
                     G.remove_edge(v, u, key=k)
                     
                     inv_attrs = d_inv.copy()
                     inv_attrs.pop('geometry', None)
                     
                     inv_attrs['weight'] = w_pb
                     inv_attrs['time'] = t_pb
                     G.add_edge(v, neoud_projeté, geometry=LineString(list(seg_pb.coords)[::-1]), **inv_attrs)
                     
                     inv_attrs['weight'] = w_ap
                     inv_attrs['time'] = t_ap
                     G.add_edge(neoud_projeté, u, geometry=LineString(list(seg_ap.coords)[::-1]), **inv_attrs)

    villes_a_projeté = LineString([point_villes, Point(neoud_projeté)])
    dist_v = villes_a_projeté.length
    time_v = dist_v / (30/3.6)
    
    G.add_edge(coord_villes, neoud_projeté, weight=dist_v, time=time_v, 
               geometry=villes_a_projeté, fclass="service", z_level=0)
    G.add_edge(neoud_projeté, coord_villes, weight=dist_v, time=time_v, 
               geometry=LineString(list(villes_a_projeté.coords)[::-1]), fclass="service", z_level=0)
    
    return neoud_projeté, True

def raccorde_ville_route(G, coord_villes, coord_villes_projeté, distance_m):
    temps_s = distance_m / (30 / 3.6)

    geom_connexion = LineString([coord_villes, coord_villes_projeté])
    geom_inverse = LineString([coord_villes_projeté, coord_villes])
    
    G.add_edge(coord_villes, coord_villes_projeté, 
               weight=distance_m, time=temps_s, 
               geometry=geom_connexion, fclass="connector", z_level=0)

    G.add_edge(coord_villes_projeté, coord_villes, 
               weight=distance_m, time=temps_s, 
               geometry=geom_inverse, fclass="connector", z_level=0)

def meilleur_noeud_fallback(point_ville, arbre, liste_noeud, G, k_voisins=10):
    coords_ville = (point_ville.x, point_ville.y)
    distances, indices = arbre.query([coords_ville[0], coords_ville[1]], k=k_voisins)
    
    meilleur_noeud = None
    meilleur_score = float('inf')

    for dist, idx in zip(distances, indices):
        neoud = liste_noeud[idx]
        
        if not G.has_node(neoud): 
            continue
        voisins = G[neoud]
        if not voisins:
            continue

        coeff_actuel = 5.0
        
        for nbr, edge_data in voisins.items():
            if isinstance(G, (type(None),)):
                pass 
            
            datas_to_check = edge_data.values() if G.is_multigraph() else [edge_data]
            
            for data in datas_to_check:
                f = data.get("fclass")
                coeff = ATTRACTIVITE_ROUTE_FALLBACK.get(f, 2.0)
                if coeff < coeff_actuel:
                    coeff_actuel = coeff
        
        score = dist * coeff_actuel
        
        if score < meilleur_score:
            meilleur_score = score
            meilleur_noeud = neoud

    real_dist = distances[0] if len(distances) > 0 else 0
    return meilleur_noeud, real_dist

def distance_orthodromique(coord1, coord2):
    dx = coord2[0] - coord1[0]
    dy = coord2[1] - coord1[1]
    return math.sqrt(dx*dx + dy*dy)

def nettoyer_boucles_chemin(chemin_noeuds):
    if len(chemin_noeuds) <= 2:
        return chemin_noeuds
    
    chemin_nettoyé = []
    for noeud in chemin_noeuds:
        if noeud in chemin_nettoyé:
            idx_ancien = chemin_nettoyé.index(noeud)
            chemin_nettoyé = chemin_nettoyé[:idx_ancien + 1]
        else:
            chemin_nettoyé.append(noeud)
    
    return chemin_nettoyé

# ================= PRINCIPAL =================

if __name__ == "__main__":
    print("Chargement des données...")
    gdf = gpd.read_file(CHEMIN_ROUTES)

    gdf = gdf.copy()

    print("Calcul des vitesses et niveaux Z...")
    gdf["final_speed"] = gdf.apply(vitesses, axis=1)

    for col in ["layer", "bridge", "tunnel"]:
        if col not in gdf.columns:
            gdf[col] = 0 if col == "layer" else "F"

    gdf["z_level"] = gdf.apply(z_level, axis=1)

    print("Reprojection des routes...")
    gdf_proj = gdf.to_crs(epsg=2154)
    transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)

    print("Chargement JSON villes...")
    with open(VILLES_ADJACENTS, "r", encoding="utf-8") as f:
        adj_data = json.load(f)
    with open(CHEMIN_COORDS, "r", encoding="utf-8") as f:
        coords_data = json.load(f)

    DB_FILE = r"src\data\sqlite\routes.db"

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS villes (
        id TEXT PRIMARY KEY,
        nom TEXT,
        lat REAL,
        lon REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        from_id TEXT,
        to_id TEXT,
        distance_km REAL,
        temps_min REAL,
        vitesse_moy REAL,
        autoroute INTEGER,
        geometry TEXT,
        PRIMARY KEY (from_id, to_id)
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_routes_from ON routes(from_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_routes_to ON routes(to_id)")
    conn.commit()

    print("Conversion des villes...")
    cities_data_list = []
    for city_id, info in tqdm(coords_data.items(), desc="Traitement JSON villes"):
        lat, lon = info.get("lat"), info.get("lon")
        if lat is not None and lon is not None:
            cities_data_list.append({
                "city_id": city_id,
                "geometry": Point(lon, lat)
            })

    villes_gdf = gpd.GeoDataFrame(cities_data_list, crs="EPSG:4326").to_crs(epsg=2154)
    villes_gdf.set_index("city_id", inplace=True)

    G = construction_graph_routes(gdf_proj)
    set_noeud_validé = set(G.nodes)
    liste_noeud_validé = list(set_noeud_validé)
    arbre = cKDTree(liste_noeud_validé)

    print("Indexation spatiale des routes...")
    index_arrete_liste = []
    for u, v, data in G.edges(data=True):
        if data.get("z_level", 0) == 0:
            d = data.copy()
            d['u'], d['v'] = u, v
            index_arrete_liste.append(d)

    gdf_arretes_index = gpd.GeoDataFrame(index_arrete_liste, crs="EPSG:2154")
    index_spatial = gdf_arretes_index.sindex

    print("Raccordement des villes au réseau...")
    villes_raccordées = {}
    villes_buffer = []
    
    for name, row in tqdm(villes_gdf.iterrows(), total=len(villes_gdf), desc="Projection"):
        point_ville = row.geometry
        coords_villes = (point_ville.x, point_ville.y)

        info_arrete = cherche_raccordement_villes_routes(point_ville, gdf_arretes_index, index_spatial, set_noeud_validé)
        
        raccordé = False
        if info_arrete:
            _, succès = insert_projected_point_in_graph(
                G, arbre, liste_noeud_validé, info_arrete, point_ville, coords_villes
            )
            raccordé = succès

        if not raccordé:
            best_node, real_dist = meilleur_noeud_fallback(point_ville, arbre, liste_noeud_validé, G)
            if best_node:
                raccorde_ville_route(G, coords_villes, best_node, real_dist)
                raccordé = True
            else:
                print(f"Erreur critique : Impossible de raccorder {name}")

        if raccordé:
            villes_raccordées[name] = {"node": coords_villes, "orig_data": coords_data[name]}
            villes_buffer.append((
                name,
                coords_data[name].get("nom_affichage", name),
                coords_data[name]["lat"],
                coords_data[name]["lon"]
            ))

    if villes_buffer:
        cur.executemany("""
        INSERT OR IGNORE INTO villes VALUES (?, ?, ?, ?)
        """, villes_buffer)
        conn.commit()

    sortie = {}
    stats_succès, stats_échec = 0, 0
    routes_buffer = []
    
    for ville_nom, villes_voisines in tqdm(adj_data.items(), desc="Calcul Itinéraires"):
        if ville_nom not in villes_raccordées: 
            continue

        noeud_départ = villes_raccordées[ville_nom]["node"]
        sortie[ville_nom] = {"coords": villes_raccordées[ville_nom]["orig_data"], "adjacents": []}

        try:
            paths = nx.single_source_dijkstra_path(G, source=noeud_départ, weight="time")
            times = nx.single_source_dijkstra_path_length(G, source=noeud_départ, weight="time")
            dists = nx.single_source_dijkstra_path_length(G, source=noeud_départ, weight="weight")
        except Exception:
            paths = {}
            times = {}
            dists = {}

        for voisin_nom in villes_voisines:
            if voisin_nom not in villes_raccordées: 
                continue
            noeud_fin = villes_raccordées[voisin_nom]["node"]

            try:
                dist_ortho = distance_orthodromique(noeud_départ, noeud_fin)

                if noeud_fin not in paths:
                    raise nx.NetworkXNoPath()

                chemin_de_noeuds = paths[noeud_fin]
                chemin_de_noeuds = nettoyer_boucles_chemin(chemin_de_noeuds)

                total_temps = times.get(noeud_fin, 0)
                total_dist = dists.get(noeud_fin, 0)
                sur_autoroute = False

                chemin_geom = []
                for i in range(len(chemin_de_noeuds) - 1):
                    u, v = chemin_de_noeuds[i], chemin_de_noeuds[i+1]
                    arrete_data = G.get_edge_data(u, v)
                    if not arrete_data:
                        continue
                    meilleur_k = min(arrete_data, key=lambda k: arrete_data[k]["time"])
                    data = arrete_data[meilleur_k]
                    chemin_geom.append(data["geometry"])
                    if data.get("fclass") in AUTOROUTES:
                        sur_autoroute = True

                if total_dist > 3 * dist_ortho:
                    ligne_directe = LineString([Point(noeud_départ), Point(noeud_fin)])
                    total_dist = dist_ortho
                    total_temps = dist_ortho / (80 / 3.6)
                    chemin_geom = [ligne_directe]
                    sur_autoroute = False

                ligne_route = linemerge(chemin_geom)
                listes_coords = []
                if ligne_route is not None and not ligne_route.is_empty:
                    if ligne_route.geom_type == 'LineString':
                        coords = list(ligne_route.coords)
                    else:
                        coords = []
                        for g in ligne_route.geoms:
                            coords.extend(list(g.coords))

                    if coords:
                        xs, ys = zip(*coords)
                        lons, lats = transformer.transform(xs, ys)
                        listes_coords = list(zip(lons, lats))

                dist_km = total_dist / 1000.0
                if dist_km > 100:
                    continue

                sortie[ville_nom]["adjacents"].append({
                    "nom": voisin_nom,
                    "distance_km": round(dist_km, 2),
                    "temps_min": round(total_temps / 60, 2),
                    "vitesse_moyenne_kmh": round(dist_km / (total_temps / 3600), 2) if total_temps > 0 else 0,
                    "autoroute": sur_autoroute,
                    "path_geometry": listes_coords
                })
                routes_buffer.append((
                    ville_nom,
                    voisin_nom,
                    round(dist_km, 2),
                    round(total_temps / 60, 2),
                    round(dist_km / (total_temps / 3600), 2) if total_temps > 0 else 0,
                    int(sur_autoroute),
                    json.dumps(listes_coords)
                ))
                stats_succès += 1

            except (nx.NetworkXNoPath, Exception):
                stats_échec += 1
    cur.executemany("""
    INSERT OR REPLACE INTO routes VALUES (?, ?, ?, ?, ?, ?, ?)
    """, routes_buffer)
    conn.commit()
    conn.close()
    print(f"Terminé. Succès : {stats_succès}, Échecs : {stats_échec}")
    with open(CHEMIN_SORTIE, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=4)