#  Proposition de Projet : Système d'Orientation Photovoltaïque Intelligent

---

##  Équipe du Projet

| Membre                  | Rôle         |
| ----------------------- | ------------ |
| **Dahman Elisa**        | Développeuse |
| **Conde Garea Gabriel** | Développeur  |
| **Gloor Lorentin**      | Développeur  |

---

##  Description du Projet

Le projet **Orientation_PV** vise à développer un système intelligent de gestion d'orientation pour panneaux photovoltaïques. Ce programme optimisera automatiquement la position des panneaux en fonction de la trajectoire solaire et gérera efficacement l'énergie produite.

###  Paramètres pris en compte

Le système analysera en temps réel les données suivantes :

-  **Saison** - adaptation à la hauteur du soleil
-  **Heure** - suivi de la course 
-  **Luminosité** - détection des conditions réelles
-  **Charge des batteries** - gestion du stockage
-  **Météo** - adaptation aux conditions climatiques
-  **Demande d'énergie** - réponse aux besoins
###  Système mécanique




Le dispositif utilisera des **moteurs rotatifs** permettant :

- La rotation azimutale (suivi Est-Ouest)
- L'inclinaison variable (adaptation saisonnière)
- Un positionnement optimal tout au long de l'année

---

##  Objectifs du Projet

###  Objectif 1 : Calcul de la Position Solaire

Développer un algorithme capable de déterminer avec précision la position du soleil en intégrant :

- Les coordonnées géographiques
- La date et l'heure
- Les conditions météorologiques
- Les mesures de luminosité en temps réel

###  Objectif 2 : Pilotage des Moteurs

Implémenter un système de contrôle moteur permettant :

- Le positionnement précis des panneaux
- Des mouvements fluides et optimisés
- Une maintenance préventive du matériel

###  Objectif 3 : Gestion de l'Énergie

Créer un module de gestion énergétique intelligent qui :

- Surveille l'état de charge des batteries
- Distribue l'énergie aux consommateurs en temps réel
- Réinjecte l'excédent sur le réseau électrique
- Optimise le rendement global du système

###  Objectif 4 : Interface et Simulation

Développer une interface utilisateur complète comprenant :

- Une simulation du comportement du système
- Des visualisations en temps réel
- Des tableaux de bord de performance
- Des tests sous différentes configurations

---

##  Technologies Envisagées
- **Langage** : Python / C++
- **Interface** : Interface graphique (Qt, Tkinter, ou web)
- **Simulation** : Modélisation 3D du mouvement
- **Calculs astronomiques** : Librairies spécialisées (PyEphem, NOAA)

---

## session 1
Choix du sujet et de l'étendue de ce dernier. Ecriture du journal de bord et présentation du projet.

## session 2
réflexion et choix de l'arborescence du code ainsi que des packages utilisés. Concernant le choix des package, le logiciel PVsyst a servit d'inspiration. En effet les calculs de position, d'astronomie, d'énergie produite, etc ... nécessitent différents packages. 

Ecriture de l'architecture du projet.

Problème de git push/pull à résoudre avec M.Chevalier.

## session 3 
Résolution du problème de push/pull.
Update de l'architecture du projet. 
Ecriture du fichier géometrie (fonction).

## session 4
Création du GUI web
Init analyses économiques
Update architecture projet
ajout fichiers regul 
ajout simul energ
ajout production
suppression GUI py

