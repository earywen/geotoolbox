# Changelog - Burgeaply Hub

## [2.1.0] - 2026-01-17 (Fort Knox Update)
### Added
- **Sécurité Renforcée** : 
  - Protection contre le "Path Traversal" dans le chargement des templates.
  - Vérification SSL stricte activée par défaut (configurable via `config.json`).
  - Validation des variables d'environnement au démarrage (`scripts/check_env.py`).
- **Tests** : 
  - Couverture de code à 100% sur les modules critiques (`modules/core.py`, `modules/geotoolbox.py`, `modules/orthohisto.py`).
  - Architecture découplée via `UIAdapter` facilitant les tests sans interface graphique.

### Changed
- **AutoLabo** : Migration complète vers une architecture modulaire (`GenericLabProcessor`). Suppression du code legacy Eurofins/Carso.
- **Fiabilité** : Validation stricte des fichiers Excel en entrée avec messages d'erreurs explicites pour l'utilisateur.
- **Performance** : Optimisation du chargement de l'application.

## [2.0.0] - 2025-12-23 (Glassmorphism UI)
### Added
- **Refonte UI v2** : Interface Glassmorphism complète (Dark Mode, Transparence).
- **Style Modernisé** : Bento Grid, animations fluides et typographie épurée.
- **Module GéoToolbox** : Outils de cartographie BSS/SSP.
- **Module Chronologie** : Extraction historique des cartes IGN.

### Changed
- **Architecture** : Séparation stricte HTML/CSS/JS. Templates externes.
