# Documentation : Analyse Topologique et Spectrale des Réseaux Urbains

## 1. Introduction & Objectifs
Cette documentation détaille les méthodes mathématiques utilisées pour "profiler" une ville à partir de son réseau routier. L'objectif est d'extraire une **Signature Topologique** unique pour chaque ville, capable de prédire son comportement (congestion, pollution) sans simulation lourde.
Nous nous basons sur la **Théorie des Graphes**, l'**Algèbre Linéaire Numérique** et l'étude des **Systèmes Dynamiques**.

---

## 2. Modélisation Fondamentale
La ville est représentée par un Graphe Orienté Pondéré $G = (V, E, W)$.
*   $V$ (Vertices) : Les intersections (carrefours).
*   $E$ (Edges) : Les routes reliant les intersections.
*   $W$ (Weights) : Poids des arêtes (longueur, ou inverse de la capacité).

### Matrice d'Adjacence ($A$)
La matrice $A$ de taille $N \times N$ capture la structure de connectivité.
$$ A_{ij} = \begin{cases} 1 & \text{si une route va de } i \text{ vers } j \\ 0 & \text{sinon} \end{cases} $$
*Note : Dans nos calculs, nous pondérons parfois par la capacité de la route.*

---

## 3. Métriques Structurelles (Macroscopiques)
Ces mesures sont issues de la théorie des réseaux complexes (instructions doctorales).

### 3.1. Densité ($\delta$)
Ratio entre le nombre d'arêtes existantes et le nombre maximum possible.
$$ \delta = \frac{|E|}{|V|(|V|-1)} $$
*   **Interprétation** : Une densité faible indique un réseau "clairsemé" (étalement urbain). Une densité élevée indique un maillage très fin (centre historique).

### 3.2. Degré Moyen ($\langle k \rangle$)
Nombre moyen de routes connectées à un carrefour.
$$ \langle k \rangle = \frac{|E|}{|V|} $$
*   **Interprétation** :
    *   $\approx 2.5$ : Ville linéaire ou cul-de-sac.
    *   $\approx 4.0$ : Ville en grille (Manhattan).
    *   $> 4.5$ : Ville complexe avec ronds-points multiples et échangeurs.

### 3.3. Diamètre ($D$) et Efficacité Globale
Le diamètre est la longueur du "plus long des plus courts chemins".
*   **Interprétation** : Mesure l'étalement de la ville. Un grand diamètre implique des trajets potentiellement longs et une pollution dispersée.

---

## 4. Analyse Spectrale & Dynamique (La "Touche Doctorat")
C'est ici que l'analyse dépasse les statistiques simples pour étudier la **dynamique** du réseau.

### 4.1. Le Rayon Spectral ($\rho$)
Défini comme la plus grande valeur propre de la matrice d'adjacence $A$.
$$ \rho(A) = \max_i |\lambda_i| $$

*   **Théorie** : Le Théorème de Perron-Frobenius garantit l'existence de cette valeur pour un graphe fortement connexe.
*   **Sens Physique** : $\rho$ est lié au "nombre de chemins" dans le graphe.
    *   $\rho$ faible : Réseau peu maillé, peu d'alternatives (fragile).
    *   $\rho$ élevé : Réseau très interconnecté, forte redondance (résilient).
*   **Source** : *Chung, F. R. K. (1997). Spectral Graph Theory. AMS.*

### 4.2. La Constante de Kreiss ($\mathcal{K}$) : L'Instabilité Transitoire
C'est un concept avancé d'algèbre linéaire pour les matrices non-normales (où $A A^T \neq A^T A$), ce qui est le cas des villes (rues à sens unique).

$$ \mathcal{K}(A) \equiv \sup_{\epsilon > 0} \frac{\alpha_\epsilon(A) - \alpha(A)}{\epsilon} \quad \text{(Définition liée au Pseudospectre)} $$
*Approximation pratique : Norme du commutateur $[A, A^T]$.*

*   **Interprétation Majeure** :
    Si un système est stable à long terme (valeurs propres < 1), il peut quand même "exploser" temporairement.
    *   **Trafic** : Dans une ville à fort $\mathcal{K}$, un petit bouchon peut s'amplifier de manière exponentielle avant de se résorber (effet papillon). C'est le marqueur de la **NERVOSITÉ** du trafic.
*   **Source** : *Trefethen, L. N., & Embree, M. (2005). Spectra and Pseudospectra: The Behavior of Nonnormal Matrices and Operators. Princeton University Press.*

---

## 5. Algorithme d'Analyse (Implémenté dans `analyze_city_structure.py`)
1.  **Construction du Graphe** via `sumolib` (lecture native .net.xml).
2.  **Calcul de la Matrice $A$** (Sparse Matrix pour optimiser la mémoire).
3.  **Résolution des Valeurs Propres** (Algorithme d'Arnoldi via `ARPACK`).
4.  **Estimation Non-Normalité** (Proxy pour Kreiss).
5.  **Output** : Rapport complet JSON/Markdown.

## 6. Bibliographie & Références
1.  **Newman, M. E. J. (2010).** *Networks: An Introduction.* Oxford University Press. (La bible des réseaux complexes).
2.  **Trefethen, L. N.** (1992). *Pseudospectra of matrices.* (Pour la constante de Kreiss).
3.  **Mohar, B.** (1991). *The Laplacian Spectrum of Graphs.* (Pour le lien entre spectre et géométrie).
