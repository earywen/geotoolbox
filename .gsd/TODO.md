# TODO.md — Quick Capture

> Items à traiter plus tard (pas de phase assignée)

---

## À faire

- [ ] Vérifier si Leaflet.Draw supporte la mesure de surface automatique
- [ ] Décider du format de sauvegarde pour les "projets" futurs (JSON ? SQLite ?)
- [ ] Investiguer l'ajout de couches ARIA/ICPE (post-v2.2.0)

---

## Idées futures

- Mode multi-emprises (plusieurs sites dans un export)
- Génération de rapport PDF automatique
- Mode "projet" avec sauvegarde/chargement de paramètres
- Historique des exports récents

---

## Notes techniques

- Leaflet.Draw events: `draw:created`, `draw:edited`, `draw:deleted`
- GeoJSON CRS: Préférer EPSG:4326 pour compatibilité
- QGIS project (.qgz) est un ZIP contenant XML
