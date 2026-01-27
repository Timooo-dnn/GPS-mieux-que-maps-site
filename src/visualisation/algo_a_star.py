def trouver_chemins(depart, arrivee):
    chemins = [
        {
            "id": 1,
            "villes": [depart, "Auxerre", arrivee],
            "km": 460,
            "minutes": 260,
            "autoroute": True
        },
        {
            "id": 2,
            "villes": [depart, "Nevers", "Roanne", arrivee],
            "km": 480,
            "minutes": 320,
            "autoroute": False
        },
        {
            "id": 3,
            "villes": [depart, "Dijon", arrivee],
            "km": 500,
            "minutes": 280,
            "autoroute": True
        }
    ]
    
    return chemins