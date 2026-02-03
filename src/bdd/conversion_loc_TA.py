import json

with open(r"src\data\routes_villes_adj.json", encoding="utf-8") as f:
    data = json.load(f)

CHEMIN_SORTIE = r"src\data\localisation_villes.json"

villes = {}

for ville_id, infos in data.items():
    nom = ville_id
    lat = infos["coords"]["lat"]
    lon = infos["coords"]["lon"]

    villes[nom] = [
        lat,
        lon
    ]

with open(CHEMIN_SORTIE, "w", encoding="utf-8") as f:
        json.dump(villes, f, ensure_ascii=False, indent=4)