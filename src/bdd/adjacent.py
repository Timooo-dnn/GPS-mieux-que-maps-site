import geopandas as gpd
import json
from libpysal.weights import Voronoi

path = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\places_filtres.shp"
gdf = gpd.read_file(path)

if 'unique_nm' in gdf.columns:
    gdf['unique_name'] = gdf['unique_nm']
else:
    gdf['unique_name'] = gdf['name'].astype(str) + "_" + gdf['osm_id'].astype(str)

# Calcul des adjacent par Voronoi
weights = Voronoi.from_dataframe(gdf)

adjacences_dictionnire = {}

for i, row in gdf.iterrows():
    # Nom unique créé dans filtre_ville
    id_ville = row['unique_name']
    
    indices_voisins = weights.neighbors[i]
    
    # Récupération des noms unique des villes adjacentes
    noms_voisins = gdf.iloc[indices_voisins]['unique_name'].tolist()
    
    adjacences_dictionnire[id_ville] = noms_voisins

output_path = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\adjacences_villes.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(adjacences_dictionnire, f, ensure_ascii=False, indent=4)

print(f"Fichier JSON d'adjacences (IDs uniques) créé : {output_path}")