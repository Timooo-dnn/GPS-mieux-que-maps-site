import json
import os

# --- CHEMIN ABSOLU ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))   # src/
PATH_DICO_FINAL = os.path.join(CURRENT_DIR, "visualisation", "dico_final.json")

with open(PATH_DICO_FINAL, encoding="utf-8") as f:
    maping = json.load(f)