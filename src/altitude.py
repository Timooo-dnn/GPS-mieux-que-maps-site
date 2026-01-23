import rasterio
import os
from glob import glob
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import geopandas as gpd
from matplotlib.lines import Line2D

# --- CONFIGURATION ---
# Chemin vers le dossier contenant vos fichiers .asc et le .shp des départements
PATH_DATA = r"C:\Users\Gwénaël\OneDrive\Bureau\ENAC\Programmation\projet_GPS\src\data\dales_alt"
PATH_INDEX_JSON = "index_bd_alti.json"
# Nom précis de votre fichier de frontières
PATH_BORDERS = os.path.join(PATH_DATA, "departements-20180101.shp")

def create_spatial_index(folder_path):
    """Scanne le dossier pour répertorier les dalles et leurs coordonnées."""
    print(f"Analyse des fichiers .asc dans : {folder_path}...")
    files = glob(os.path.join(folder_path, "*.asc"))
    
    if not files:
        print("Erreur : Aucun fichier .asc trouvé dans le dossier.")
        return {}

    spatial_index = {}
    for file_path in files:
        file_name = os.path.basename(file_path)
        try:
            with rasterio.open(file_path) as src:
                b = src.bounds
                spatial_index[file_name] = {
                    "full_path": file_path,
                    "xmin": b.left,
                    "xmax": b.right,
                    "ymin": b.bottom,
                    "ymax": b.top,
                    "resolution": src.res[0]
                }
        except Exception as e:
            print(f"Erreur lors de la lecture de {file_name} : {e}")

    print(f"Indexation terminée. {len(spatial_index)} dalles répertoriées.")
    return spatial_index

def plot_coverage_with_borders(index_alti, borders_path):
    """Affiche les dalles indexées et les frontières des départements ciblés."""
    if not index_alti:
        print("L'index est vide, impossible d'afficher la carte.")
        return

    print("Préparation de la visualisation...")
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 1. DESSIN DES DALLES (Rectangles bleus)
    for name, info in index_alti.items():
        rect = patches.Rectangle(
            (info['xmin'], info['ymin']), 
            info['xmax'] - info['xmin'], 
            info['ymax'] - info['ymin'], 
            linewidth=0.5, edgecolor='blue', facecolor='skyblue', alpha=0.4
        )
        ax.add_patch(rect)
    
    # 2. DESSIN DES FRONTIÈRES FILTRÉES (Lignes rouges)
    if os.path.exists(borders_path):
        print("Chargement et filtrage des frontières (Midi-Pyrénées)...")
        gdf = gpd.read_file(borders_path)
        
        # Codes INSEE des 8 départements des Midi-Pyrénées
        midi_pyrenees = ['09', '12', '31', '32', '46', '65', '81', '82']
        
        # Recherche de la colonne de code (selon la source du fichier)
        col_code = None
        for col in ['code_insee', 'dep', 'code', 'insee_dep']:
            if col in gdf.columns:
                col_code = col
                break
        
        if col_code:
            gdf = gdf[gdf[col_code].isin(midi_pyrenees)]
            
            # Reprojection en Lambert 93 pour correspondre aux dalles
            if gdf.crs != "EPSG:2154":
                gdf = gdf.to_crs(epsg=2154)
            
            gdf.plot(ax=ax, edgecolor='red', facecolor='none', linewidth=1.5)
            
            # ZOOM sur la zone des départements (+ 20km de marge)
            minx, miny, maxx, maxy = gdf.total_bounds
            ax.set_xlim(minx - 20000, maxx + 20000)
            ax.set_ylim(miny - 20000, maxy + 20000)
        else:
            print("Erreur : Impossible de trouver la colonne des codes départements dans le .shp")
            print(f"Colonnes disponibles : {gdf.columns.tolist()}")
    else:
        print(f"Attention : Fichier frontières non trouvé à : {borders_path}")

    # Mise en forme finale
    ax.set_aspect('equal')
    plt.title(f"Couverture BD ALTI ({len(index_alti)} dalles) - Focus Midi-Pyrénées")
    plt.xlabel("Lambert 93 X (m)")
    plt.ylabel("Lambert 93 Y (m)")
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Légende manuelle
    custom_lines = [patches.Patch(facecolor='skyblue', edgecolor='blue', alpha=0.4),
                    Line2D([0], [0], color='red', lw=1.5)]
    ax.legend(custom_lines, ['Dalles BD ALTI détectées', 'Frontières Midi-Pyrénées'])

    print("Affichage de la carte...")
    plt.show()

# --- LOGIQUE DE LANCEMENT ---

# 1. Gestion de l'index (On ne le crée que s'il n'existe pas)
if os.path.exists(PATH_INDEX_JSON):
    print("Chargement de l'index existant...")
    with open(PATH_INDEX_JSON, "r", encoding="utf-8") as f:
        index_alti = json.load(f)
else:
    index_alti = create_spatial_index(PATH_DATA)
    if index_alti:
        with open(PATH_INDEX_JSON, "w", encoding="utf-8") as f:
            json.dump(index_alti, f, indent=4)
        print(f"Index sauvegardé dans {PATH_INDEX_JSON}")

# 2. Lancement de la carte
plot_coverage_with_borders(index_alti, PATH_BORDERS)