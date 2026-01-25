# Brainstorming: Améliorations Techniques & Fonctionnelles

Document généré suite à l'analyse du code (`vector_fetcher.py`, `core.py`) et des ressources contextuelles (`OWSLib`).

## 1. Robustesse du client WFS (Priorité Haute)

Le module `vector_fetcher.py` construit actuellement les requêtes WFS "à la main" et parse le GML via des expressions régulières ou BeautifulSoup. Cette approche est fragile face aux changements de version WFS ou de format (GML vs JSON).

**Proposition : Migration vers `OWSLib`**
- **Pourquoi ?** : `OWSLib` est la librairie standard Python pour interagir avec les services OGC (WFS, WMS).
- **Avantages** :
  - Gestion automatique des versions WFS (1.0 vs 1.1 vs 2.0).
  - Parsing robuste des réponses GML sans "bricolage" XML.
  - Gestion native des filtres OGC (pas seulement BBOX).
- **Impact** : Remplacement de la logique manuelle dans `vector_fetcher.py`.

```python
from owslib.wfs import WebFeatureService
wfs = WebFeatureService(url, version='2.0.0')
response = wfs.getfeature(typename=layer_name, bbox=bbox)
# Le parsing est géré, plus besoin de REGEX complexes
```

## 2. Optimisation des Performances (Scraping & I/O)

L'application utilise `ThreadPoolExecutor` pour le scraping (BSS, SSP). C'est bien, mais `asyncio` + `aiohttp` serait nettement plus performant pour des centaines de requêtes, ou au moins l'utilisation d'une `Session` persistante plus agressivement configurée.

**Pistes :**
- **AsyncIO pour le Scraping** : Réécrire les fonctions `scrape_bss` et `scrape_ssp` pour utiliser `aiohttp`. Cela permet de traiter des centaines de fiches en parallèle sans bloquer sur les threads OS.
- **Cache Local (`joblib` ou `diskcache`)** : Mettre en cache les réponses WFS (pour une même emprise) et surtout les résultats de scraping (le niveau d'eau d'un piézomètre BSS change peu en 1h).

## 3. Qualité et Sécurité du Code

- **Validation des Données (`Pydantic`)** :
  - Actuellement, les objets (lignes) sont des dictionnaires peu typés.
  - Utiliser `Pydantic` pour définir des modèles (ex: `SiteBSS`, `SiteSSP`) garantirait que les champs attendus sont présents et du bon type.
- **Gestion des Erreurs unifiée** :
  - Remplacer les retours string `"Err HTTP"` par un système de gestion d'erreur plus formel ou des Enums de statut.

## 4. Expérience Utilisateur (Suggestions UI/UX)

- **Indicateurs de chargement prévisibles** : Avec `OWSLib` ou AsyncIO, on peut mieux estimer la progression.
- **Mode Hors-Ligne partiel** : Si le cache est implémenté, permettre de revoir les dernières données sans appel réseau.

---

## Intégration au Roadmap GSD

Ces améliorations s'insèrent logiquement dans ou après la **Phase 1 (Fondations Backend)** ou en tant que refonte technique dédiée (**Phase "Architecture V2"**).

### Actions suggérées pour immédiat :
1.  **POC OWSLib** : Créer un petit script pour valider qu' `OWSLib` récupère bien les données IGN/BRGM correctement.
2.  **Audit Performance** : Mesurer le temps actuel de fetch sur une grande zone pour justifier le passage à `AsyncIO`.
