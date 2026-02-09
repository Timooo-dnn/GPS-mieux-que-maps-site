import sqlite3
import json

DB_FILE = r"src\data\sqlite\routes.db"

def audit_database(limit_routes=10):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    print("\n=== AUDIT SQLITE ROUTES.DB ===\n")

    # ---------- VILLES ----------
    cur.execute("SELECT COUNT(*) FROM villes")
    nb_villes = cur.fetchone()[0]
    print(f"Nombre de villes : {nb_villes}")

    cur.execute("SELECT id, nom FROM villes LIMIT 5")
    print("Exemples de villes :")
    for v in cur.fetchall():
        print("  ", v)

    # ---------- ROUTES ----------
    cur.execute("SELECT COUNT(*) FROM routes")
    nb_routes = cur.fetchone()[0]
    print(f"\nNombre de routes : {nb_routes}")

    cur.execute("""
        SELECT from_id, to_id,
               distance_km, temps_min, vitesse_moy, autoroute,
               geometry
        FROM routes
        LIMIT ?
    """, (limit_routes,))

    rows = cur.fetchall()

    print(f"\n--- Analyse des {len(rows)} premières routes ---")
    for r in rows:
        from_id, to_id, dist, temps, vit, auto, geom = r

        print(f"\nRoute {from_id} -> {to_id}")
        print(f"  distance : {dist} km | temps : {temps} min | vitesse : {vit} km/h | autoroute : {bool(auto)}")

        if not geom:
            print("  ❌ Géométrie absente")
            continue

        try:
            geometry = json.loads(geom)
        except Exception as e:
            print("  ❌ JSON invalide :", e)
            continue

        if not isinstance(geometry, list) or len(geometry) < 2:
            print("  ❌ Géométrie invalide (moins de 2 points)")
            continue

        print(f"  ✔ Nb points : {len(geometry)}")
        print(f"  Premier point : {geometry[0]}")
        print(f"  Dernier point  : {geometry[-1]}")

        # vérification cohérence distance
        if dist <= 0 or temps <= 0:
            print("  ⚠️ Distance ou temps invalide")

    # ---------- ROUTES ORPHELINES ----------
    print("\n--- Recherche routes orphelines (ville absente) ---")
    cur.execute("""
        SELECT r.from_id, r.to_id
        FROM routes r
        LEFT JOIN villes v1 ON r.from_id = v1.id
        LEFT JOIN villes v2 ON r.to_id   = v2.id
        WHERE v1.id IS NULL OR v2.id IS NULL
        LIMIT 10
    """)
    orphelines = cur.fetchall()

    if not orphelines:
        print("✔ Aucune route orpheline")
    else:
        for o in orphelines:
            print("❌ Route orpheline :", o)

    # ---------- ROUTES NON BIDIRECTIONNELLES ----------
    print("\n--- Routes sans retour inverse ---")
    cur.execute("""
        SELECT r1.from_id, r1.to_id
        FROM routes r1
        LEFT JOIN routes r2
          ON r1.from_id = r2.to_id
         AND r1.to_id   = r2.from_id
        WHERE r2.id IS NULL
        LIMIT 10
    """)
    sens_unique = cur.fetchall()

    if not sens_unique:
        print("✔ Toutes les routes sont bidirectionnelles")
    else:
        for s in sens_unique:
            print("⚠️ Sens unique :", s[0], "->", s[1])

    conn.close()
    print("\n=== FIN AUDIT ===\n")

if __name__ == "__main__":
    audit_database(limit_routes=5)