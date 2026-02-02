import json
localisation_ville_test = {"Toulouse":[43.6044638, 1.4442433],
 "Blagnac": [43.6343476, 1.3986403],
 "Colomiers": [43.6112476, 1.3367443],
 "Tournefeuille": [0.5832062, 1.3160025],
 "Aussonne":[43.6343470, 1.3986400]}

with open(r"src\data\localisation_villes.json",encoding="utf-8") as f:
    localisation_ville = json.load(f)
