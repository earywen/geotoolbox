Texte

Ces services permettent de consulter ou sélectionner les données hébergées sur la Géoplateforme.

Texte

Ce service s'appuie sur le protocole WMTS en version 1.0.0

Il permet un affichage rapide d'images précalculées dans un format, un système de référence et des niveaux de zoom prédéfinis.

Il propose les méthodes suivantes :

-   **GetCapabilities** pour obtenir les métadonnées du service
-   **GetTile** pour obtenir une tuile
-   **GetFeatureInfo** pour obtenir les métadonnées d'une tuile

### Requête GetCapabilities

```
https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities
```

La requête a pour caractéristiques :

-   Paramètres obligatoires :
    -   SERVICE=WMTS
    -   REQUEST=GetCapabilities
    -   VERSION=1.0.0
-   Méthode possible : GET
-   Format de réponse : XML

### Requête GetTile

```
https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER={Couche}&STYLE={Style}&FORMAT={format}&TILEMATRIXSET={TileMatrixSet}&TILEMATRIX={TileMatrix}&TILEROW={TileRow}&TILECOL={TileCol}
```

La requête a pour caractéristiques :

-   Paramètres obligatoires :
    -   SERVICE=WMTS
    -   REQUEST=GetTile
    -   VERSION=1.0.0
    -   LAYER : la donnée consultée)
    -   STYLE : le style de rendu à appliquer)
    -   FORMAT
    -   TILEMATRIXSET : le nom de la pyramide d’images
    -   TILEMATRIX : le nom de la matrice qui contient la tuile
    -   TILEROW : le numéro de ligne du coin supérieur gauche de la tuile
    -   TILECOL : le numéro de colonne du coin supérieur gauche de la tuile
-   Méthode possible : GET
-   Format de réponse : dépend du format de la donnée (PNG, JPEG, TIFF, BIL...)

### Requête GetFeatureInfo

```
https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetFeatureInfo&VERSION=1.0.0&LAYER={Couche}&STYLE={Style}&FORMAT={Format}&I={abscisse}&J={ordonnée}&INFOFORMAT={format} 
```

La requête a pour caractéristiques :

-   Paramètres obligatoires :
    -   SERVICE=WMTS
    -   REQUEST=GetFeatureInfo
    -   VERSION=1.0.0
    -   I : abscisse d’un point dans l’image en pixels
    -   J : ordonnée d’un point dans l’image en pixels
    -   INFOFORMAT
    -   LAYER : la couche demandée
    -   STYLE : le nom d’un style de rendu de la couche à appliquer
    -   FORMAT
-   Méthode possible : GET

Texte

Ce service s'appuie sur le protocole TMS en version 1.0.0

Il permet un affichage rapide d'images précalculées, avec la possibilité de personnaliser l'affichage grâce à des légendes et à des filtres.

Il propose les méthodes suivantes :

-   Accès aux métadonnées du service
-   Accès aux métadonnées d'une donnée
-   Accès à une tuile

### Accès aux métadonnées du service

```
https://data.geopf.fr/tms/1.0.0
```

### Accès aux métadonnées d'une donnée

```
https://data.geopf.fr/tms/1.0.0/{Layer}/metadata.json
```

### Accès à une tuile

```
https://data.geopf.fr/tms/1.0.0/{Layer}/{z}/{x}/{y}.pbf
```

### Accès aux styles vectoriels

```
https://data.geopf.fr/annexes/ressources/vectorTiles/styles/{Layer}/{style}.json
```

L'IGN propose une [bibliothèque de styles disponible ici](https://geoservices.ign.fr/documentation/services/api-et-services-ogc/tuiles-vectorielles-tmswmts/styles).

Texte

Ce service s'appuie sur le protocole WMS en version 1.3.0

Il est limité à 40 requêtes/s.

Il permet un affichage d'images avec des possibilités de personnalisation (style, système de référence, emprise, format et taille d’image).

Il propose les méthodes suivantes :

-   **GetCapabilities** pour obtenir les métadonnées du service
-   **GetMap** pour obtenir une carte
-   **GetFeatureInfo** pour obetenir les métadonnées d'une carte

### Requête GetCapabilities

```
https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities
```

### Requête GetMap

```
https://data.geopf.fr/wms-r?LAYERS={couche}&FORMAT={format}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS={crs}&BBOX={Xmin,Ymin,Xmax,Ymax}&WIDTH={largeur}&HEIGHT={hauteur}
```

### Requête GetFeatureInfo

```
https://data.geopf.fr/wms-r?LAYERS={couche}&QUERY_LAYERS={donnée_requêtée}&INFO_FORMAT={format_de_sortie}&FORMAT={format}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&STYLES={style}&CRS={crs}&BBOX={Xmin,Ymin,Xmax,Ymax}&WIDTH={largeur}&HEIGHT={hauteur}&I={abscisse}&J={ordonnée}
```

Texte

Ce service s'appuie sur le protocole WMS en version 1.3.0

Il est limité à 50 requêtes/s.

Il permet un affichage d'images de données vectorielles avec des possibilités de personnalisation (style, système de référence, emprise, format et taille d’image).

Il propose les méthodes suivantes :

-   **GetCapabilities** pour obtenir les métadonnées du service
-   **GetMap** pour obtenir une carte
-   **GetFeatureInfo** pour obetenir les métadonnées d'une carte

### Requête GetCapabilities

```
https://data.geopf.fr/wms-v/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities
```

### Requête GetMap

```
https://data.geopf.fr/wms-v/ows?LAYERS={couche}&FORMAT={format}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES={style}&CRS={crs}&BBOX={Xmin,Ymin,Xmax,Ymax}&WIDTH={largeur}&HEIGHT={hauteur}
```

### Requête GetFeatureInfo

```
https://data.geopf.fr/wms-v/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&FORMAT={format}&QUERY_LAYERS={donnée_requêtée}&LAYERS={couche}&INFO_FORMAT={format_de_sortie}&I={abscisse}&J={ordonnée}&CRS={crs}&STYLES={style}&WIDTH={largeur}&HEIGHT={hauteur}&BBOX={Xmin,Ymin,Xmax,Ymax}
```

Texte

Ce service s'appuie sur le protocole WFS en version 2.0.0

Il est limité à 30 requêtes/s.

Il permet la récupération d'extraits de bases de données via des requêtes fondées sur des critères et valeurs.

Il propose les méthodes suivantes :

-   **GetCapabilities** pour obtenir les métadonnées du service
-   **DescribeFeatureType** pour obtenir la description de la structure d'une donnée
-   **GetFeature (hits)** pour obtenir le nombre d'objets associés à une demande
-   **GetFeature (results)** pour obtenir les objets associés à une demande

### Requête GetCapabilities

```
https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities
```

### Requête DescribeFeatureType

```
https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=DescribeFeatureType&TYPENAMES={classes}&OUTPUTFORMAT={format_de_sortie}
```

### Requête GetFeature (hits)

```
https://data.geopf.fr/wfs/ows?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&TYPENAMES={classes}&RESULTTYPE=hits
```

### Requête GetFeature (results)

```
https://data.geopf.fr/wfs/ows?SERVICE=WFS&TYPENAMES={classes}&REQUEST=GetFeature&VERSION=2.0.0
```

La bascule entre le Géoportail et la Géoplateforme entraîne des différences dans les réponses WFS. Certains éléments de vos requêtes peuvent être impactés. [Plus d’informations](https://geoservices.ign.fr/documentation/flux-wfs-les-changements-entre-geoservices-et-geoplateforme)