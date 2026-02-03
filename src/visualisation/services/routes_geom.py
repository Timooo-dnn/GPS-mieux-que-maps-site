import sqlite3
import json

DB_FILE = r"src\data\sqlite\routes.db"


def extraire_infos_itineraire(liste_villes):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

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
            routes.append({
                "from": v_from,
                "to": v_to,
                "autoroute": bool(autoroute),
                "geometry": json.loads(geom_json)
            })

    conn.close()

    return {
        "villes": villes,
        "routes": routes
    }
