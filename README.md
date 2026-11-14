# HELIOS — tableau de bord solaire

HELIOS est une application locale de pré-étude photovoltaïque. Elle estime la production solaire d'un site, aide à dimensionner une installation, compare différents équipements et calcule des indicateurs économiques.

Le projet a été réalisé dans le cadre d'un mini-projet Python académique. Il réunit une interface web, un moteur de calcul solaire, un client MeteoSwiss et des outils de comparaison financière.

## Fonctionnalités

- calcul de la position du Soleil et de l'irradiance reçue par les panneaux ;
- estimation des productions journalière, mensuelle et annuelle ;
- prise en compte des pertes courantes : ombrage, encrassement, température, câblage et onduleur ;
- récupération des données MeteoSwiss avec simulation en ciel clair hors ligne ;
- dimensionnement selon la puissance cible et la surface disponible ;
- comparaison de panneaux, d'onduleurs et de batteries ;
- calcul des coûts, revenus, flux de trésorerie et retour sur investissement ;
- export des résultats en CSV et en PDF via l'impression du navigateur.

## Prérequis

- Python 3.12 ou plus récent ;
- [`uv`](https://docs.astral.sh/uv/) recommandé pour gérer l'environnement et les dépendances.

## Installation

Clonez le dépôt, puis installez ses dépendances :

```bash
git clone git@github.com:pythonge2-a/mini-projet-helios.git
cd mini-projet-helios
uv sync
```

Une installation classique avec `pip` reste possible :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Lancement

Avec `uv` :

```bash
uv run python -m helios
```

Ou avec le raccourci fourni :

```bash
./run
```

L'application ouvre normalement le navigateur automatiquement. Sinon, rendez-vous sur <http://127.0.0.1:8000/>.

## Utilisation

1. Dans **Simulation**, indiquez le lieu, la date, l'orientation et les caractéristiques du système.
2. Lancez le calcul pour obtenir la production et les principaux indicateurs énergétiques.
3. Utilisez **Dimensionnement** pour choisir la puissance et le matériel adapté.
4. Complétez les hypothèses de coûts dans **Finances**.
5. Exportez la synthèse en CSV ou utilisez l'impression du navigateur pour créer un PDF.

Les paramètres MeteoSwiss se trouvent dans [`helios/data/config.yaml`](helios/data/config.yaml). Le mode de repli en ciel clair permet d'utiliser les calculs principaux sans connexion au service météo.

## Architecture

```text
.
├── helios/
│   ├── calculus/       Géométrie solaire et production énergétique
│   ├── data/           Configuration, stations et client MeteoSwiss
│   ├── economics/      Dimensionnement et comparaison des équipements
│   ├── interface/      Composants d'interface expérimentaux
│   ├── regul/          Régulation et orientation
│   ├── tests/          Tests automatisés
│   └── __main__.py     Serveur HTTP local et API de l'application
├── web/                Interface web principale
├── pyproject.toml      Métadonnées et dépendances Python
├── uv.lock             Versions reproductibles des dépendances
└── run                 Raccourci de lancement
```

## Données

Le dépôt contient :

- la liste publique des stations MeteoSwiss ;
- des tableaux comparatifs de panneaux, d'onduleurs et de batteries ;
- la configuration utilisée par le client météo.

Les résultats de l'application constituent des estimations pédagogiques. Ils ne remplacent pas une étude réalisée par un professionnel qualifié.

## Tests et qualité du code

Installez les dépendances de développement, puis lancez :

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Pour appliquer automatiquement le format Ruff :

```bash
uv run ruff format .
```

## État du projet

Le dépôt représente la version finale du mini-projet. L'interface principale est l'application web contenue dans `web/`; certains composants PySide présents dans `helios/interface/` documentent des expérimentations antérieures.

## Licence

Aucune licence open source n'a encore été sélectionnée. En l'absence de fichier `LICENSE`, les droits de réutilisation ne sont pas accordés automatiquement.
