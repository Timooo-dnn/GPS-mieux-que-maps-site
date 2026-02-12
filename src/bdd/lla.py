import geopandas as gpd
import json

path_source = r"C:\projet_GPS\src\data\places_filtres.shp"
gdf = gpd.read_file(path_source)

coords_dictionnaire = {}

for _, ligne in gdf.iterrows():
    id_ville = ligne['unique_nm'] if 'unique_nm' in ligne else f"{ligne['name']}_{ligne['osm_id']}"
    
    coords_dictionnaire[id_ville] = {
        "nom_affichage": ligne['name'],
        "lat": ligne['geometry'].y,
        "lon": ligne['geometry'].x
    }

output_path = r"C:\projet_GPS\src\data\coords_villes.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(coords_dictionnaire, f, ensure_ascii=False, indent=4)

print(f"Fichier des coordonnées (IDs uniques) créé : {output_path}")
print(f"Nombre de villes enregistrées : {len(coords_dictionnaire)}")