# Présentation Scientifique : Prédiction des Émissions de CO2 Urbain par Intelligence Artificielle et Théorie des Graphes

Présentateur : Thomas
Date : Mars 2026

*Sujet du Projet : Comment la topologie urbaine et l'analyse du trafic peuvent nourrir un modèle de Machine Learning pour la prédiction de CO2.*

---

## 1. Introduction : L'Enjeu Climatique et Topologique
*   **Problématique globale** : La pollution automobile est un facteur critique dans les grandes agglomérations. L'objectif est de prédire précisément le volume de CO2 avant qu'il ne se forme.
*   **Hypothèse de recherche** : La structure mathématique du réseau routier (la Géométrie de la ville) influence de façon vitale la formation de la pollution, indépendamment de la quantité brute de véhicules.
*   **Objectif du Modèle (IA)** : Relier finement les propriétés du graphe de la ville aux données de trafic pour deviner la masse de pollution finale d'un scénario de simulation SUMO futur.

---

## 2. Extraction des Données : Définition de ( $X$ | $y$ )

Pour entraîner l'Intelligence Artificielle, nous devions construire un référentiel de données parfait. Suite à la décision collégiale sur l'approche à suivre, nous définissons :

**Variables Prédictives $X$ : Qu'est-ce que l'IA va lire ?**
1.  *La Topologie ($X_{topo}$) :*
    *   **$n$** : Nombre de nœuds (intersections).
    *   **$m$** : Nombre d'arêtes (routes).
    *   **Densité** : Le ratio calculé comme $\frac{m}{0.5n(n-1)}$ (La complexité du labyrinthe).
    *   **Degré Moyen** : La moyenne mathématique $\frac{2m}{n}$ (Nombre moyen de branches traversables par carrefour).
    *   **Analyse Spectrale ($\rho$)** : Valeur propre maximale issue de la théorie algébrique des graphes (Mesure la connectivité fondamentale).
    *   **Constante de Kreiss** : Détecteur de sensibilité. Elle mesure si le réseau est de nature "nerveuse" (une perturbation créerait un effet domino) ou "robuste".

2.  *Le Trafic ($X_{trafic}$) :*
    *   **Durée de la simulation** : Le temps global $t$.
    *   **Parc Automobile Complet** : Nombre absolu et individuel pour : *Voitures, Camions, Bus, Motos* ainsi que le *Total* absolu.

**Variable à prédire $y$ : L'Objectif**
*   **$y$** : La masse continue totale de $CO_2$ émise (Évaluée en Kilogrammes).

**Processus** : Pour chaque simulation SUMO ($N \approx 50$), l'extraction complexe de ces données livre $N$ tuples formatés : $(y | X)$ qui constituent notre Dataset parfait.

---

## 3. Choix du Modèle d'IA : L'Arbre de Décision Avancé

### Pourquoi choisir XGBoost ?
En Machine Learning, on adapte l'outil au besoin. Pourquoi avoir écarté un énorme Réseau de Neurones ?
1.  **Parc de variables ($X$) limité** $\rightarrow$ Ni image, ni texte, uniquement 12 valeurs numériques (Tableur).
2.  **Taille d'échantillon N relativement modeste** $\rightarrow$ Les modèles de Deep Learning ont la fâcheuse tendance à apprendre par cœur les échantillons limités sans capacité de généralisation (Sur-Apprentissage).

**Nous avons donc choisi XGBoost (Extreme Gradient Boosting)** de la famille des *Ensembles Learning*.
*   Il s'agit du modèle le plus primé en Science des Données pour les informations tabulaires et numériques.
*   **Sa plus grande force** : XGBoost construit plusieurs centaines (voire milliers) de petits "Arbres de Décision" à la suite. Chaque nouvel arbre s'entraîne spécifiquement à "corriger les erreurs mathématiques" (le gradient) résiduelles laissées par l'arbre précédent.

### Notre Modèle est une Régression (`XGBRegressor`)
Il est crucial de préciser l'approche scientifique concernant nos données :
*   L'exemple algorithmique classique d'une plante (Ex: l'*Iris flower dataset*) s'entraîne sur le module **`XGBClassifier`** car son but est de valider si "Oui" ou "Non" l'espèce est *Versicolor*. C'est ce qu'on appelle une approche Catégorielle (Classification). L'évaluation se fait alors via un pourcentage d'*Accuracy*.
*   Au contraire, notre variable cible ($y$) est un **nombre continu allant de centaines à des millions (les kg de CO2).** Nous utilisons un Modèle de Régression continue appelé **`XGBRegressor`**.  L'évaluation est effectuée en regardant la MAE (la moyenne des erreurs sur prédictions absolues) et le coefficient de certitude $R^2$.


---

## 4. Fonctionnement Interne d'XGBoost (Couche Arbre)

Pour dé-simplifier la "Boite Noire", que fait réellement notre algorithme à l'intérieur ?

**Étape 1 : Le Modèle de base** (La supposition innocente)
L'algorithme analyse l'ensemble des données d'entrée globalement et propose une moyenne naïve. 
*Moyenne = ~25,000 kg pour toute ville.*

**Étape 2 : Le premier Arbre (Généralisation Trafic / Topologique)**
Le Modèle calcule ce qui manque par rapport à 25,000kg.
*   Il crée son premier point de bifurcation binaire. Par exemple : il apprend que la densité a l'impact de variance le plus fort, il décide :
    *   *Branche Gauche* : Si *Densité* < 0.05 **ET** *Kreiss* > 50 $\rightarrow$ Il ajoute $+2,000$ kg.
    *   *Branche Droite* : Si *Densité* >= 0.05 $\rightarrow$ Il soustrait $-500$ Kg.

*(Notons l'intervention du Taux d'Apprentissage ou `learning_rate` : il n'applique qu'une fraction (ex: 5%) de l'arbre pour rester progressif et éviter le sur-apprentissage).*

**Étape 3 : Le millième et dernier Arbre (Spécialisation)**
A force de corriger ses erreurs de prédiction précédentes, le $1000^{eme}$ arbre ne s'occupera que de micro-détails, par ex : "*Corriger l'impact paradoxal produit uniquement quand il y a plus de 5000 Camions dans une ville ayant un Degré Moyen > 3.0*".

**Le résultat final $y$ prédit** est purement la somme mathématique de ces milliers de corrections successives (Boosting).

---

## 5. Bilan et Conclusion

1.  **La Similitude des Villes par Algorithme** : L'utilisation de notre référentiel de données sur les *Villes Prototypes* n'est plus utilisée pour scinder l'apprentissage de l'IA. Au contraire, XGBoost préfère la globalité des données pour repérer lui-même ces similitudes dans la construction de ses branches.
2.  L'extraction pure de la topologie ($X_{topo}$) permet désormais à une ville de voir son trafic *adapté algorithmiquement* à sa configuration physique avant même que la première ligne du scénario SUMO n'ait tourné 10 minutes !
3.  L'impact des features (*Feature Importance*) tiré en fin de processus par l'algorithme permet de mesurer exactement quelle variable topologique a pesé le plus lourd dans les prédictions (ex: La fameuse constante de la sensitivité perturbatrice *Kreiss*).
