from pathlib import Path
import sqlite3
import json

CURRENT_DIR = Path(__file__).parent  # src/visualisation/services
DB_FILE = CURRENT_DIR.parent / "ma_base.db"  # remonte à src/visualisation
print("DB_FILE =", DB_FILE)

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
        reverse_direction = False
        
        if not row:
            cur.execute(
                """
                SELECT autoroute, geometry
                FROM routes
                WHERE from_id = ? AND to_id = ?
                """,
                (v_to, v_from)
            )
            row = cur.fetchone()
            reverse_direction = True
        
        if row:
            autoroute, geom_json = row
            try:
                # Si c'est une chaîne JSON, la parser
                if isinstance(geom_json, str):
                    coordinates = json.loads(geom_json)
                else:
                    coordinates = geom_json
                
                if reverse_direction:
                    coordinates = coordinates[::-1]
                
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
                    "geometry": geometry,
                    "reverse": reverse_direction
                })

    conn.close()

    return {
        "villes": villes,
        "routes": routes
    }
