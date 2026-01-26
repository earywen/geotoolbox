1.  [ACCUEIL](https://geoservices.ign.fr/)
2.  [SERVICES WEB](https://geoservices.ign.fr/services-web)
3.  Services web "découverte"

Contenu

Texte

### Accéder gratuitement et librement à Plan IGN et aux Photographies aériennes dans votre site web ou application

Texte

Avec nos **URL** prêtes à l'emploi, accédez à deux ressources emblématiques de nos services web : Plan IGN et Photographies aériennes, sous la forme de flux d'images, de façon gratuite et sans inscription, dans votre site web ou dans l'application de votre choix.

Image

Image

![Services web "découverte" - WMTS](https://geoservices.ign.fr/sites/default/files/2021-07/decouverte_wmts.png)

## 

Titre

Service d'images tuilées WMTS

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique decouverte (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wmts/decouverte.xml
```

Image

Image

![Plan IGN via la clé pratique](https://geoservices.ign.fr/sites/default/files/2021-05/pratique_150253.png)

Texte

Un fond cartographique IGN complet, représentant avec précision et lisibilité la France de l'échelle monde au 1 : 1 000 environ, tout en proposant un contenu cartographique riche à grande échelle, notamment en zone urbaine.

Nom technique de la ressource :

```
GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2<!-- Plan IGN --> 
```

Image

Image

![Photographies aériennes via la clé pratique](https://geoservices.ign.fr/sites/default/files/2021-05/pratique_909.jpg)

## 

Titre

Donnée "Photographies aériennes"

Texte

L'image géographique du territoire national, la France vue du ciel, composée d'un assemblage de prises de vues aériennes et d'images satellites.

Nom technique de la ressource :

```
ORTHOIMAGERY.ORTHOPHOTOS<!-- Photographies aériennes -->
```

## 

Titre

Exemple d'utilisation avec l'API cartographique "Leaflet"

Texte

[Leaflet](http://leafletjs.com/ "A JS library for interactive maps") | Carte © IGN/Geoplateforme

Texte

Cet exemple permet de consulter les photographies aériennes sur lesquelles Plan IGN se superpose en transparence.

Vous trouverez, ci-dessous, le code HTML de cet exemple.

Pour l'utiliser, il vous suffit d'en copier le contenu dans un fichier HTML (par exemple "geoservices.html") et d'ouvrir ce fichier dans votre navigateur internet.

```
<html>
<head>
    <title>Géoservices - Carte simple</title>
    <meta charset="utf-8" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.3.1/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.3.1/dist/leaflet.js"></script>
</head>
<body>
<div id="map" style="width: 100%; height: 400px;"></div>
    <!-- Leaflet map JavaScript -->
    <script>
        // L'id du container, par exemple <div id="map"></div>
        var mapID = 'map';

        // Plan IGN avec une transparence de 50%
        var PlanIGN = L.tileLayer('https://data.geopf.fr/wmts?'+
            '&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&TILEMATRIXSET=PM'+
            '&LAYER={ignLayer}&STYLE={style}&FORMAT={format}'+
            '&TILECOL={x}&TILEROW={y}&TILEMATRIX={z}',
            {
            ignLayer: 'GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2',
            style: 'normal',
            format: 'image/png',
            service: 'WMTS',
                opacity: 0.4,
                attribution: 'Carte © IGN/Geoplateforme'
        });

// Photographies aériennes en-dessous de Plan IGN
var OrthoIGN = L.tileLayer('https://data.geopf.fr/wmts?'+
            '&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&TILEMATRIXSET=PM'+
            '&LAYER={ignLayer}&STYLE={style}&FORMAT={format}'+
            '&TILECOL={x}&TILEROW={y}&TILEMATRIX={z}',
            {
            ignLayer: 'ORTHOIMAGERY.ORTHOPHOTOS',
            style: 'normal',
            format: 'image/jpeg',
            service: 'WMTS'
        });
        // Ma carte
        var myMap = L.map(mapID, {
        center: [48.8456,2.4245],
        zoom: 15,
        layers: [OrthoIGN,PlanIGN]
        })
    </script>
</body>
</html>
```

## 

Titre

Exemple d'utilisation avec le SIG "QGIS"

Texte

Deux options sont possibles :

-   Télécharger **[ce fichier](https://geoservices.ign.fr/sites/default/files/2025-02/Decouverte.qgs)** permettant en clic d'ouvrir les flux "découverte" sous QGIS.
-   Suivre le tutoriel ci-dessous :

Pour ajouter une donnée dans le système d'information géographique QGIS :

1\. Ouvrir QGIS, sélectionner le menu **Couche** et sélectionner **Ajouter une couche** puis **Ajouter une couche WMS/WMTS**.

![Services web découverte - QGIS - Ajouter une couche](https://geoservices.ign.fr/sites/default/files/inline-images/decouverte_QGIS_1.png)

2\. Donner un nom à la couche (ici "GPF-WMTS-Decouverte") et saisir l'URL d'accès **https://data.geopf.fr/annexes/ressources/wmts/decouverte.xml**

![Services web découverte - QGIS - Paramétrer la couche](https://geoservices.ign.fr/sites/default/files/inline-images/GPF-WMTS-Decouverte.png)

![Services web découverte - QGIS - Choisir la donnée](https://geoservices.ign.fr/sites/default/files/inline-images/decouverte_QGIS_3.png)

3\. La carte s'affiche munie de la donnée sélectionnée.

![Services web découverte - QGIS - Afficher la donnée](https://geoservices.ign.fr/sites/default/files/inline-images/decouverte_QGIS_4.png)

## 

Titre

Utiliser les services web dans votre application

Contenu

### Images Tuilées - WMTS (OGC)

Vignette

Image

![Defaut_Documentation](https://geoservices.ign.fr/sites/default/files/styles/vignette_200x200_/public/2021-04/Defaut_Documentation.png?itok=yeQuFMdD)

### Utilisation Web

Vignette

Image

![Defaut_Documentation](https://geoservices.ign.fr/sites/default/files/styles/vignette_200x200_/public/2021-04/Defaut_Documentation.png?itok=yeQuFMdD)

### Utilisation SIG

Vignette

Image

![Defaut_Documentation](https://geoservices.ign.fr/sites/default/files/styles/vignette_200x200_/public/2021-04/Defaut_Documentation.png?itok=yeQuFMdD)