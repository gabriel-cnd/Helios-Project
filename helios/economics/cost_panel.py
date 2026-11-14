#!/usr/bin/env python3
# ==============================================================================
# SCRIPT D'ANALYSE ET SÉLECTION DE PANNEAUX PHOTOVOLTAÏQUES
# ==============================================================================
#
# Ce script aide à choisir le meilleur panneau solaire en fonction de :
# - La surface disponible sur votre toit (en m²)
# - La puissance électrique souhaitée (en Watts)
# - Le budget (prix en CHF)
#
# Usage :
#   python cost_panel.py --html index.html --csv "panneaux.csv"
#   python cost_panel.py --surface 25 --power 5000 --csv "panneaux.csv"
#
# ==============================================================================

import re  # Pour rechercher des motifs dans du texte (ex: "150 W")
import math  # Pour les calculs mathématiques (arrondir vers le haut, etc.)
import sys  # Pour interagir avec le système (quitter le programme, etc.)
import argparse  # Pour lire les arguments de la ligne de commande
from pathlib import Path  # Pour manipuler les chemins de fichiers facilement
from typing import Dict, Optional  # Pour les annotations de type
import pandas as pd  # Pour lire et manipuler les fichiers CSV (tableaux)
from bs4 import BeautifulSoup  # Pour analyser les fichiers HTML

# ==============================================================================
# VÉRIFICATION DES DÉPENDANCES
# ==============================================================================
# On vérifie que les bibliothèques nécessaires sont installées
try:
    # Si cette ligne s'exécute, les imports ci-dessus ont fonctionné
    pass
except Exception as e:
    # Si une erreur survient, on affiche un message et on quitte
    sys.exit(
        "Dépendances manquantes. Installez pandas et beautifulsoup4. Erreur: " + str(e)
    )


# ==============================================================================
# CLASSE : PANNEAU PHOTOVOLTAÏQUE
# ==============================================================================
class Panel:
    """
    Représente un panneau photovoltaïque avec ses caractéristiques principales.

    Attributs:
        id : identifiant unique du panneau (nom, modèle)
        power_w : puissance nominale en Watts
        area_m2 : surface en m²
        cost_per_m2 : coût par m² (prix unitaire / surface)
    """

    def __init__(self, id: str, power_w: float, area_m2: float, cost_per_m2: float):
        self.id = id
        self.power_w = power_w
        self.area_m2 = area_m2
        self.cost_per_m2 = cost_per_m2


class CostPanel:
    """Load panel data and compare installation options."""

    @staticmethod
    def load_panels(csv_path: str) -> Dict[str, Panel]:
        """Load a panel comparison CSV into a dictionary keyed by model name."""
        dataframe = pd.read_csv(csv_path)
        columns = detect_columns(dataframe)

        name_column = columns.get("model")
        power_column = columns.get("power")
        price_column = columns.get("price")
        area_columns = columns.get("area_candidate", [])
        area_column = area_columns[0] if area_columns else None

        if power_column is None or price_column is None or area_column is None:
            raise ValueError("Le fichier CSV ne contient pas les colonnes requises.")

        panels: Dict[str, Panel] = {}
        for index, row in dataframe.iterrows():
            name = str(row[name_column]) if name_column else f"panel_{index}"
            power = try_cast_float(row[power_column])
            area = try_cast_float(row[area_column])
            price = try_cast_float(row[price_column])
            if power is None or area is None or price is None:
                continue
            panels[name] = Panel(name, power, area, price)

        return panels

    @staticmethod
    def surface_needed(
        installed_power_kw: float,
        panel_power_w: Optional[float] = None,
        panel_area_m2: Optional[float] = None,
        panels: Optional[Dict[str, Panel]] = None,
        panel_name: Optional[str] = None,
        margin: float = 0.0,
    ) -> Dict[str, float]:
        """Calculate the number of panels and total surface required."""
        if panel_name is not None:
            if panels is None or panel_name not in panels:
                raise ValueError("Le panneau demandé est absent du catalogue.")
            panel = panels[panel_name]
            panel_power_w = panel.power_w
            panel_area_m2 = panel.area_m2

        if panel_power_w is None or panel_power_w <= 0:
            raise ValueError("La puissance du panneau doit être supérieure à zéro.")
        if panel_area_m2 is None or panel_area_m2 <= 0:
            raise ValueError("La surface du panneau doit être supérieure à zéro.")

        target_power_w = float(installed_power_kw) * 1000 * (1 + float(margin))
        required_panels = math.ceil(target_power_w / panel_power_w)
        return {
            "required_panels": required_panels,
            "total_area_m2": required_panels * panel_area_m2,
            "provided_power_w": required_panels * panel_power_w,
        }

    @staticmethod
    def find_best_panel(
        installed_power_kw: float,
        panels: Dict[str, Panel],
        margin: float = 0.0,
    ) -> Dict[str, object]:
        """Return the panel offering the highest nominal power per unit cost."""
        valid_panels = {
            name: panel
            for name, panel in panels.items()
            if panel.power_w > 0 and panel.cost_per_m2 > 0 and panel.area_m2 > 0
        }
        if not valid_panels:
            raise ValueError("Aucun panneau valide n'est disponible.")

        name, panel = max(
            valid_panels.items(),
            key=lambda item: item[1].power_w / item[1].cost_per_m2,
        )
        sizing = CostPanel.surface_needed(
            installed_power_kw=installed_power_kw,
            panel_power_w=panel.power_w,
            panel_area_m2=panel.area_m2,
            margin=margin,
        )
        return {"best_panel": name, **sizing}


# ==============================================================================
# TAUX DE CHANGE VERS FRANCS SUISSES (CHF)
# ==============================================================================
# Dictionnaire contenant les taux de conversion approximatifs
# Par exemple : 1 EUR = 1.07 CHF
EXCHANGE_TO_CHF = {
    "CHF": 1.0,  # Franc suisse (déjà en CHF, pas de conversion)
    "EUR": 1.07,  # Euro
    "€": 1.07,  # Symbole Euro
    "EUR€": 1.07,  # Variante avec symbole
    "USD": 0.93,  # Dollar américain
    "$": 0.93,  # Symbole Dollar
}


# ==============================================================================
# FONCTION : EXTRAIRE UN NOMBRE AVEC SON UNITÉ
# ==============================================================================
def find_input_by_keywords(soup, keywords):
    """
    Cherche une valeur dans les balises HTML qui contiennent
    certains mots-clés (ex: 'surface', 'power')
    """
    # On parcourt toutes les balises susceptibles de contenir des données
    for inp in soup.find_all(["input", "span", "div", "p", "label"]):
        # On récupère les attributs de la balise (id, name, class)
        attrs = " ".join([str(inp.get(k, "")) for k in ("id", "name", "class")])
        # On combine le texte et les attributs pour la recherche
        text = (inp.get("value") or inp.text or "") + " " + attrs

        # Si un des mots-clés est trouvé dans ce texte
        if any(k.lower() in text.lower() for k in keywords):
            # On essaie d'extraire un nombre avec son unité
            val, unit = parse_number_with_unit(text)
            if val is not None:
                return val, unit

    return None, None


def parse_index_html(html_path):
    """
    Extrait les paramètres (surface, puissance) depuis un fichier HTML.
    """
    result = {}

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            txt = f.read()
    except Exception:
        return result

    soup = BeautifulSoup(txt, "html.parser")

    # --- RECHERCHE DE LA SURFACE ---
    # Mots-clés français et anglais pour "surface"
    surf_val, surf_unit = find_input_by_keywords(
        soup, ["surface", "area", "superficie"]
    )

    # Si on n'a rien trouvé dans les balises, on cherche dans tout le texte
    if surf_val is None:
        surf_val, surf_unit = parse_number_with_unit(txt)

    # --- RECHERCHE DE LA PUISSANCE ---
    power_val, power_unit = find_input_by_keywords(soup, ["puissance", "power", "kW"])

    # Si on n'a rien trouvé dans les balises
    if power_val is None:
        # On cherche "puissance" ou "power" suivi d'un nombre + W/kW
        # Ex: "Puissance souhaitée : 5 kW"
        m = re.search(
            r"(puissance|power).{0,40}?([\d\.,]+\s*(?:kW|W))",
            txt,
            flags=re.IGNORECASE,
        )
        if m:
            power_val, power_unit = parse_number_with_unit(m.group(2))
        else:
            # Solution de secours : le premier nombre suivi de W ou kW dans le document
            p = re.search(r"([\d\.,]+)\s*(kW|W)\b", txt, flags=re.IGNORECASE)
            if p:
                power_val, power_unit = parse_number_with_unit(p.group(0))

    # --- STOCKAGE DES RÉSULTATS ---
    # Si on a trouvé une surface en m²
    if surf_val is not None and surf_unit in ("m2",):
        result["surface_m2"] = float(surf_val)
    # Si on a trouvé une valeur en mètres simples, on la traite comme des m²
    elif surf_val is not None and surf_unit == "m":
        result["surface_m2"] = float(surf_val)

    # Si on a trouvé une puissance en Watts
    if power_val is not None and power_unit == "W":
        result["required_power_w"] = float(power_val)

    return result


def parse_number_with_unit(text):
    """
    Cherche et extrait un nombre suivi d'une unité dans un texte.

    Exemples de textes acceptés :
    - "25 m2" ou "25 m²" → retourne (25.0, 'm2')
    - "3.5 kW" → retourne (3500.0, 'W')  [converti en Watts]
    - "250 W" → retourne (250.0, 'W')

    Arguments :
        text : le texte à analyser (ex: "Surface: 25 m2")

    Retourne :
        tuple (valeur, unité) ou (None, None) si rien n'est trouvé
    """
    # Si le texte est vide, on ne peut rien extraire
    if not text:
        return None, None

    # On remplace les virgules par des points pour les nombres décimaux
    # (ex: "25,5" devient "25.5")
    text = text.replace(",", ".")


# ==============================================================================
# FONCTION : CONVERTIR UNE VALEUR EN NOMBRE DÉCIMAL
# ==============================================================================
def try_cast_float(x):
    """
    Tente de convertir n'importe quelle valeur en nombre décimal (float).

    Gère les cas suivants :
    - Nombres déjà en format numérique
    - Texte avec des espaces ou caractères spéciaux ("150,50 CHF")
    - Valeurs vides ou NaN (Not a Number)

    Arguments :
        x : la valeur à convertir (peut être str, int, float, etc.)

    Retourne :
        Un nombre décimal (float) ou None si la conversion échoue
    """
    # Si la valeur est vide ou NaN (valeur manquante dans un CSV)
    if pd.isna(x):
        return None

    # Si c'est déjà un nombre, on le convertit juste en float
    if isinstance(x, (int, float)):
        return float(x)

    # Conversion en texte et nettoyage
    s = str(x).strip()
    if s == "":
        return None

    # Nettoyage du texte :
    # - Suppression des espaces insécables (\xa0)
    # - Suppression des espaces normaux
    # - Remplacement des virgules par des points (notation décimale)
    s = s.replace("\xa0", " ").replace(" ", "").replace(",", ".")

    # Suppression de tous les caractères non numériques (symboles de devises, etc.)
    # Ne garde que les chiffres, points et signes moins
    s = re.sub(r"[^\d\.\-]", "", s)

    # Tentative de conversion
    try:
        return float(s)
    except (TypeError, ValueError):
        # Si ça échoue, on retourne None
        return None


# ==============================================================================
# FONCTION : DÉTECTER LES COLONNES PERTINENTES DU CSV
# ==============================================================================
def detect_columns(df):
    """
    Identifie automatiquement les colonnes importantes dans le fichier CSV.

    Cherche les colonnes contenant des informations sur :
    - Le modèle du panneau (nom, marque)
    - La puissance (W, kW)
    - Le prix (CHF, EUR, etc.)
    - La surface ou dimensions (m², dimensions)

    Arguments :
        df : DataFrame pandas contenant les données du CSV

    Retourne :
        Dictionnaire indiquant quelle colonne contient quelle information
        Ex: {'model': 'Modèle', 'power': 'Puissance (W)', 'price': 'Prix (CHF)'}
    """
    # Dictionnaire qui contiendra les résultats
    lookup = {}

    # --- RECHERCHE DE LA COLONNE "MODÈLE" ---
    # Liste de mots-clés possibles pour identifier la colonne du modèle
    for keyword in ("model", "modèle", "mod", "name", "nom", "marque", "type"):
        for c in df.columns:
            # Si le mot-clé apparaît dans le nom de la colonne
            if keyword in str(c).lower():
                lookup["model"] = c
                break
        # Si on a trouvé, on arrête de chercher
        if "model" in lookup:
            break

    # --- RECHERCHE DE LA COLONNE "PUISSANCE" ---
    for keyword in ("power", "w", "puissance", "pmax", "watts"):
        for c in df.columns:
            if keyword in str(c).lower():
                lookup["power"] = c
                break
        if "power" in lookup:
            break

    # --- RECHERCHE DE LA COLONNE "PRIX" ---
    for keyword in ("price", "prix", "chf", "franc", "€", "eur", "cost"):
        for c in df.columns:
            if keyword in str(c).lower():
                lookup["price"] = c
                break
        if "price" in lookup:
            break

    # --- RECHERCHE DES COLONNES "SURFACE/DIMENSIONS" ---
    # Peut y avoir plusieurs colonnes candidates (surface, largeur, hauteur, etc.)
    for keyword in (
        "area",
        "surface",
        "m2",
        "m²",
        "dimensions",
        "size",
        "dimension",
        "width",
        "height",
        "longueur",
    ):
        for c in df.columns:
            if keyword in str(c).lower():
                # On stocke toutes les colonnes candidates dans une liste
                lookup.setdefault("area_candidate", []).append(c)

    return lookup


# ==============================================================================
# FONCTION : CONVERTIR DES DIMENSIONS EN SURFACE
# ==============================================================================
def parse_dimensions_to_m2(s):
    """
    Convertit des dimensions textuelles en surface (m²).

    Exemples de formats acceptés :
    - "1650 x 992 mm" → calcule la surface en m²
    - "1.65 x 0.992 m" → calcule la surface en m²
    - "1650x992" → devine l'unité selon les valeurs

    Arguments :
        s : texte contenant les dimensions (ex: "1650 x 992 mm")

    Retourne :
        Surface en m² (float) ou None si impossible à parser
    """
    # Si la valeur est vide ou NaN
    if pd.isna(s):
        return None

    # Conversion en texte minuscule et remplacement virgule → point
    text = str(s).lower().replace(",", ".")

    # --- RECHERCHE DU MOTIF : NOMBRE x NOMBRE UNITÉ ---
    # Ex: "1650 x 992 mm" ou "1.65 x 0.992 m"
    m = re.search(r"([\d\.]+)\s*[x×*]\s*([\d\.]+)\s*(mm|cm|m)?", text)

    if not m:
        # Tentative avec unités séparées : "1650mm x 992mm"
        m = re.search(r"([\d\.]+)\s*(mm|cm|m)\s*[x×]\s*([\d\.]+)\s*(mm|cm|m)", text)

        if not m:
            # Solution de secours : cherche juste deux nombres dans le texte
            m2 = re.findall(r"([\d\.]+)", text)
            if len(m2) >= 2:
                a = float(m2[0])
                b = float(m2[1])
                # Devine l'unité selon la taille des valeurs
                # Si > 100, on suppose que c'est en millimètres
                if a > 100 and b > 100:
                    return (a / 1000.0) * (b / 1000.0)  # mm → m
                else:
                    return a * b  # Déjà en mètres
            return None
        else:
            # Cas avec unités explicites sur chaque nombre
            a = float(m.group(1))
            unit1 = m.group(2)
            b = float(m.group(3))
            unit2 = m.group(4)

            # Fonction pour convertir en mètres
            def to_m(v, u):
                if u == "mm":
                    return v / 1000.0
                if u == "cm":
                    return v / 100.0
                if u == "m" or u is None:
                    return v
                return v

            # Calcul de la surface : largeur × hauteur (toutes deux en mètres)
            return to_m(a, unit1) * to_m(b, unit2)

    # Si on arrive ici, on a trouvé le motif de base
    a = float(m.group(1))
    b = float(m.group(2))
    unit = m.group(3)  # Peut être None si pas d'unité spécifiée

    # Conversion selon l'unité
    if unit == "mm":
        return (a / 1000.0) * (b / 1000.0)
    if unit == "cm":
        return (a / 100.0) * (b / 100.0)

    # Pas d'unité : on devine selon la taille des valeurs
    if a > 100 and b > 100:
        return (a / 1000.0) * (b / 1000.0)  # Probablement en mm

    return a * b  # Probablement déjà en mètres


# ==============================================================================
# FONCTION : NORMALISER LE PRIX EN CHF
# ==============================================================================
def normalize_price_to_chf(raw):
    """
    Convertit un prix (dans n'importe quelle devise) en francs suisses (CHF).

    Détecte automatiquement la devise dans le texte et applique le taux de change.

    Exemples :
    - "€150" → (160.5, 'EUR')  [150 × 1.07]
    - "150 CHF" → (150.0, 'CHF')
    - "150" → (150.0, 'CHF')  [par défaut]

    Arguments :
        raw : valeur brute pouvant contenir prix et devise (str, float, etc.)

    Retourne :
        Tuple (prix_en_chf, devise_detectée) ou (None, None) si échec
    """
    # Si la valeur est vide
    if pd.isna(raw):
        return None, None

    # Conversion en texte
    s = str(raw).strip()

    # --- DÉTECTION DE LA DEVISE ---
    cur = None  # Variable qui contiendra la devise détectée

    # Recherche de "CHF", "franc", "fr."
    if re.search(r"franc|chf|fr\.", s, flags=re.IGNORECASE):
        cur = "CHF"
    # Recherche de "€", "EUR", "euro"
    elif "€" in s or re.search(r"\beur\b|\beuro", s, flags=re.IGNORECASE):
        cur = "EUR"
    # Recherche de "$", "USD"
    elif "$" in s or re.search(r"\busd\b", s, flags=re.IGNORECASE):
        cur = "USD"

    # --- EXTRACTION DU NOMBRE ---
    # On garde seulement les chiffres, points, virgules et signes moins
    snum = s.replace("\xa0", " ")  # Espace insécable → espace normal
    snum = re.sub(r"[^\d\.,\-]", "", snum).replace(",", ".")  # Nettoyage

    # Tentative de conversion en nombre
    try:
        val = float(snum)
    except (TypeError, ValueError):
        # Si ça échoue, on essaie avec la fonction try_cast_float
        val = try_cast_float(raw)

    if val is None:
        return None, None

    # Si aucune devise détectée, on suppose CHF par défaut
    if cur is None:
        cur = "CHF"

    # Application du taux de change
    rate = EXCHANGE_TO_CHF.get(cur, 1.0)  # Récupère le taux ou 1.0 si devise inconnue

    return float(val) * rate, cur


# ==============================================================================
# FONCTION PRINCIPALE : TROUVER LE MEILLEUR PANNEAU
# ==============================================================================
def find_best_panel(csv_path, surface_m2, required_power_w):
    """
    Analyse le fichier CSV et trouve le meilleur panneau selon les critères.

    Processus :
    1. Lit le fichier CSV (essaie différents encodages)
    2. Identifie les colonnes pertinentes
    3. Extrait les données de chaque panneau
    4. Calcule combien de panneaux sont nécessaires
    5. Vérifie si la surface disponible est suffisante
    6. Sélectionne le panneau le moins cher qui convient

    Arguments :
        csv_path : chemin vers le fichier CSV
        surface_m2 : surface disponible en m²
        required_power_w : puissance demandée en Watts

    Retourne :
        Tuple (meilleur_panneau, tous_les_résultats)
    """

    # --- LECTURE DU FICHIER CSV ---
    # On essaie plusieurs encodages car on ne sait pas lequel est utilisé
    df = None
    csv_path = Path(csv_path)

    for enc in ("utf-8", "latin1", "cp1252"):
        try:
            # Tentative de lecture avec séparateur virgule par défaut
            df = pd.read_csv(csv_path, encoding=enc)
            break
        except Exception:
            try:
                # Tentative avec séparateur point-virgule (format français)
                df = pd.read_csv(csv_path, sep=";", encoding=enc)
                break
            except Exception:
                df = None

    # Si toutes les tentatives ont échoué
    if df is None:
        raise RuntimeError("Impossible de lire le fichier CSV: " + str(csv_path))

    # --- IDENTIFICATION DES COLONNES ---
    lookup = detect_columns(df)

    # --- EXTRACTION DES DONNÉES DE CHAQUE PANNEAU ---
    candidates = []  # Liste qui contiendra tous les panneaux valides

    # On parcourt chaque ligne du CSV (chaque panneau)
    for idx, row in df.iterrows():
        # --- EXTRACTION DU MODÈLE ---
        if "model" in lookup:
            model = str(row.get(lookup.get("model")))
        else:
            # Si pas de colonne "modèle", on prend la première colonne
            model = str(row.iloc[0])

        # --- EXTRACTION DE LA PUISSANCE ---
        power = None
        if "power" in lookup:
            # Si on a identifié une colonne "puissance"
            power = try_cast_float(row.get(lookup["power"]))
        else:
            # Sinon, on cherche dans toutes les colonnes un nombre suivi de W ou kW
            for c in df.columns:
                v = row.get(c)
                vv = str(v)
                m = re.search(r"([\d\.,]+)\s*(kW|W)\b", vv, flags=re.IGNORECASE)
                if m:
                    val, unit = parse_number_with_unit(m.group(0))
                    if unit == "W":
                        power = val
                        break

        # Si on n'a pas trouvé de puissance, on ignore ce panneau
        if power is None:
            continue

        # --- EXTRACTION DE LA SURFACE ---
        area = None

        # On essaie d'abord les colonnes candidates identifiées
        if "area_candidate" in lookup:
            for ac in lookup["area_candidate"]:
                v = row.get(ac)

                # Tentative 1 : valeur numérique directe
                a = try_cast_float(v)
                if a is not None:
                    # Si le nom de la colonne contient "m2" ou "m²", on accepte la valeur
                    # ou si la valeur est petite (< 5), probablement déjà en m²
                    if "m2" in str(ac).lower() or "m²" in str(ac).lower() or a < 5:
                        area = a
                        break

                # Tentative 2 : parse des dimensions (ex: "1650 x 992 mm")
                area_dim = parse_dimensions_to_m2(v)
                if area_dim:
                    area = area_dim
                    break

        # Si toujours pas de surface, on cherche dans toutes les autres colonnes
        if area is None:
            for c in df.columns:
                # On ignore les colonnes déjà vérifiées
                if c in lookup.get("area_candidate", []):
                    continue
                v = row.get(c)
                area_dim = parse_dimensions_to_m2(v)
                if area_dim:
                    area = area_dim
                    break

        # --- EXTRACTION DU PRIX ---
        price_chf, cur = None, None

        if "price" in lookup:
            # Si on a identifié une colonne "prix"
            price_chf, cur = normalize_price_to_chf(row.get(lookup["price"]))
        else:
            # Sinon, on cherche dans toutes les colonnes
            for c in df.columns:
                v = row.get(c)
                s = str(v)
                # Si le nom de la colonne ou la valeur contient un indicateur de prix
                if re.search(
                    r"\b(prix|price|chf|€|eur|\$)\b", c, flags=re.IGNORECASE
                ) or re.search(r"€|chf|\$|prix|price", s, flags=re.IGNORECASE):
                    price_chf, cur = normalize_price_to_chf(v)
                    if price_chf is not None:
                        break

        # --- VALIDATION DES DONNÉES ---
        # Si puissance ou prix manquants, on ignore ce panneau
        if power is None or price_chf is None:
            continue

        # Si surface inconnue, on ne peut pas vérifier la contrainte
        # On ignore aussi ce panneau pour éviter les erreurs
        if area is None:
            continue

        # --- AJOUT DU PANNEAU À LA LISTE DES CANDIDATS ---
        candidates.append(
            {
                "index": idx,
                "model": model,
                "power_w": float(power),
                "area_m2": float(area),
                "price_chf": float(price_chf),
            }
        )

        name_col = lookup.get("model")
        power_col = lookup.get("power")
        area_col = (
            lookup.get("area_candidate")[0] if "area_candidate" in lookup else None
        )
        cost_col = lookup.get("price")

        panels: Dict[str, Panel] = {}
        for idx, row in df.iterrows():
            name = str(row[name_col]) if name_col else f"panel_{idx}"
            try:
                power = (
                    float(row[power_col])
                    if power_col and not pd.isna(row[power_col])
                    else 0.0
                )
            except Exception:
                power = 0.0
            try:
                area = (
                    float(row[area_col])
                    if area_col and not pd.isna(row[area_col])
                    else 0.0
                )
            except Exception:
                area = 0.0
            try:
                cost = (
                    float(row[cost_col])
                    if cost_col and not pd.isna(row[cost_col])
                    else 0.0
                )
            except Exception:
                cost = 0.0

            panel = Panel(id=name, power_w=power, area_m2=area, cost_per_m2=cost)
            panels[name] = panel

        # Expose each panel as a safe module-level variable: e.g. "Panasonic_300W" -> Panasonic_300W
        for n, p in panels.items():
            safe = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in n)
            if not safe:
                continue
            if not safe[0].isalpha():
                safe = "_" + safe
            globals()[safe] = p

        return panels

    def surface_needed(
        installed_power_kw: float,
        panel_power_w: Optional[float] = None,
        panel_area_m2: Optional[float] = None,
        panels: Optional[Dict[str, Panel]] = None,
        panel_name: Optional[str] = None,
        margin: float = 0.0,
    ) -> Dict[str, float]:
        """
        Calcule le nombre de panneaux et la surface totale nécessaire pour une puissance d'installation donnée.
        - installed_power_kw: puissance souhaitée en kW (ex: 5 -> 5000 W)
        - panel_power_w / panel_area_m2: si fournis, utilisation directe
        - panels + panel_name: si fournis, récupère les caractéristiques depuis le dictionnaire retourné par load_panels
        - margin: marge supplémentaire (ex: 0.10 pour 10%)

        Retour: dict { 'required_panels': int, 'total_area_m2': float, 'provided_power_w': float }
        """
        if panel_name:
            if panels is None or panel_name not in panels:
                raise ValueError(
                    "Si panel_name est fourni, panels doit contenir ce nom."
                )
            panel = panels[panel_name]
            panel_power_w = panel.power_w
            panel_area_m2 = panel.area_m2

        if panel_power_w is None or panel_power_w <= 0:
            raise ValueError(
                "La puissance du panneau (panel_power_w) doit être fournie et > 0."
            )
        if panel_area_m2 is None or panel_area_m2 <= 0:
            raise ValueError(
                "La surface du panneau (panel_area_m2) doit être fournie et > 0."
            )

        target_w = float(installed_power_kw) * 1000.0
        effective_target = target_w * (1.0 + float(margin))
        required_panels = math.ceil(effective_target / float(panel_power_w))
        total_area = required_panels * float(panel_area_m2)
        provided_power = required_panels * float(panel_power_w)

        return {
            "required_panels": required_panels,
            "total_area_m2": total_area,
            "provided_power_w": provided_power,
        }

    def find_best_panel(
        installed_power_kw: float, panels: Dict[str, Panel], margin: float = 0.0
    ) -> Dict[str, any]:
        """
        Trouve le meilleur panneau selon le ratio puissance/coût.
        Retourne le nom du panneau et les résultats de surface_needed pour ce panneau.
        """
        if not panels:
            raise ValueError("Le dictionnaire de panneaux ne peut pas être vide.")

        best_panel_name = None
        best_ratio = 0

        for name, panel in panels.items():
            if panel.power_w <= 0 or panel.cost_per_m2 <= 0:
                continue
            ratio = panel.power_w / panel.cost_per_m2
            if ratio > best_ratio:
                best_ratio = ratio
                best_panel_name = name

        if best_panel_name is None:
            raise ValueError("Aucun panneau valide trouvé dans le dictionnaire.")

        result = surface_needed(
            installed_power_kw=installed_power_kw,
            panel_name=best_panel_name,
            panels=panels,
            margin=margin,
        )
        return {"best_panel": best_panel_name, **result}

    # --- CALCUL POUR CHAQUE PANNEAU ---
    results = []

    for c in candidates:
        # Calcul du nombre de panneaux nécessaires
        # On arrondit vers le haut (ex: 4.2 → 5 panneaux)
        n_panels = math.ceil(required_power_w / c["power_w"])

        # Calcul de la surface totale occupée
        total_area = n_panels * c["area_m2"]

        # Calcul du prix total
        total_price = n_panels * c["price_chf"]

        # Vérification : est-ce que ça rentre dans la surface disponible ?
        # On ajoute 1e-9 pour gérer les erreurs d'arrondi numérique
        fits = total_area <= surface_m2 + 1e-9

        # Stockage des résultats
        results.append(
            {
                **c,  # On copie toutes les données du panneau
                "n_panels": n_panels,
                "total_area": total_area,
                "total_price_chf": total_price,
                "fits": fits,  # True si ça rentre, False sinon
            }
        )

    # --- SÉLECTION DU MEILLEUR PANNEAU ---

    # Filtre : on garde seulement les panneaux qui rentrent dans la surface
    fits_list = [r for r in results if r["fits"]]

    if fits_list:
        # Si au moins un panneau convient, on choisit le moins cher
        # En cas d'égalité de prix, on choisit celui qui occupe le moins de surface
        fits_list.sort(key=lambda r: (r["total_price_chf"], r["total_area"]))
        best = fits_list[0]
        return best, results
    else:
        # Aucun panneau ne rentre dans la surface disponible
        # On propose quand même le panneau qui dépasse le moins

        # Calcul du dépassement de surface pour chaque panneau
        for r in results:
            r["area_over"] = r["total_area"] - surface_m2

        # Tri : d'abord par dépassement minimal, puis par prix
        results.sort(key=lambda r: (max(r["area_over"], 0.0), r["total_price_chf"]))
        best = results[0]
        return best, results


# ==============================================================================
# FONCTION PRINCIPALE DU PROGRAMME
# ==============================================================================


def main():
    """
    Point d'entrée principal du programme.
    Cette fonction orchestre tout le processus :
    1. Lit les paramètres fournis par l'utilisateur
    2. Extrait les données depuis HTML et/ou arguments
    3. Trouve le meilleur panneau
    4. Affiche les résultats de manière lisible
    """

    # ===========================================================================
    # ÉTAPE 1 : CONFIGURATION DU PARSEUR D'ARGUMENTS
    # ===========================================================================
    # argparse permet de lire les options de ligne de commande
    # Ex: python script.py --surface 25 --power 5000
    p = argparse.ArgumentParser(
        description="Trouve le meilleur panneau selon surface, puissance et coût."
    )

    # Définition de l'argument --html
    # 'default' : si l'utilisateur ne spécifie rien, on utilise "index.html"
    p.add_argument(
        "--html",
        default="index.html",
        help="Chemin vers index.html contenant les données d'entrée",
    )

    # Définition de l'argument --csv
    # Permet de spécifier un autre fichier CSV que celui par défaut
    p.add_argument(
        "--csv",
        default="Comparatif de 20 panneaux photovoltaïque.csv",
        help="Fichier CSV comparatif",
    )

    # Définition de l'argument --surface
    # type=float : force la conversion en nombre décimal
    # Pas de default : optionnel, None si non fourni
    p.add_argument("--surface", type=float, help="Surface disponible en m2 (override)")

    # Définition de l'argument --power
    # Permet de forcer la puissance sans lire le HTML
    p.add_argument("--power", type=float, help="Puissance demandée en W (override)")

    # Parse (analyse) les arguments fournis par l'utilisateur
    # args contiendra tous les paramètres sous forme d'objet
    # Ex: args.surface, args.power, args.html, args.csv
    args = p.parse_args()

    # ===========================================================================
    # ÉTAPE 2 : RÉCUPÉRATION DES PARAMÈTRES D'ENTRÉE
    # ===========================================================================

    # Tentative d'extraction des données depuis le fichier HTML
    # parsed sera un dictionnaire, ex: {'surface_m2': 25.0, 'required_power_w': 5000.0}
    parsed = parse_index_html(args.html)

    # Détermination de la surface à utiliser
    # PRIORITÉ : argument ligne de commande > valeur du HTML
    # Si args.surface n'est pas None (l'utilisateur l'a spécifié), on l'utilise
    # Sinon, on prend la valeur extraite du HTML (ou None si pas trouvée)
    surface = args.surface if args.surface is not None else parsed.get("surface_m2")

    # Détermination de la puissance à utiliser
    # Même logique de priorité que pour la surface
    power = args.power if args.power is not None else parsed.get("required_power_w")

    # ===========================================================================
    # ÉTAPE 3 : VALIDATION DES DONNÉES
    # ===========================================================================

    # Vérification : on a besoin d'au moins une surface ET une puissance
    # Si l'une des deux est None, on ne peut pas continuer
    if surface is None or power is None:
        # Affichage d'un message d'erreur explicatif
        print(
            "Erreur: impossible d'obtenir surface et puissance. Spécifiez --surface et --power ou vérifiez index.html."
        )

        # Affichage de ce qui a été trouvé dans le HTML pour aider au débogage
        # Ex: si parsed = {'surface_m2': 25.0}, l'utilisateur verra qu'il manque la puissance
        print("Valeurs trouvées dans index.html:", parsed)

        # Quitte le programme avec le code d'erreur 1
        # Code 0 = succès, Code 1 = erreur
        sys.exit(1)

    # ===========================================================================
    # ÉTAPE 4 : RECHERCHE DU MEILLEUR PANNEAU
    # ===========================================================================

    try:
        # Appel de la fonction principale qui analyse le CSV
        # float(surface) et float(power) : conversion explicite en nombre décimal
        #
        # Retour :
        # - best : dictionnaire avec les infos du meilleur panneau
        # - all_results : liste de tous les panneaux analysés (pour référence)
        best, all_results = find_best_panel(args.csv, float(surface), float(power))

    except Exception as e:
        # Si une erreur survient (CSV illisible, format incorrect, etc.)
        # on l'attrape ici et on affiche un message explicatif
        print("Erreur lors du traitement du CSV:", e)
        sys.exit(1)  # Quitte avec code d'erreur

    # ===========================================================================
    # ÉTAPE 5 : AFFICHAGE DES RÉSULTATS
    # ===========================================================================

    # --- En-tête des résultats ---
    print("Résultat:")

    # Affichage de la surface disponible
    # {surface:.2f} signifie : affiche le nombre avec 2 chiffres après la virgule
    # Ex: 25.0 → "25.00 m2", 25.567 → "25.57 m2"
    print(f"Surface disponible: {surface:.2f} m2")

    # Affichage de la puissance demandée
    # {power:.0f} signifie : affiche le nombre sans chiffres après la virgule
    # Ex: 5000.0 → "5000 W", 5234.7 → "5235 W"
    print(f"Puissance demandée: {power:.0f} W")

    # Ligne vide pour la lisibilité
    print("")

    # --- Détails du panneau sélectionné ---
    print("Meilleur panneau (sélection):")

    # Nom/modèle du panneau
    # best['model'] récupère la valeur associée à la clé 'model' dans le dictionnaire
    print(f"Modèle: {best['model']}")

    # Puissance d'un seul panneau (en Watts)
    # {best['power_w']:.0f} → pas de décimales, ex: "450 W"
    print(f"Puissance par panneau: {best['power_w']:.0f} W")

    # Surface d'un seul panneau (en m²)
    # {best['area_m2']:.3f} → 3 décimales, ex: "1.234 m2"
    # Utile car les panneaux ont souvent des surfaces précises comme 1.638 m²
    print(f"Surface par panneau: {best['area_m2']:.3f} m2")

    # Prix d'un seul panneau (en CHF)
    # {best['price_chf']:.2f} → 2 décimales (format monétaire standard)
    # Ex: "234.50 CHF"
    print(f"Prix unitaire (approx. CHF): {best['price_chf']:.2f} CHF")

    # Nombre de panneaux nécessaires pour atteindre la puissance demandée
    # C'est un nombre entier (déjà calculé avec math.ceil dans find_best_panel)
    # Ex: si on demande 5000W et qu'un panneau fait 450W, il faut 12 panneaux
    print(f"Nombre de panneaux requis: {best['n_panels']}")

    # Surface totale occupée par tous les panneaux
    # = nombre de panneaux × surface d'un panneau
    # {best['total_area']:.3f} → 3 décimales, ex: "14.856 m2"
    print(f"Surface totale requise: {best['total_area']:.3f} m2")

    # Prix total de l'installation
    # = nombre de panneaux × prix unitaire
    # {best['total_price_chf']:.2f} → format monétaire, ex: "2814.00 CHF"
    print(f"Prix total: {best['total_price_chf']:.2f} CHF")

    # Indication si le panneau convient à la surface disponible
    # Expression ternaire (condition) :
    # - Si best.get('fits') est True → affiche "Oui"
    # - Si best.get('fits') est False → affiche "Non (surface insuffisante)"
    #
    # .get('fits') est utilisé plutôt que ['fits'] pour éviter une erreur
    # si la clé n'existe pas (retournerait None au lieu de lever une exception)
    print(
        "Satisfait la surface disponible:",
        "Oui" if best.get("fits") else "Non (surface insuffisante)",
    )


# ==============================================================================
# POINT D'ENTRÉE DU PROGRAMME
# ==============================================================================
# Cette condition spéciale vérifie si le fichier est exécuté directement
# (et non importé comme module dans un autre script Python)

if __name__ == "__main__":
    # __name__ est une variable spéciale Python
    # - Si le script est exécuté directement : __name__ == '__main__'
    # - Si le script est importé : __name__ == 'nom_du_fichier'
    #
    # Cette condition empêche l'exécution automatique de main() si quelqu'un
    # importe ce fichier dans un autre script
    #
    # Cas d'usage :
    # - python cost_panel.py → __name__ == '__main__' → main() s'exécute
    # - import cost_panel (dans un autre fichier) → main() ne s'exécute PAS
    main()
