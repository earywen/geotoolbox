---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Intégrer Leaflet.Draw dans l'application

## Objective

Ajouter la bibliothèque Leaflet.Draw pour permettre le dessin de polygones sur la carte. Le polygone dessiné servira d'emprise du site pour l'export.

## Context

- `assets/index.html` — Fichier principal, contient les CDN Leaflet
- `assets/js/cartographie.js` — Module JS à modifier
- `assets/templates/cartographie.html` — Template à modifier
- Leaflet.Draw CDN: https://unpkg.com/leaflet-draw

## Tasks

<task type="auto">
  <name>Ajouter les CDN Leaflet.Draw dans index.html</name>
  <files>assets/index.html</files>
  <action>
    Ajouter après les ressources Leaflet existantes :
    
    ```html
    <!-- Leaflet Draw -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css" />
    <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
    ```
    
    Placer APRÈS les scripts Leaflet de base (leaflet.js) mais AVANT app.js.
  </action>
  <verify>Select-String -Path "assets/index.html" -Pattern "leaflet-draw"</verify>
  <done>Les références Leaflet.Draw sont présentes dans index.html</done>
</task>

<task type="auto">
  <name>Ajouter les styles CSS pour les contrôles de dessin</name>
  <files>assets/templates/cartographie.html</files>
  <action>
    Ajouter dans la section <style> du template :
    
    ```css
    /* Draw Controls Customization */
    .leaflet-draw-toolbar a {
        background-color: rgba(30, 41, 59, 0.9) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    .leaflet-draw-toolbar a:hover {
        background-color: var(--accent) !important;
    }
    
    .emprise-info {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 8px;
        padding: 10px;
        margin-top: 10px;
        font-size: 12px;
        display: none;
    }
    
    .emprise-info.visible {
        display: block;
    }
    ```
  </action>
  <verify>Select-String -Path "assets/templates/cartographie.html" -Pattern "emprise-info"</verify>
  <done>Les styles pour les contrôles et l'info emprise sont ajoutés</done>
</task>

## Success Criteria

- [ ] Leaflet.Draw CSS et JS chargés dans index.html
- [ ] Styles personnalisés ajoutés au template
- [ ] Pas d'erreur console au chargement de la page
