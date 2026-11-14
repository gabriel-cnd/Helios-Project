"""
1. Importer yaml
2. Importer json
3. créer la fonction load_config
4. lire config.yaml
5. Retourner le contenu (dictionnaire)
6. créer la fonction load_metadata
7. lire metadata.json
8. Retourner le contenu (dictionnaire)
"""

import yaml
import json
import os  # pour gérer les chemins de fichiers
from functools import lru_cache


@lru_cache(maxsize=1)
def load_config():
    "Load ans return the configuration from config.yaml"
    base_dir = os.path.dirname(__file__)  # répertoire actuel
    path = os.path.join(base_dir, "config.yaml")  # chemin complet vers config.yaml
    with open(path, "r") as f:
        config = yaml.safe_load(f)  # lire le fichier YAML
    return config


def load_metadata():
    "Load project metadata from metadata.json"
    base_dir = os.path.dirname(__file__)  # répertoire actuel
    path = os.path.join(base_dir, "metadata.json")  # chemin complet vers metadata
    with open(path, "r") as f:
        metadata = json.load(f)  # lire le fichier JSON
    return metadata


def get_meteo_settings():
    "Retourne la configuration MeteoSwiss (ou un dict vide)."
    config = load_config()
    meteo = config.get("meteo") or {}
    return meteo.get("meteoswiss", {})


if __name__ == "__main__":
    "Test load_config and load_metadata fucntions"
    config = load_config()
    metadata = load_metadata()

    print("CONFIG:", config)
    print("METADATA:", metadata)
