## Les principes

  

-   L’API Carto est une API Rest compatible avec la spécification OpenAPI.
-   Le format utilisé est JSON/GeoJSON
-   La projection utilisée est WGS84 (coordonnées en longitude,latitude)
-   Les API offrent des opérations génériques de filtrage simple:
    -   Par attribut sous la forme (?nom\_attribut=valeur)
    -   Par intersection géométrique (?geom=géométrie GeoJSON)

Remarques :

-   Les croisements de données métiers sont réalisés côté client (croisements de données = appels successifs aux API)
-   Les traitements géométriques métiers (calcul de surface, filtrage des résultats, etc.) sont réalisés côté client à l'aide de bibliothèques de calcul géométrique

## Les modules

  

| Module | Description |  |
| --- | --- | --- |
| Cadastre | API d'accès aux données cadastrales (commune, division, parcelle, etc.) | [API](https://apicarto.ign.fr/api/doc/cadastre) |
| Limites Administratives | API de récupération des données administratives (commune, département, région) | [API](https://apicarto.ign.fr/api/doc/limites-administratives) |
| Codes Postaux | API de récupération des communes en fonction d'un code postal | [API](https://apicarto.ign.fr/api/doc/codes-postaux) |
| Urbanisme (GpU) | API d'accès aux données du géoportail de l'urbanisme (PLU, POS, CC, PSMV, SUP) | [API](https://apicarto.ign.fr/api/doc/gpu) |
| RPG | API d'accès aux données RPG | [API](https://apicarto.ign.fr/api/doc/rpg) |
| WFS-Geoportail | API d'accès à n'importe quel flux WFS du Géoportail | [API](https://apicarto.ign.fr/api/doc/wfs-geoportail) |
| Nature | API d'accès aux flux WFS Géoportail s'appuyant sur des données du MNHN | [API](https://apicarto.ign.fr/api/doc/nature) |

## Les sources de données

| Source | Version | Modules | Plus d'information |
| --- | --- | --- | --- |
| Géoplateforme | Flux WFS | Cadastre  
RPG  
Nature  
WFS-Geoportail  
 | [Geoservices](https://geoservices.ign.fr/services-web-experts) |
| GPU | Flux WFS | GPU  
 | [Géoportail de l'urbanisme](https://www.geoportail-urbanisme.gouv.fr/) |
| Base adresse nationale | v4.1.2 | Codes Postaux  
 | [BAN](https://github.com/baseadressenationale/codes-postaux) |

**Remarques** :

-   Version=flux traduit généralement une mise à jour en continue
-   API Carto conserve la licence des sources de données

## A voir aussi...

### Les bibliothèques JavaScript

Les bibliothèques ci-après sont complémentaires à API Carto :

-   Les bibliothèques de **calcul géométrique** peuvent être utilisées en amont et en aval des appels aux API pour calculer des surfaces, des unions de géométrie, calcul d'intersection, etc.
-   Les bibliothèques de **représentation cartographique** permettent de visualiser et d'éditer les données en entrée et sortie des API.
-   Les bibliothèques d'**accès à des services et des données** apportent des fonctionnalités complémentaires à API Carto

| Nom | Type | Description |
| --- | --- | --- |
| [turfjs](http://turfjs.org/) | Calcul géométrique | Permet de réaliser des calculs géométriques simples sur les données GeoJSON (bbox, surface, intersection, etc.) |
| [jsts](https://bjornharrtell.github.io/jsts/) | Calcul géométrique | Portage de JTS en JavaScript qui permet de réaliser des calculs géométriques avancés (zones tampons, etc.). C'est sensiblement le même moteur de calcul que celui de postgis. |
| [geoportal-access-lib](https://github.com/IGNF/geoportal-access-lib#biblioth%C3%A8que-dacc%C3%A8s-aux-ressources-du-g%C3%A9oportail) | Accès aux services/données | Bibliothèque simplifiant l'accès aux services du géoportail (géocodage, calcul d'itinéraire, calcul d'isochrones, etc.) |
| [geoportal-wfs-client](https://github.com/IGNF/geoportal-wfs-client#geoportal-wfs-client) | Accès aux services/données | Bibliothèque simplifiant l'accès aux services WFS du géoportail (API Carto générique sous forme d'un client JavaScript) |
| [openlayers](https://openlayers.org/) | Réprésentation cartographique | Bibliothèque cartographique JavaScript |
| [leaflet](http://leafletjs.com/) | Réprésentation cartographique | Bibliothèque cartographique JavaScript |
| [axios](https://github.com/axios/axios#example) | Utilitaire | Implémentation des requêtes HTTP sous forme de Promise (simplifie le chaînage des appels) |
| [bluebird](http://bluebirdjs.com/docs/getting-started.html) | Utilitaire | Implémentation des Promise JavaScript avec un support pour les différents navigateurs (simplifie les chaînages de requête et la gestion des exécutions en parallèle) |
| [proj4](https://github.com/proj4js/proj4js) | Tranformation géométrique | Bibliothèque JavaScript permettant de transformer des coordonnées géomtriques dans un autre référentiel |