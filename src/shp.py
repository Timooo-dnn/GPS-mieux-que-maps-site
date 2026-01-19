import geopandas as gpd
from geopandas import sjoin

# fichiers
cities_file = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\gis_osm_places_free_1.shp"
roads_file  = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\gis_osm_roads_free_1.shp"

# lire les shapefiles
cities = gpd.read_file(cities_file)
roads  = gpd.read_file(roads_file)

# filtrer pour simplifier
cities = cities[cities['fclass'].isin(['city', 'town'])]
roads  = roads[roads['fclass'].isin(['motorway', 'primary', 'secondary', 'tertiary'])]

cities['buffer'] = cities.geometry.buffer(0.01)

roads_with_cities = sjoin(roads, cities[['name', 'buffer']], how='inner', predicate='intersects')

print(roads_with_cities[['name', 'fclass', 'geometry']].head())