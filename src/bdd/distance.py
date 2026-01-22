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

warnings.filterwarnings("ignore")

# ================= CONFIGURATION =================
PATH_ROADS = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\gis_osm_roads_free_1.shp"
PATH_ADJACENTS = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\adjacences_villes.json"
PATH_COORDS = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\coords_villes.json"
PATH_OUTPUT = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\routes_villes_adj.json"

SPEED_DEFAULTS = {
    'motorway': 130,
    'motorway_link': 90,
    'trunk': 110,
    'trunk_link': 70,
    'primary': 80,
    'primary_link': 50,
    'secondary': 80,
    'secondary_link': 50,
    'tertiary': 50,
    'tertiary_link': 50,
    'residential': 50,
    'living_street': 20,
    'unclassified': 50,
    'service': 30
}

# ================= FONCTIONS =================

def get_speed(row):
    try:
        s = float(row['maxspeed'])
        if s > 0:
            return s
    except:
        pass
    return SPEED_DEFAULTS.get(row['fclass'], 50)


def build_projected_graph(gdf_roads_projected):
    print("Construction du graphe haute précision...")

    # Éclatement des MultiLineString
    gdf_edges = gdf_roads_projected.explode(index_parts=False).reset_index(drop=True)

    # Calculs des attributs
    gdf_edges['weight'] = gdf_edges.geometry.length
    gdf_edges['speed_ms'] = gdf_edges['final_speed'] / 3.6
    gdf_edges['time'] = np.where(
        gdf_edges['speed_ms'] > 0,
        gdf_edges['weight'] / gdf_edges['speed_ms'],
        0
    )

    # Extraction des extrémités
    gdf_edges['u'] = gdf_edges.geometry.apply(lambda geom: geom.coords[0])
    gdf_edges['v'] = gdf_edges.geometry.apply(lambda geom: geom.coords[-1])

    cols_to_keep = ['u', 'v', 'weight', 'time', 'geometry']

    # --- Sens Direct ---
    mask_direct = gdf_edges['oneway'].isin(['F', 'B', 'N', 'False', None])
    edges_direct = gdf_edges.loc[mask_direct, cols_to_keep].copy()

    # --- Sens Inverse ---
    mask_reverse = gdf_edges['oneway'].isin(['B', 'N', 'False', None])
    edges_reverse = gdf_edges.loc[mask_reverse, cols_to_keep].copy()
    edges_reverse = edges_reverse.rename(columns={'u': 'v', 'v': 'u'})
    edges_reverse['geometry'] = edges_reverse['geometry'].apply(
        lambda x: LineString(list(x.coords)[::-1])
    )

    all_edges = pd.concat([edges_direct, edges_reverse], ignore_index=True)

    # 5. Création du MultiDiGraph
    G = nx.MultiDiGraph()
    for _, row in all_edges.iterrows():
        G.add_edge(
            row['u'],
            row['v'],
            weight=row['weight'],
            time=row['time'],
            geometry=row['geometry']
        )

    # Nettoyage
    if len(G) > 0:
        largest_cc = max(nx.weakly_connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()
        print(f"Graphe prêt : {len(G.nodes)} nœuds.")

    return G

# ================= Principal =================

print("1. Chargement des données...")
gdf = gpd.read_file(PATH_ROADS)

gdf = gdf[gdf['fclass'].isin(SPEED_DEFAULTS.keys())].copy()
gdf['final_speed'] = gdf.apply(get_speed, axis=1)
gdf_proj = gdf.to_crs(epsg=2154)

with open(PATH_ADJACENTS, 'r', encoding='utf-8') as f:
    adj_data = json.load(f)

with open(PATH_COORDS, 'r', encoding='utf-8') as f:
    coords_data = json.load(f)

G = build_projected_graph(gdf_proj)

# Arbres de recherche
graph_nodes_xy = list(G.nodes)
tree = cKDTree(graph_nodes_xy)

# Pré-calcul des villes
print("Raccordement des villes au réseau...")
cities_df = pd.DataFrame.from_dict(coords_data, orient='index').dropna(
    subset=['lon', 'lat']
)
cities_gdf = gpd.GeoDataFrame(
    cities_df,
    geometry=gpd.points_from_xy(cities_df.lon, cities_df.lat),
    crs="EPSG:4326"
).to_crs(epsg=2154)

processed_cities = {}
city_coords = np.c_[cities_gdf.geometry.x, cities_gdf.geometry.y]
dists, idxs = tree.query(city_coords, k=1)

for i, name in enumerate(cities_gdf.index):
    processed_cities[name] = {
        "node": graph_nodes_xy[idxs[i]],
        "dist_to_road": dists[i],
        "orig_data": coords_data[name]
    }

# Calculs
final_output = {}
stats_success, stats_fail = 0, 0

for ville_nom, villes_voisines in tqdm(adj_data.items(), desc="Calcul"):
    if (
        ville_nom not in processed_cities
        or processed_cities[ville_nom]['dist_to_road'] > 5000
    ):
        continue

    start_info = processed_cities[ville_nom]
    final_output[ville_nom] = {
        "coords": start_info['orig_data'],
        "adjacents": []
    }

    for voisin_nom in villes_voisines:
        if voisin_nom not in processed_cities:
            continue

        end_info = processed_cities[voisin_nom]

        try:
            path_nodes = nx.shortest_path(
                G,
                source=start_info['node'],
                target=end_info['node'],
                weight='weight'
            )

            path_geometries = []
            total_dist, total_time = 0, 0

            for u, v in zip(path_nodes[:-1], path_nodes[1:]):
                data = min(
                    G.get_edge_data(u, v).values(),
                    key=lambda x: x['weight']
                )
                path_geometries.append(data['geometry'])
                total_dist += data['weight']
                total_time += data['time']

            full_line_proj = linemerge(path_geometries)
            full_line_wgs84 = gpd.GeoSeries(
                [full_line_proj],
                crs="EPSG:2154"
            ).to_crs(epsg=4326).iloc[0]

            if full_line_wgs84.geom_type == 'MultiLineString':
                coords_list = [list(g.coords) for g in full_line_wgs84.geoms]
                coords_list = [item for sublist in coords_list for item in sublist]
            else:
                coords_list = list(full_line_wgs84.coords)

            dist_km = total_dist / 1000.0
            if dist_km > 250:
                continue

            final_output[ville_nom]["adjacents"].append({
                "nom": voisin_nom,
                "distance_km": round(dist_km, 3),
                "vitesse_moyenne_kmh": round(
                    (dist_km / (total_time / 3600)), 1
                ) if total_time > 0 else 0,
                "path_geometry": coords_list
            })

            stats_success += 1

        except:
            stats_fail += 1

print(f"Terminé. Succès : {stats_success}, Echecs : {stats_fail}")

with open(PATH_OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(final_output, f, ensure_ascii=False, indent=4)
