# Rapport d'Excellence Spectrale : Marseilles


## Synthèse de l'Interprétation Mathématique

### 1. Analyse du Rayon Spectral ($\rho = 3.4641$)
$\rho > 1$ indique un système structurellement instable. Dans votre graphe routier, cela traduit l'existence de **corridors dominants** et une structure très hiérarchisée où les flux sont asymétriques. C'est un facteur de fragilité majeur.

### 2. Amplification Maximale ($\sigma_{max} = 3.4641$)
Le fait que $\sigma_{max} \approx \rho$ signifie que l'amplification maximale instantanée est alignée avec la direction dominante. La majorité des trajets "efficaces" passent par les mêmes arcs, traduisant une **faible redondance** des itinéraires.

### 3. Normes et Énergie (Système Discrete)
- **Norme $H_\infty = 3.4641$** : Le pire cas entrée-sortie est purement topologique. SUMO va congestionner là où la structure l’impose.
- **Norme $H_2 = 21.0950$** : Très élevée par rapport à $H_\infty$. Le réseau **stocke de l'énergie** de perturbation, ce qui mène à une congestion diffuse et persistante.

### 4. Indice de Kreiss ($K = 37.4166$)
C'est le signal le plus critique. Avec $K \gg \sigma_{max}$, la **non-normalité** est massive. Le système peut amplifier une perturbation locale de manière disproportionnée (effet papillon), provoquant des explosions transitoires de congestion.

## Identification du Secteur Critique (Pivot de Perron-Frobenius)
- **Rue Critique** : **-558848783#0** (ID: `-558848783#0`)
- **Poids Spectral** : 0.571097
- **Action Recommandée** : Casser la non-normalité sur cet axe (pénalisation des hubs dominants, splitting d'arcs).


---
*Document de recherche confidentiel | Urban Topology Lab*
