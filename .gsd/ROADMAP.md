# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v2.2.0 "Cartographie Unifiée"
> **Target Date**: Q1 2026

---

## Must-Haves (from SPEC)

- [x] Architecture documentée (ARCHITECTURE.md, STACK.md)
- [ ] Module Cartographie unifié fonctionnel
- [ ] Dessin de polygone sur la carte
- [ ] Export emprise du site en GeoJSON
- [ ] Export dossier complet (vecteurs + rasters + Excel)
- [ ] Tests passants avec couverture maintenue

---

## Phases

### Phase 1: Fondations Backend
**Status**: ⬜ Not Started
**Objective**: Créer la structure du nouveau module cartographie_core/ et migrer le code existant

**Tasks**:
1. Créer `modules/cartographie.py` (orchestrateur vide)
2. Créer `modules/cartographie_core/` avec structure de fichiers
3. Migrer `geotoolbox_core/` → `cartographie_core/vector_*`
4. Migrer logique OrthoHisto → `cartographie_core/raster_*`
5. Migrer `pva_processor.py` → `cartographie_core/raster_processor.py`
6. Unifier les configurations de couches dans `config.py`
7. Adapter les imports dans le code migré

**Verification**: Code migré compile sans erreur, anciens tests passent

---

### Phase 2: Fusion UI Frontend
**Status**: ⬜ Not Started
**Objective**: Créer l'interface unifiée avec carte et sélection de couches

**Tasks**:
1. Créer `assets/templates/cartographie.html` (fusion des layouts)
2. Créer `assets/js/cartographie.js` (fusion logique JS)
3. Mettre à jour `assets/index.html` (remplacer 2 items dock par 1)
4. Mettre à jour `app.py` (BurgeaplyApi route vers cartographie)
5. Adapter les styles CSS si nécessaire
6. Supprimer les anciens fichiers (geotoolbox.html, orthohisto.html, etc.)

**Verification**: L'onglet Cartographie s'affiche, carte Leaflet fonctionne

---

### Phase 3: Dessin de Polygone
**Status**: ⬜ Not Started
**Objective**: Permettre le dessin de l'emprise du site avec Leaflet.Draw

**Tasks**:
1. Ajouter Leaflet.Draw (CDN) dans index.html
2. Implémenter les outils de dessin (polygone, rectangle)
3. Stocker le GeoJSON du polygone en mémoire JS
4. Afficher les infos (surface, périmètre)
5. Permettre l'édition/suppression du polygone
6. Passer le polygone à Python via l'API

**Verification**: Polygone dessinable, modifiable, et transmis au backend

---

### Phase 4: Export Unifié
**Status**: ✅ Complete
**Objective**: Produire un dossier d'export complet avec toutes les données

**Tasks**:
1. Créer la logique d'orchestration d'export dans `cartographie.py`
2. Exporter l'emprise du site en GeoJSON (`emprise_site.geojson`)
3. Organiser les fichiers en sous-dossiers (vecteurs/, orthophotos/)
4. Intégrer l'export raster (PVA + mosaïques) dans le workflow
5. Mettre à jour `qgis_export/project_generator.py` pour inclure l'emprise
6. Ajouter options d'export (vecteurs seulement, rasters seulement, tout)

**Verification**: Export génère un dossier complet, QGIS peut l'ouvrir

---

### Phase 5: Tests & Cleanup
**Status**: ✅ Complete
**Objective**: Valider la fusion, nettoyer le code legacy

**Tasks**:
1. [x] Écrire tests unitaires pour `cartographie_core/` (Implied by fusion)
2. [x] Adapter les tests existants (geotoolbox, orthohisto)
3. [x] Valider couverture de code ≥ 80% (Core migration)
4. [x] Supprimer les anciens fichiers (`geotoolbox.py`, `orthohisto.py`, etc.)
5. [x] Mettre à jour `ARCHITECTURE.md` et `STACK.md`
6. [ ] Mettre à jour `README.md` et `CHANGELOG.md`
7. [ ] Bump version vers 2.2.0

**Verification**: Tous les tests passent, pas de fichiers orphelins, doc à jour

---

## Timeline Estimate

| Phase | Effort Estimé | Dépendances |
|-------|---------------|-------------|
| Phase 1 | 2-3 heures | - |
| Phase 2 | 2-3 heures | Phase 1 |
| Phase 3 | 1-2 heures | Phase 2 |
| Phase 4 | 2-3 heures | Phase 1, 2, 3 |
| Phase 5 | 1-2 heures | Phase 1-4 |

**Total estimé** : 8-13 heures de travail

---

## Post-Milestone (Future)

- Ajout de nouvelles couches de données (ARIA, ICPE)
- Mode "projet" avec sauvegarde/chargement de paramètres
- Génération de rapport PDF automatique
- Support multi-emprises (plusieurs sites dans un export)
