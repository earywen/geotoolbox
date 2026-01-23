# SPEC.md — Project Specification

> **Status**: `FINALIZED`
> **Version**: 2.2.0 "Cartographie Unifiée"
> **Date**: 2026-01-23

---

## Vision

Unifier les modules **GéoToolbox** et **OrthoHisto** en un seul module **Cartographie** offrant une expérience utilisateur simplifiée : l'utilisateur définit l'emprise de son site (polygone libre ou bbox), sélectionne les données souhaitées (vecteurs + photos aériennes), et obtient un dossier d'export complet prêt à être importé dans QGIS.

---

## Goals

1. **Fusion des modules** : Combiner GéoToolbox et OrthoHisto en un module "Cartographie" unique
2. **Dessin de polygone** : Permettre à l'utilisateur de dessiner l'emprise exacte de son site d'étude
3. **Export unifié** : Produire un dossier complet avec vecteurs, rasters et projet QGIS prêt à l'emploi
4. **UX simplifiée** : Un seul workflow au lieu de deux onglets séparés

---

## Non-Goals (Out of Scope)

- Migration vers un autre framework UI (on reste sur PyWebView)
- Ajout de nouvelles sources de données (ARIA, SSP supplémentaires) — phase ultérieure
- Édition des données après export (ce n'est pas un SIG)
- Mode serveur/multi-utilisateur

---

## Users

**Utilisateur principal** : Ingénieur environnement (GINGER BURGEAP)

**Workflow typique** :
1. Reçoit une mission avec une adresse/coordonnées
2. Lance Burgeaply, dessine l'emprise du site
3. Sélectionne les données pertinentes (BSS, aquifères, SSP, photos historiques)
4. Exporte tout dans un dossier
5. Ouvre dans QGIS → toutes les couches sont déjà configurées

---

## Constraints

### Techniques
- **Backend** : Python 3.13, PyWebView 6.1
- **Frontend** : HTML/CSS/JS avec Leaflet.js
- **Compatibilité** : Windows 10/11 (packaging PyInstaller)
- **Dépendances** : Pas de nouvelles dépendances majeures (Leaflet.Draw est un plugin JS léger)

### Performance
- Les téléchargements PVA restent parallélisés (ThreadPoolExecutor)
- Les requêtes WFS doivent rester sous 30s de timeout

### Rétrocompatibilité
- Les anciens exports (GéoToolbox seul) doivent rester possibles via options
- La structure des fichiers Excel ne change pas

---

## Success Criteria

- [ ] Un seul onglet "Cartographie" remplace GéoToolbox + OrthoHisto
- [ ] L'utilisateur peut dessiner un polygone libre sur la carte
- [ ] L'emprise dessinée est exportée en GeoJSON avec le reste des données
- [ ] L'export génère un dossier structuré avec vecteurs, rasters, et Excel
- [ ] Un projet QGIS (.qgz) optionnel peut être généré automatiquement
- [ ] Les tests existants passent (100% coverage maintenue sur core)
- [ ] Documentation utilisateur mise à jour

---

## Technical Overview

### Architecture cible

```
modules/
├── cartographie.py                  # Module unifié (orchestrateur)
├── cartographie_core/
│   ├── __init__.py
│   ├── config.py                    # Configuration couches (fusion)
│   ├── vector_fetcher.py            # Requêtes WFS (ex-geotoolbox)
│   ├── vector_export.py             # Export Excel/GeoJSON
│   ├── raster_fetcher.py            # WMS/PVA (ex-orthohisto)
│   ├── raster_processor.py          # Traitement images (ex-pva_processor)
│   ├── maths.py                     # Calculs géométriques
│   ├── models.py                    # Modèles de données
│   └── parsers.py                   # Parsing XML/JSON
├── qgis_export/                     # Inchangé
│   ├── geojson_writer.py
│   ├── project_generator.py         # Mise à jour pour emprise
│   └── worldfile_writer.py
└── [anciens fichiers supprimés après migration]
```

### Frontend

```
assets/
├── js/
│   ├── app.js
│   └── cartographie.js              # Fusion geotoolbox.js + orthohisto.js
├── templates/
│   └── cartographie.html            # Nouveau template unifié
└── css/style.css                    # Styles pour Leaflet.Draw
```

### Dépendances JS additionnelles

- **Leaflet.Draw** : Plugin pour dessin de polygones (CDN)

---

## Risks & Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Régression fonctionnelle | Élevé | Tests exhaustifs avant suppression anciens modules |
| Performance dégradée | Moyen | Profiling avant/après fusion |
| Complexité UI accrue | Moyen | Design itératif avec feedback utilisateur |
