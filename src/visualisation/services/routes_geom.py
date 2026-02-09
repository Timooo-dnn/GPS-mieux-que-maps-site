import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DB_FILE = BASE_DIR / "src" / "data" / "sqlite" / "routes.db"

def extraire_infos_itineraire(liste_villes):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    print("DB_FILE =", DB_FILE)

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables présentes :", cur.fetchall())

    villes = {}
    routes = []

    # ---------- VILLES ----------
    placeholders = ",".join("?" for _ in liste_villes)
    cur.execute(
        f"""
        SELECT id, nom, lat, lon
        FROM villes
        WHERE id IN ({placeholders})
        """,
        liste_villes
    )

    for vid, nom, lat, lon in cur.fetchall():
        villes[vid] = {
            "nom": nom,
            "lat": lat,
            "lon": lon
        }

    # ---------- ROUTES (ordre du chemin) ----------
    for i in range(len(liste_villes) - 1):
        v_from = liste_villes[i]
        v_to = liste_villes[i + 1]

        cur.execute(
            """
            SELECT autoroute, geometry
            FROM routes
            WHERE from_id = ? AND to_id = ?
            """,
            (v_from, v_to)
        )

        row = cur.fetchone()
        if row:
            autoroute, geom_json = row
            # Convertir la liste de coordonnées en GeoJSON LineString
            try:
                # Si c'est une chaîne JSON, la parser
                if isinstance(geom_json, str):
                    coordinates = json.loads(geom_json)
                else:
                    coordinates = geom_json
                
                # Créer un GeoJSON LineString valide
                geometry = {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Erreur parsing geometry pour {v_from}->{v_to}: {e}")
                geometry = None
            
            if geometry:
                routes.append({
                    "from": v_from,
                    "to": v_to,
                    "autoroute": bool(autoroute),
                    "geometry": geometry
                })

    conn.close()

    return {
        "villes": villes,
        "routes": routes
    }
