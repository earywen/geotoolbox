# JOURNAL.md — Development Journal

> Chronique des sessions de développement

---

## 2026-01-23 — Initialisation du projet GSD

**Durée:** ~30 min  
**Focus:** Mapping codebase + Planning fusion Cartographie

### Résumé

Session de planification pour la v2.2.0 "Cartographie Unifiée".

### Accomplissements

1. **Mapping complet** de l'application Burgeaply existante
   - 7 composants majeurs identifiés
   - 6 APIs externes documentées
   - 5 items de dette technique notés

2. **Discussion architecture** : Fusion GéoToolbox + OrthoHisto
   - Initialement hésitant (SRP, séparation des responsabilités)
   - Convaincu par l'argument UX et workflow unifié
   - Décision validée : module "Cartographie" unique

3. **Feature additionnelle** : Dessin de polygone
   - Idée de l'utilisateur pour la définition de l'emprise du site
   - Intégrée au scope via Leaflet.Draw
   - Export en GeoJSON inclus

4. **Documentation créée**
   - `ARCHITECTURE.md` — Structure et flux de données
   - `STACK.md` — Inventaire technologique
   - `SPEC.md` — Spécification finalisée
   - `ROADMAP.md` — 5 phases de développement
   - `DECISIONS.md` — ADRs pour les choix clés

### Décisions clés

| Décision | Rationale |
|----------|-----------|
| Fusionner GéoToolbox + OrthoHisto | UX simplifiée, export unifié |
| Ajouter dessin polygone | Emprise précise, export SIG-ready |
| Leaflet.Draw via CDN | Plugin léger, bien maintenu |

### Prochaine session

- Commencer Phase 1 : Fondations Backend
- Créer structure `cartographie_core/`
- Migrer le code existant

### Humeur

🚀 Projet bien cadré, vision claire. Let's go!

---

## Template pour futures entrées

```markdown
## YYYY-MM-DD — [Titre court]

**Durée:** X heures  
**Focus:** [Zone de travail]

### Résumé
[1-2 phrases]

### Accomplissements
- [Item 1]
- [Item 2]

### Blocages / Problèmes
- [Problème et solution]

### Prochaine session
- [Next step]

### Humeur
[Emoji + commentaire]
```
