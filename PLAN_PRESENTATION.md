# Plan de Présentation - Soutenance Doctorale / Stage

## Slide 1 : Titre & Introduction
-   **Titre** : Prédiction de la Pollution Urbaine par Intelligence Artificielle et Analyse Spectrale des Graphes.
-   **Contexte** : Urgence climatique, zones à faibles émissions (ZFE).
-   **Problématique** : Peut-on prédire la pollution d'une ville uniquement en analysant la géométrie de son plan et quelques paramètres de flux, sans simulation lourde ?

## Slide 2 : Méthodologie "Jumeau Numérique"
-   **Approche** : Simulation Microscopique vs IA.
-   **Outil** : SUMO (Simulation of Urban MObility).
-   **Données** : Génération de 5 Jumeaux Numériques (Paris, Berlin, LA, Madrid, Hanoi) avec 10 000 véhicules chacun.
-   *Visuel : Capture d'écran de l'interface SUMO avec les voitures.*

## Slide 3 : La Ville vue comme un Graphe (Maths)
-   Transformation de la carte en Graphe $G=(V,E)$.
-   Comparaison simple : Grille (LA) vs Organique (Paris).
-   **Limites des métriques classiques** : La densité ne suffit pas à expliquer la congestion.

## Slide 4 : L'Apport de l'Analyse Spectrale (Cœur scientifique)
-   **Concept** : Utiliser les valeurs propres de la matrice d'adjacence pour "écouter" la forme de la ville.
-   **Le Rayon Spectral ($\rho$)** : Mesure la connectivité et la redondance. Une ville à fort $\rho$ diffuse mieux le trafic.
-   **La Constante de Kreiss ($\mathcal{K}$)** :
    -   *Définition vulgarisée* : Le "coefficient de nervosité" du réseau.
    -   *Importance* : Prévoit la sensibilité aux bouchons fantômes et aux perturbations.
    -   *Hypothèse* : $\mathcal{K}$ élevé $\Rightarrow$ Pollution Instable/Élevée.

## Slide 5 : L'Intelligence Artificielle
-   **Modèle** : Réseau de Neurones (MLP).
-   **Entrées (Features)** : Rayon Spectral, Kreiss, Densité, Nombre de Véhicules.
-   **Sortie (Target)** : Émissions CO2 Totales.
-   **Processus** : Entraînement sur les simulations $\to$ Prédiction sur de nouvelles villes inconnues.

## Slide 6 : Optimisation & Résultats
-   Méthode de recherche des hyperparamètres optimaux (Grid Search).
-   Présentation des courbes de performance (R² score).
-   *Tableau comparatif* : Prédiction vs Réalité (Simulation).

## Slide 7 : Conclusion & Perspectives
-   **Validation** : L'IA parvient à distinguer les types de villes grâce aux signatures spectrales.
-   **Futur** : Étendre à 100 villes, intégrer la topographie (hauteur) et la météo.
