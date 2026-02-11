# Documentation Technique : IA de Prédiction de Pollution Urbaine par Analyse Spectrale

## 1. Introduction
Ce document détaille l'architecture technique et mathématique de l'Intelligence Artificielle développée pour prédire les émissions polluantes (CO2, NOx) des réseaux routiers.
L'approche innovante de ce projet réside dans l'utilisation de la **Théorie Spectrale des Graphes** pour caractériser la topologie des villes et son influence sur la dynamique du trafic.

## 2. Pipeline de Données
Le système se décompose en 3 modules principaux :
1.  **Acquisition & Modélisation** : Téléchargement des cartes (OSM) et conversion en graphes orientés pondérés (SUMO).
2.  **Extraction de Caractéristiques (Feature Extraction)** : Calcul des descripteurs topologiques et spectraux.
3.  **Apprentissage Supervisé** : Entraînement d'un Réseau de Neurones sur les données de simulation.

---

## 3. Modélisation Mathématique
La ville est modélisée par un graphe $G = (V, E)$, où $V$ est l'ensemble des intersections et $E$ l'ensemble des routes.
Nous construisons la **Matrice d'Adjacence** $A$ de taille $N \times N$, où $A_{ij} = 1$ s'il existe une route de $i$ à $j$.

### 3.1. Rayon Spectral ($\rho$)
Le rayon spectral est défini comme la plus grande valeur propre (en module) de la matrice d'adjacence $A$ :
$$ \rho(G) = \max_{i} |\lambda_i(A)| $$

**Interprétation Trafic :**
Le rayon spectral mesure la "connectivité globale" et la capacité de diffusion du réseau via le "walk count".
-   Un $\rho$ élevé indique un grand nombre de chemins possibles, donc une forte complexité de navigation mais aussi une plus grande redondance (résilience).
-   Il est corrélé à la capacité du réseau à propager une congestion (effet cascade).

### 3.2. La Constante de Kreiss ($\mathcal{K}$) : Le "Détecteur de Nervosité"
Contrairement à l'analyse modale classique (valeurs propres) qui suppose un régime établi ($t \to \infty$), la constante de Kreiss capture le comportement transitoire (transient behavior).

Pour une matrice $A$, la constante de Kreiss est définie par l'analyse du **Pseudospectre** :
$$ \mathcal{K}(A) = \sup_{\varepsilon > 0} \frac{\sup_{|z|>1} \|(zI - A)^{-1}\|}{1/\varepsilon} $$

Concrètement, nous l'approximons par l'indice de **Non-Normalité** du graphe (commutateur $[A, A^T] \neq 0$).

**Pourquoi pour le trafic ?**
Dans les réseaux routiers (graphes orientés non-symétriques), des embouteillages géants peuvent émerger soudainement même si le système semble stable spectralement ($\rho < 1$ pour un système dynamique linéaire). C'est l'effet d'amplification transitoire.
-   Une $\mathcal{K}$ élevée signifie que le réseau est "nerveux" : une petite perturbation (accident, pluie) peut causer une congestion massive disproportionnée avant de se résorber.
-   C'est un indicateur clé pour distinguer des villes "robustes" (Grille américaine) des villes "sensibles" (Villes médiévales européennes).

---

## 4. Extraction de Caractéristiques (Scripts)
Le script `extract_features.py` calcule pour chaque ville :
1.  **Métriques Classiques** :
    -   $N$ (Nombre de nœuds), $M$ (Nombre d'arêtes).
    -   Densité $D = \frac{M}{N(N-1)}$.
2.  **Métriques Spectrales** :
    -   `spectral_radius` : Calculé via `scipy.sparse.linalg.eigs`.
    -   `kreiss_constant` : Estimée par la norme de Frobenius du commutateur $AA^T - A^TA$.

Ces caractéristiques forment le vecteur d'entrée $X$ de l'IA.

---

## 5. Modèle d'Intelligence Artificielle
Nous utilisons un **Perceptron Multicouche (MLPRegressor)**.

### 5.1. Optimisation des Hyperparamètres
Pour garantir la robustesse scientifique, les paramètres ne sont pas choisis au hasard mais trouvés via une recherche exhaustive (**Grid Search**) validée par validation croisée (Cross-Validation).

**Espace de Recherche :**
-   **Architecture** : 1 à 2 couches cachées, 50 à 100 neurones.
-   **Activation** : ReLU (Rectified Linear Unit) vs Tanh.
-   **Apprentissage** : Taux compris entre $10^{-3}$ et $10^{-2}$.

Le script `train_model.py` génère automatiquement un rapport `optimal_params.txt` justifiant le choix final.

## 6. Résultats et Perspectives
L'IA apprend la fonction $f : \mathbb{R}^d \to \mathbb{R}^+$ telle que :
$$ \text{Pollution}_{CO2} = f(\text{Topologie}, \text{Spectral}, \text{Flux}) $$

Les premiers résultats montrent que l'ajout des métriques spectrales améliore significativement la précision, confirmant que la "forme" mathématique de la ville dicte sa pollution autant que le nombre de voitures.
