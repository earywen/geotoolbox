---
phase: 3
plan: 4
wave: 1
---

# Plan 3.4: Refonte Logique Zone d'Étude (Polygone + Rayon)

## Objective

Modifier l'UX pour que l'utilisateur définisse TOUJOURS son site par un polygone, puis définisse un rayon de recherche autour du centre de ce polygone.

## Changes

### 1. UI (cartographie.html)
- Supprimer les boutons Toggle Mode (Cercle/Polygone).
- Le slider "Rayon" reste visible en permanence.
- Changer le libellé pour "Rayon de recherche (autour du centre)".

### 2. Logique JS (cartographie.js)
- `init()` : Initialiser les contrôles de dessin par défaut (polygone/rectangle).
- `onDrawCreated` :
  1. Enregistrer le polygone (Emprise Site).
  2. Calculer le centroïde (Centre).
  3. Dessiner un cercle de recherche autour du centre avec le rayon actuel.
  4. Mettre à jour `selectedLat/Lon` avec le centroïde.
- `updateRadius()` : Mettre à jour le cercle autour du centroid existant.
- `getCurrentBbox()` : Retourner la BBOX du CERCLE DE RECHERCHE (pas du polygone site).
- `runExport()` : Envoyer la BBOX du cercle pour la recherche, mais le GeoJSON du polygone pour l'emprise.

## Workflow Utilisateur
1. Carte vide au départ.
2. User utilise les outils de dessin (carré/polygone) pour délimiter le site.
3. Dès que le dessin est fini -> Un cercle bleu (zone de recherche) apparaît autour.
4. User peut ajuster le rayon avec le slider.
5. User lance l'extraction -> Le backend cherche dans le cercle, mais exporte le polygone comme emprise.

## Tasks

<task type="auto">
  <name>Mettre à jour cartographie.html</name>
  <files>assets/templates/cartographie.html</files>
  <action>
    - Supprimer la div `mode-toggle`.
    - Supprimer la classe `hidden` conditionnelle sur `radiusContainer`.
    - Modifier les textes d'aide.
  </action>
</task>

<task type="auto">
  <name>Refondre cartographie.js</name>
  <files>assets/js/cartographie.js</files>
  <action>
    - Supprimer `currentMode` et `setMode`.
    - Activer `initDrawControls` dès le `init()`.
    - Modifier le handler `L.Draw.Event.CREATED` :
      - Sauvegarder polygone.
      - Calculer centroid.
      - Appeler `updateSiteSelection(centroid)`.
    - Modifier `updateRadiusVisuals` :
      - Toujours dessiner le cercle si un centre est défini.
  </action>
</task>
