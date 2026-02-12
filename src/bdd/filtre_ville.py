import geopandas as gpd

path_source = r"C:\projet_GPS\src\data\gis_osm_places_free_1.shp"

print("Chargement des données...")
gdf = gpd.read_file(path_source)

filtre_categories = ['city', 'town', 'village']
villes_filtres = gdf[gdf['fclass'].isin(filtre_categories)].copy()

villes_filtres['unique_name'] = villes_filtres['name'].astype(str) + "_" + villes_filtres['osm_id'].astype(str)

path_dest = r"C:\projet_GPS\src\data\places_filtres.shp"
villes_filtres.to_file(path_dest)

print(f"Lieux restants : {len(villes_filtres)}")
print(f"Lien du fichier : {path_dest}")