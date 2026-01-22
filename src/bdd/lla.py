import geopandas as gpd
import json

path_source = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\places_filtres.shp"
gdf = gpd.read_file(path_source)

coords_dictionnaire = {}

for _, row in gdf.iterrows():
    id_ville = row['unique_nm'] if 'unique_nm' in row else f"{row['name']}_{row['osm_id']}"
    
    coords_dictionnaire[id_ville] = {
        "nom_affichage": row['name'],
        "lat": row['geometry'].y,
        "lon": row['geometry'].x
    }

output_path = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\coords_villes.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(coords_dictionnaire, f, ensure_ascii=False, indent=4)

print(f"Fichier des coordonnées (IDs uniques) créé : {output_path}")
print(f"Nombre de villes enregistrées : {len(coords_dictionnaire)}")