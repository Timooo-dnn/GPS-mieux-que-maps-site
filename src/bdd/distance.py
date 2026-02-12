#python -m src.bdd.distance
#python3 -m src.bdd.distance

import geopandas as gpd
import pandas as pd
import networkx as nx
import json
from shapely.geometry import Point, LineString
from shapely.ops import linemerge
from scipy.spatial import cKDTree
import warnings
import numpy as np
from tqdm import tqdm
import math
import sqlite3
from pathlib import Path
warnings.filterwarnings("ignore")
PATH_ROUTES = r"src\data\gis_osm_roads_free_1.shp"
VILLES_ADJACENTS = r"src\data\adjacences_villes.json"
CHEMIN_COORDS = r"src\data\coords_villes.json"
CHEMIN_SORTIE = r"src\data\routes_villes_adj.json"
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

PENALITE_PETIT_VILLAGE = 1.5
THRESHOLD_GRAND_CARREFOUR = 5

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
        print("Nettoyage des routes isolées...")
        largest_cc = max(nx.weakly_connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()
        print(f"Graphe principal : {len(G.nodes)} nœuds.")
        
    return G

def cherche_raccordement_villes_routes(point, gdf_arretes, spatial_index, G_nodes_set, distance_max=3000): #Identifie le meilleur point d'ancrage pour chaque ville sur le graph précédent
    # Création d'un rectangle (bounding box) autour de la ville avec le rayon distance_max pour limiter la recherche aux routes proches
    rayon_3 = point.buffer(distance_max).bounds
    
    # Recherche dans l'index spatial des routes dont la bounding box intersecte le rectangle
    routes_possibles = list(spatial_index.intersection(rayon_3))
    
    # Si aucune route n'est proche, on renvoie None
    if not routes_possibles:
        return None

    # Sélection des routes candidates à partir des indices trouvés
    arretes_possibles = gdf_arretes.iloc[routes_possibles].copy()
    
    # Calcul de la distance entre la ville et chaque route candidate
    arretes_possibles["dist_geom"] = arretes_possibles.geometry.distance(point)
    
    # Filtrage des routes trop éloignées (distance supérieure à distance_max)
    arretes_possibles = arretes_possibles[arretes_possibles["dist_geom"] < distance_max]
    
    # Si aucune route n'est dans le rayon autorisé, on renvoie None
    if arretes_possibles.empty:
        return None

    # Initialisation des variables pour mémoriser la meilleure route
    meilleur_routes = None
    meilleur_score = float('inf')

    # Parcours des routes candidates
    for idx, row in arretes_possibles.iterrows():
        u, v = row['u'], row['v']  # nœuds de l'arête candidate
        
        # On ne considère que les routes connectées à au moins un nœud déjà dans le graphe
        if u not in G_nodes_set and v not in G_nodes_set:
            continue
            
        # Application d'une pénalité si l'arête est sur un niveau z différent de 0 (ex: pont, tunnel) pour éviter de s'y attacher sauf "extrême" nécessité
        penalite_z = 1.0
        if row['z_level'] != 0:
            penalite_z = 5.0

        # Définition des routes majeures pour réduire leur pénalité
        routes_majeures = ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"]
        
        # Pénalité selon le type de route, pénalité en fonction de POSSIBILITE_RACCORDEMENTS et si non défini alors 2 par défaut
        penalite_type_routes = POSSIBILITE_RACCORDEMENTS.get(row['fclass'], 2.0)
        
        # Si c'est une route majeure, on divise la pénalité par 2, préférence pour ce type de route
        if row['fclass'] in routes_majeures:
            penalite_type_routes *= 0.5
        
        # Calcul du score de cette route : distance * pénalité type * pénalité z
        score = row['dist_geom'] * penalite_type_routes * penalite_z
        
        # Si ce score est meilleur que le meilleur score précédent, on mémorise cette route
        if score < meilleur_score:
            meilleur_score = score
            
            geom = row.geometry  # géométrie de l'arête
            # Calcul de la distance projetée le long de l'arête
            dist_along = geom.project(point)
            dist_along = max(0, min(geom.length, dist_along))  # s'assure que la distance est dans les bornes
            
            # Calcul du point projeté sur l'arête
            proj_pt = geom.interpolate(dist_along)
            
            # Enregistrement des informations de la meilleure route
            meilleur_routes = {
                'arrete': (u, v),
                'données_arretes': row.drop(['u', 'v', 'dist_geom']).to_dict(),
                'projection_point': proj_pt,             # shapely Point projeté
                'distance': row['dist_geom'],           # distance du point à l'arête
                'coordonnées_projetes': (proj_pt.x, proj_pt.y)  # coordonnées X,Y du point projeté
            }

    # Retourne la meilleure route trouvée ou None si aucune
    return meilleur_routes

def insert_projected_point_in_graph(G, tree, listes_noeud, arrete_infos, point_villes, coord_villes): #Crée une intersection la ou le meilleur point d'ancrage a été identifié
    if arrete_infos is None:
        return None, False
    
    u, v = arrete_infos['arrete']
    données_arretes = arrete_infos['données_arretes']
    coordonnées_projetes = arrete_infos['coordonnées_projetes']
    projection_point = arrete_infos['projection_point']
    
    distance, idx = tree.query([coordonnées_projetes[0], coordonnées_projetes[1]], k=1)
    
    if distance < 1.0:
        neoud_projeté = listes_noeud[idx]
    else:
        neoud_projeté = coordonnées_projetes

        geometrie_original = données_arretes['geometry']
        distance_afaire = geometrie_original.project(projection_point)
        liste_coordonnées = list(geometrie_original.coords)
        
        distance_tot = 0
        insertion_index = 1
        for i in range(len(liste_coordonnées) - 1):
            p1, p2 = Point(liste_coordonnées[i]), Point(liste_coordonnées[i+1])
            d = p1.distance(p2)
            if distance_tot <= distance_afaire <= distance_tot + d + 0.01:
                insertion_index = i + 1
                break
            distance_tot += d
        
        coords_ap = liste_coordonnées[:insertion_index] + [coordonnées_projetes]
        coords_pb = [coordonnées_projetes] + liste_coordonnées[insertion_index:]
        
        seg_ap = LineString(coords_ap)
        seg_pb = LineString(coords_pb)
        
        def data_routes_créé(geom, orig_w, orig_t):
            ratio = geom.length / orig_w if orig_w > 0 else 0
            return geom.length, orig_t * ratio

        w_ap, t_ap = data_routes_créé(seg_ap, données_arretes['weight'], données_arretes['time'])
        w_pb, t_pb = data_routes_créé(seg_pb, données_arretes['weight'], données_arretes['time'])

        if G.has_edge(u, v):
            G.remove_edge(u, v)
            
        G.add_edge(u, neoud_projeté, weight=w_ap, time=t_ap, geometry=seg_ap, 
                   fclass=données_arretes['fclass'], z_level=données_arretes.get('z_level', 0))
        G.add_edge(neoud_projeté, v, weight=w_pb, time=t_pb, geometry=seg_pb, 
                   fclass=données_arretes['fclass'], z_level=données_arretes.get('z_level', 0))

        sens_inverse = G.get_edge_data(v, u)
        if sens_inverse:
            keys = list(sens_inverse.keys())
            for k in keys:
                données_sens_inverse = sens_inverse[k]
                if 'geometry' in données_sens_inverse:
                    G.remove_edge(v, u, key=k)
                    G.add_edge(v, neoud_projeté, weight=w_pb, time=t_pb, 
                               geometry=LineString(list(seg_pb.coords)[::-1]),
                               fclass=données_sens_inverse['fclass'], z_level=données_sens_inverse.get('z_level', 0))
                    G.add_edge(neoud_projeté, u, weight=w_ap, time=t_ap, 
                               geometry=LineString(list(seg_ap.coords)[::-1]),
                               fclass=données_sens_inverse['fclass'], z_level=données_sens_inverse.get('z_level', 0))

    villes_a_projeté = LineString([point_villes, projection_point])
    dist_v = villes_a_projeté.length
    time_v = dist_v / (30/3.6)
    
    G.add_edge(coord_villes, neoud_projeté, weight=dist_v, time=time_v, 
               geometry=villes_a_projeté, fclass="service", z_level=0)
    G.add_edge(neoud_projeté, coord_villes, weight=dist_v, time=time_v, 
               geometry=LineString(list(villes_a_projeté.coords)[::-1]), fclass="service", z_level=0)
    
    return neoud_projeté, True

def raccorde_ville_route(G, coord_villes, coord_villes_projeté, distance_m): #Crée le lien (D/I) entre la nouvelle intersection et la ville
    temps_s = distance_m / (30 / 3.6)
    
    geom_ville_vers_route= LineString([coord_villes, coord_villes_projeté])
    geom_route_vers_ville = LineString([coord_villes, coord_villes_projeté])
    
    G.add_edge(coord_villes, coord_villes_projeté, 
               weight=distance_m, time=temps_s, 
               geometry=geom_ville_vers_route, fclass="connector", z_level=0)

    G.add_edge(coord_villes_projeté, coord_villes, 
               weight=distance_m, time=temps_s, 
               geometry=geom_route_vers_ville, fclass="connector", z_level=0)

def meilleur_noeud_fallback(point_ville, arbre, liste_noeud, G, k_voisins=10): #Si aucune route n'est trouvé précédemment, on utilise le noeud le plus logique autour de la ville
    coords_ville = (point_ville.x, point_ville.y)
    distances, indices = arbre.query([coords_ville[0], coords_ville[1]], k=k_voisins)
    
    meilleur_noeud = None
    meilleur_score = float('inf')

    attractivité_route = {
        "motorway": 0.1,
        "trunk": 0.2,
        "primary": 0.3,
        "secondary": 0.5,
        "tertiary": 0.8,
        "residential": 1.2,
        "service": 2.0,
        "track": 3.0,
        "connector": 10.0
    }

    for dist, idx in zip(distances, indices):
        neoud = liste_noeud[idx]
        
        arrtes = G.edges(neoud, data=True)
        if not arrtes:
            continue
            
        meilleur_fclass = "service"
        classes_found = [data.get("fclass") for _, _, data in arrtes]
        
        coeff_actuel = 5.0
        for f in classes_found:
            coeff = attractivité_route.get(f, 2.0)
            if coeff < coeff_actuel:
                coeff_actuel = coeff
        
        score = dist * coeff_actuel
        
        if score < meilleur_score:
            meilleur_score = score
            meilleur_noeud = neoud

    return meilleur_noeud, distances[0]

def distance_orthodromique(coord1, coord2):
    # Les coordonnées en Lambert93 sont en mètres, calcul simple
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

    print("Chargement JSON villes...")
    with open(VILLES_ADJACENTS, "r", encoding="utf-8") as f:
        adj_data = json.load(f)

    # ===== Forcer les adjacences bidirectionnelles =====
    for ville, voisins in list(adj_data.items()):
        for voisin in voisins:
            adj_data.setdefault(voisin, [])
            if ville not in adj_data[voisin]:
                adj_data[voisin].append(ville)
    print(f"Adjacences totales après symétrie : {sum(len(v) for v in adj_data.values())}")
    #====================================================
            
    with open(CHEMIN_COORDS, "r", encoding="utf-8") as f:
        coords_data = json.load(f)

    BASE_DIR = Path(__file__).resolve().parents[2]
    DB_FILE = BASE_DIR / "src" / "data" / "sqlite" / "routes.db"

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
        tire_droit INTEGER,
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

    # Graphs routes
    G = construction_graph_routes(gdf_proj)
    set_noeud_validé = set(G.nodes)
    liste_noeud_validé = list(set_noeud_validé)
    arbre = cKDTree(liste_noeud_validé)

    # applicage des layer
    print("Indexation spatiale des routes...")
    index_arrete_liste = []
    for u, v, data in G.edges(data=True):
        if data.get("z_level", 0) == 0:
            d = data.copy()
            d['u'], d['v'] = u, v
            index_arrete_liste.append(d)

    gdf_arretes_index = gpd.GeoDataFrame(index_arrete_liste, crs="EPSG:2154")
    index_spatial = gdf_arretes_index.sindex

    # Raccordement intelligent des villes
    print("Raccordement des villes au réseau...")
    villes_raccordées = {}
    
    for name, row in tqdm(villes_gdf.iterrows(), total=len(villes_gdf), desc="Projection"):
        point_ville = row.geometry
        coords_villes = (point_ville.x, point_ville.y)

        info_arrete = cherche_raccordement_villes_routes(point_ville, gdf_arretes_index, index_spatial, set_noeud_validé)
        
        lien_succès = False
        if info_arrete:
            _, succès = insert_projected_point_in_graph(
                G, arbre, liste_noeud_validé, info_arrete, point_ville, coords_villes
            )
            if succès:
                villes_raccordées[name] = {"node": coords_villes, "orig_data": coords_data[name]}
                lien_succès = True
                cur.execute("""
                INSERT OR IGNORE INTO villes VALUES (?, ?, ?, ?)
                """, (
                    name,
                    coords_data[name].get("nom_affichage", name),
                    coords_data[name]["lat"],
                    coords_data[name]["lon"]
                ))

        if not lien_succès:
            best_node, real_dist = meilleur_noeud_fallback(point_ville, arbre, liste_noeud_validé, G)

            if best_node:
                raccorde_ville_route(G, coords_villes, best_node, real_dist)
                villes_raccordées[name] = {"node": coords_villes, "orig_data": coords_data[name]}
                cur.execute("""
                INSERT OR IGNORE INTO villes VALUES (?, ?, ?, ?)
                """, (
                    name,
                    coords_data[name].get("nom_affichage", name),
                    coords_data[name]["lat"],
                    coords_data[name]["lon"]
                ))
            else:
                print(f"Erreur critique : Impossible de raccorder {name}")

    # Calcul des itinéraires
    sortie = {}
    stats_succès, stats_échec = 0, 0
    stats_tire_droit = 0
    stats_distances = []  # Pour analyser les ratios distance/ortho
    routes_buffer = []
    
    for ville_nom, villes_voisines in tqdm(adj_data.items(), desc="Calcul Itinéraires"):
        if ville_nom not in villes_raccordées: 
            continue

        noeud_départ = villes_raccordées[ville_nom]["node"]
        sortie[ville_nom] = {"coords": villes_raccordées[ville_nom]["orig_data"], "adjacents": []}

        for voisin_nom in villes_voisines:
            if voisin_nom not in villes_raccordées: 
                continue
            noeud_fin = villes_raccordées[voisin_nom]["node"]

            try:
                # 1. Calculer distance orthodromique (vol d'oiseau)
                dist_ortho = distance_orthodromique(noeud_départ, noeud_fin)
                
                # 2. Chercher le chemin par routes
                chemin_de_noeuds = nx.shortest_path(G, source=noeud_départ, target=noeud_fin, weight="time")
                
                # 3. Nettoyer les boucles
                chemin_de_noeuds = nettoyer_boucles_chemin(chemin_de_noeuds)
                
                # 4. Calculer distance et temps réels
                chemin_geom = []
                total_dist, total_temps = 0, 0
                sur_autoroute = False

                for i in range(len(chemin_de_noeuds) - 1):
                    u, v = chemin_de_noeuds[i], chemin_de_noeuds[i+1]
                    arrete_data = G.get_edge_data(u, v)
                    if arrete_data is None:
                        continue
                    meilleur_k = min(arrete_data, key=lambda k: arrete_data[k]["time"])
                    data = arrete_data[meilleur_k]

                    chemin_geom.append(data["geometry"])
                    total_dist += data["weight"]
                    total_temps += data["time"]
                    if data.get("fclass") in AUTOROUTES: sur_autoroute = True
                
                # 5. Si la distance par routes > 3x la distance orthodromique, utiliser la droite
                tire_droit = False
                if total_dist > 3 * dist_ortho:
                    # Utiliser un lien direct entre les deux villes
                    coord_depart = Point(noeud_départ)
                    coord_fin = Point(noeud_fin)
                    ligne_directe = LineString([coord_depart, coord_fin])
                    
                    total_dist = dist_ortho
                    total_temps = dist_ortho / (80 / 3.6)  # Assumer 80 km/h en moyenne
                    chemin_geom = [ligne_directe]
                    sur_autoroute = False
                    tire_droit = True

                ligne_route = linemerge(chemin_geom)
                ligne_route_wgs84 = gpd.GeoSeries([ligne_route], crs="EPSG:2154").to_crs(epsg=4326).iloc[0]
                
                listes_coords = list(ligne_route_wgs84.coords) if ligne_route_wgs84.geom_type == 'LineString' else []
                if not listes_coords and ligne_route_wgs84.geom_type == 'MultiLineString':
                    for g in ligne_route_wgs84.geoms: listes_coords.extend(list(g.coords))

                dist_km = total_dist / 1000.0
                if dist_km > 100: 
                    continue

                sortie[ville_nom]["adjacents"].append({
                    "nom": voisin_nom,
                    "distance_km": round(dist_km, 2),
                    "temps_min": round(total_temps / 60, 2),
                    "vitesse_moyenne_kmh": round(dist_km / (total_temps / 3600), 2) if total_temps > 0 else 0,
                    "autoroute": sur_autoroute,
                    "tire_droit": tire_droit,
                    "path_geometry": listes_coords
                })
                routes_buffer.append((
                    ville_nom,
                    voisin_nom,
                    round(dist_km, 2),
                    round(total_temps / 60, 2),
                    round(dist_km / (total_temps / 3600), 2) if total_temps > 0 else 0,
                    int(sur_autoroute),
                    int(tire_droit),
                    json.dumps(listes_coords)
                ))
                stats_succès += 1

            except (nx.NetworkXNoPath, Exception):
                stats_échec += 1
    cur.executemany("""
    INSERT OR REPLACE INTO routes VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, routes_buffer)
    conn.commit()
    conn.close()
    print(f"Terminé. Succès : {stats_succès}, Échecs : {stats_échec}")

    #==============Symétrisation de routes_villes_adj.json=================

    for ville, data in list(sortie.items()):
        for adj in data["adjacents"]:
            voisin = adj["nom"]

            sortie.setdefault(voisin, {
                "coords": coords_data.get(voisin, {}),
                "adjacents": []
            })

            # éviter les doublons
            noms_existants = {a["nom"] for a in sortie[voisin]["adjacents"]}

            if ville not in noms_existants:
                adj_inverse = adj.copy()
                adj_inverse["nom"] = ville
                sortie[voisin]["adjacents"].append(adj_inverse)
#==========================================================================

    with open(CHEMIN_SORTIE, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=4)