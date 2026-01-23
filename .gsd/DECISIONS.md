# DECISIONS.md — Architecture Decision Records

> Log des décisions techniques importantes du projet

---

## ADR-001: Fusion des modules GéoToolbox et OrthoHisto

**Date:** 2026-01-23  
**Status:** Accepted  
**Deciders:** Laurent BRIGAUD

### Context

L'application Burgeaply possède deux modules distincts pour les données géospatiales :
- **GéoToolbox** : Extraction de données vectorielles (BSS, BDLisa, SSP)
- **OrthoHisto** : Extraction de photos aériennes historiques (PVA, mosaïques IGN)

Ces deux modules partagent un workflow similaire (sélection zone → extraction → export) mais nécessitent deux onglets séparés dans l'UI.

### Decision

Fusionner les deux modules en un seul module **"Cartographie"** offrant :
- Une interface unifiée
- Un export complet (vecteurs + rasters) dans un seul dossier
- Un projet QGIS prêt à l'emploi

### Rationale

1. **UX simplifiée** : L'utilisateur fait un seul export au lieu de deux
2. **Cohérence métier** : Les données vectorielles et les photos aériennes font partie du même contexte d'étude
3. **Export prêt à l'emploi** : Le dossier généré est immédiatement utilisable dans QGIS
4. **Argument dépendances invalidé** : L'application est compilée en .exe standalone, donc pas de souci de taille de dépendances

### Consequences

- [+] Meilleure expérience utilisateur
- [+] Moins de navigation entre onglets
- [+] Export plus complet
- [-] Refactoring significatif du code
- [-] Complexité accrue du module Cartographie

---

## ADR-002: Ajout du dessin de polygone pour l'emprise du site

**Date:** 2026-01-23  
**Status:** Accepted  
**Deciders:** Laurent BRIGAUD

### Context

Actuellement, la zone d'étude est définie par un rectangle (bbox) sur la carte. Pour les sites d'études environnementales, l'emprise réelle est souvent un polygone irrégulier.

### Decision

Ajouter la possibilité de dessiner un polygone libre via **Leaflet.Draw**, en plus du mode rectangle existant.

### Rationale

1. **Précision** : L'emprise réelle du site est mieux représentée
2. **Export SIG** : Le polygone est exporté en GeoJSON, prêt pour QGIS
3. **UX standard** : Leaflet.Draw est un pattern connu des utilisateurs SIG

### Consequences

- [+] Emprise précise exportable
- [+] Intégration native avec le workflow QGIS
- [-] Légère complexité UI additionnelle
- [-] Dépendance JS supplémentaire (Leaflet.Draw via CDN)

---

## Template pour futures décisions

```markdown
## ADR-XXX: [Titre]

**Date:** YYYY-MM-DD  
**Status:** Proposed | Accepted | Deprecated | Superseded  
**Deciders:** [Noms]

### Context
[Quel est le problème ou la situation ?]

### Decision
[Quelle décision a été prise ?]

### Rationale
[Pourquoi cette décision ?]

### Consequences
[Quels sont les impacts positifs et négatifs ?]
```
