import json
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # src/
PATH_LOCALISATION = os.path.join(CURRENT_DIR, "visualisation", "coords_villes.json")

with open(PATH_LOCALISATION, encoding="utf-8") as f:
    localisation_ville = json.load(f)
