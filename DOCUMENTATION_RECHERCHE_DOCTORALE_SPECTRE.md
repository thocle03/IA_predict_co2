# Rapport Méthodologique : Topologie Spectrale & Intelligence Artificielle

Ce guide est destiné à la documentation doctorale du projet. Il explique pourquoi la structure mathématique d'un réseau routier est le prédicteur le plus fiable de sa pollution future.

## 1. Vision Doctorale : Pourquoi le Spectre ?

La pollution urbaine est un phénomène dynamique (fluide) sur une structure statique (graphe). Traditionnellement, on simule chaque voiture. Notre approche est différente : nous analysons la **capacité de transport et de blocage** du réseau via ses propriétés spectrales.

### Le Concept de Non-Normalité
Un réseau de transport est un graphe dirigé, donc sa matrice d'adjacence est **non-normale**. Cela signifie que même si tous les signaux sont stables à long terme, ils peuvent subir une **amplification transitoire massive**. C'est le "coup de bélier" du trafic : une petite perturbation qui sature une ville entière.

## 2. Dictionnaire des Indicateurs de Performance

| Indicateur | Définition Doctorale | Traduction "Terrain" |
| :--- | :--- | :--- |
| **Rayon Spectral ($\rho$)** | Valeur propre dominante de la matrice. | Indique la force des corridors de transit. Plus $\rho$ est grand, plus la ville est "autoroutière" et hiérarchisée. |
| **Indice de Kreiss ($K$)** | Borne supérieure de la résolvante. | **Le prédicteur de bouchons.** Si $K > 10$, le réseau est incapable de gérer les imprévus (travaux, pluie) sans créer de pics de CO2. |
| **Norme $H_\infty$** | Gain maximal stabilisé. | Le niveau de pollution "de base" inévitable dû à la simple géométrie des rues. |
| **Norme $H_2$** | Somme des carrés des réponses impulsionnelles. | La "mémoire" du réseau. Une $H_2$ élevée signifie que la pollution met des heures à s'évacuer après l'heure de pointe. |

## 3. Analyse Différentielle : Cas d'Écoles

### 🏆 Cas A : Le Réseau "Respirant" (Ex: Berlin simplifié)
- **Topologie** : Grille régulière, multiples chemins alternatifs.
- **Résultat Spectral** : Rayon spectral $\rho \approx 1$. Indice de Kreiss faible.
- **Interprétation** : La pollution est diffuse. L'IA prédira des émissions stables car le réseau "digère" bien le flux.

### ⚠️ Cas B : Le Réseau "Goulot" (Ex: Monaco, Collines)
- **Topologie** : Convergence vers un unique tunnel ou pont.
- **Résultat Spectral** : $\rho > 5$. Indice de Kreiss explose ($> 100$).
- **Interprétation** : Instabilité structurelle. L'IA doit prédire des pics de pollution exponentiels dès que le volume de véhicules dépasse un seuil critique.

## 4. Synergie avec l'Intelligence Artificielle (Roadmap)

L'objectif final est de remplacer les simulations SUMO (très lentes, plusieurs heures) par une **prédiction IA instantanée**.

### Phase 1 : Extraction de Features (En cours)
Nous extrayons les signatures spectrales de 20 villes. C'est l'ADN de la ville.
- **Vecteur d'entrée IA** : `[nodes, edges, rho, K, H2, H_inf, avg_degree]`

### Phase 2 : Apprentissage Transversal (Cross-City)
L'IA apprend à reconnaître que :
- Ville A (Simulée) + Signature X = Pollution Y.
- Ville B (Inconnue) + Signature X' (proche de X) $\rightarrow$ **L'IA en déduit la Pollution Y' sans simulation.**

### Phase 3 : Aide à la Décision
En modifiant virtuellement une rue (suppression d'un sens unique), l'IA calcule instantanément le nouveau Spectres et dit : *"Attention, cette modification augmente l'indice de Kreiss, vous allez créer un nouveau point noir de CO2."*

---
*Document de référence pour le moteur de prédiction IA Pollution | 2026*
