import geopandas as gpd
import json
from libpysal.weights import Voronoi
from shapely.geometry import Point
from scipy.spatial import cKDTree
import numpy as np
from tqdm import tqdm

path = r"src\data\places_filtres.shp"
roads_path = r"src\data\gis_osm_roads_free_1.shp"

gdf = gpd.read_file(path)
gdf_roads = gpd.read_file(roads_path)

if 'unique_nm' in gdf.columns:
    gdf['unique_name'] = gdf['unique_nm']
else:
    gdf['unique_name'] = gdf['name'].astype(str) + "_" + gdf['osm_id'].astype(str)

# ============= ROUTES MAJEURES =============
# Classification des routes par importance
ROUTES_MAJEURES = ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"]
ROUTES_SECONDAIRES = ["secondary", "secondary_link", "tertiary", "tertiary_link"]

# Filtrer et reprojeter les routes majeures
gdf_roads_proj = gdf_roads.to_crs(epsg=2154)
gdf_villes_proj = gdf.to_crs(epsg=2154)

# Routes majeures (autoroutes, nationales)
gdf_majeures = gdf_roads_proj[gdf_roads_proj['fclass'].isin(ROUTES_MAJEURES)].copy()

# Explode pour avoir des segments simples
gdf_majeures_exploded = gdf_majeures.explode(index_parts=False).reset_index(drop=True)

print(f"Routes majeures trouvées: {len(gdf_majeures_exploded)} segments")
print(f"Villes à traiter: {len(gdf_villes_proj)}")

# ============= ADJACENCE PAR ROUTES MAJEURES =============
# Pour chaque route majeure, identifier les villes qu'elle traverse/approche

def villes_sur_route(route_geom, villes_gdf, buffer_m=1500):
    """Trouve les villes à proximité d'une route"""
    route_buffer = route_geom.buffer(buffer_m)
    villes_proches = villes_gdf[villes_gdf.geometry.intersects(route_buffer)]
    return villes_proches.index.tolist()

# Dictionnaire d'adjacence avec hiérarchie
adjacences_routes = {}
adjacences_voronoi = {}

# Calcul Voronoi pour adjacence locale (fallback)
print("Calcul des adjacences locales (Voronoi)...")
weights = Voronoi.from_dataframe(gdf_villes_proj)

for i, row in gdf_villes_proj.iterrows():
    id_ville = row['unique_name']
    indices_voisins = weights.neighbors[i]
    noms_voisins = gdf_villes_proj.iloc[indices_voisins]['unique_name'].tolist()
    adjacences_voronoi[id_ville] = noms_voisins

# Adjacence par routes majeures
print("Extraction des adjacences par routes majeures...")
for idx, route_row in tqdm(gdf_majeures_exploded.iterrows(), total=len(gdf_majeures_exploded), desc="Routes"):
    route_geom = route_row.geometry
    villes_route = villes_sur_route(route_geom, gdf_villes_proj, buffer_m=1500)
    
    # Si au moins 2 villes sur cette route, les ajouter comme adjacentes
    if len(villes_route) >= 2:
        for ville_idx in villes_route:
            id_ville = gdf_villes_proj.iloc[ville_idx]['unique_name']
            
            # Ajouter les autres villes de cette route comme adjacentes
            villes_adjacentes = [gdf_villes_proj.iloc[v]['unique_name'] for v in villes_route if v != ville_idx]
            
            if id_ville not in adjacences_routes:
                adjacences_routes[id_ville] = set()
            
            adjacences_routes[id_ville].update(villes_adjacentes)

# ============= FUSION DES DEUX APPROCHES =============
# Combiner adjacence par routes (priorité haute) + Voronoi (fallback local)

adjacences_finale = {}

for i, row in tqdm(gdf_villes_proj.iterrows(), total=len(gdf_villes_proj), desc="Fusion"):
    id_ville = row['unique_name']
    
    # Commencer par adjacences par routes
    adjacents = set(adjacences_routes.get(id_ville, []))
    
    # Ajouter adjacences Voronoi (si pas déjà présentes)
    adjacents.update(adjacences_voronoi.get(id_ville, []))
    
    # Garder au maximum les 15 plus proches pour éviter un graphe trop dense
    if len(adjacents) > 15:
        # Calculer les distances aux adjacents et garder les plus proches
        point_ville = row.geometry
        distances = []
        for adj_ville in adjacents:
            idx_adj = gdf_villes_proj[gdf_villes_proj['unique_name'] == adj_ville].index[0]
            dist = point_ville.distance(gdf_villes_proj.iloc[idx_adj].geometry)
            distances.append((adj_ville, dist))
        
        # Trier par distance et garder les 15 plus proches
        distances.sort(key=lambda x: x[1])
        adjacents = {d[0] for d in distances[:15]}
    
    adjacences_finale[id_ville] = sorted(list(adjacents))

# Statistiques
print(f"\n=== STATISTIQUES ===")
print(f"Villes avec adjacences par routes: {len(adjacences_routes)}")
print(f"Adjacences moyennes par route: {sum(len(v) for v in adjacences_routes.values()) / max(1, len(adjacences_routes)):.1f}")
print(f"Adjacences moyennes finales: {sum(len(v) for v in adjacences_finale.values()) / len(adjacences_finale):.1f}")

# Sauvegarde
output_path = r"src\data\adjacences_villes.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(adjacences_finale, f, ensure_ascii=False, indent=4)

print(f"\nFichier JSON d'adjacences créé : {output_path}")
print(f"Total villes: {len(adjacences_finale)}")