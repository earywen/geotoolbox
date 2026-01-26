Texte

### Accéder gratuitement et librement à nos services web les plus fréquemment utilisés

Texte

Avec les URL prêtes à l'emploi filtrées sur les données **essentiels** de l'IGN, accédez à nos principaux services web, de façon gratuite et sans inscription, dans votre site web ou dans l'application de votre choix.

Plusieurs services (WMTS, WFS, etc.) sont proposés, répondant chacun à un besoin particulier.

Les [noms techniques des ressources](https://geoservices.ign.fr/services-web-essentiels#nomstechniques) des services web essentiels sont précisés en bas de page.

L'accès à des [tutoriels](https://geoservices.ign.fr/services-web-essentiels#tutoriels) d'utilisation dans des SIG ou API cartographiques complète cette page.

Image

Image

![Services WMTS essentiels](https://geoservices.ign.fr/sites/default/files/2021-06/choisirgeoportail_wmts.png)

## 

Titre

Services d'images tuilées WMTS

Texte

Une visualisation performante d'images géo-référencées.

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique essentiels (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wmts/essentiels.xml
```

Image

Image

![Services Vecteur Tuilé essentiels](https://geoservices.ign.fr/sites/default/files/2021-06/choisirgeoportail_VT.png)

## 

Titre

Service tuiles vectorielles

Texte

Un service de visualisation alliant performances et personnalisation.

La ressource Plan IGN est délivrée par le service accessible sur l'URL :

```
https://data.geopf.fr/tms/1.0.0/PLAN.IGN/metadata.json/
```

La ressource Admin EXPRESS est délivrée par le service accessible sur l'URL :

```
https://data.geopf.fr/tms/1.0.0/ADMIN_EXPRESS/metadata.json/
```

Image

Image

![Services WMS Raster essentiels](https://geoservices.ign.fr/sites/default/files/2021-06/choisirgeoportail_wms-r.png)

## 

Titre

Services d'image WMS Raster

Texte

Une visualisation paramétrable de données images.

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique essentiels (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wms-r/essentiels.xml
```

Image

Image

![Services WMS Vecteur essentiels](https://geoservices.ign.fr/sites/default/files/2021-06/choisirgeoportail_wms-v.png)

## 

Titre

Services d'image WMS Vecteur

Texte

Une visualisation paramétrable de données vectorielles.

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wms-v/ows?service=wms&version=1.3.0&request=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique essentiels (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wms-v/essentiels.xml
```

Image

Image

![WFS](https://geoservices.ign.fr/sites/default/files/2021-06/choisirgeoportail_wfs.png)

Texte

Pour des requêtes spatiales (sélection d’objets fondée sur des critères géographiques et des valeurs d’attributs des objets).

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique essentiels (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wfs/essentiels.xml
```

## 

Titre

Noms techniques des ressources

Texte

### Ressources WMTS

```
GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2<!-- Plan IGN -->
ORTHOIMAGERY.ORTHOPHOTOS<!-- Photographies aériennes -->
CADASTRALPARCELS.PARCELLAIRE_EXPRESS<!-- Parcelles cadastrales -->
```

### Ressources tuiles vectorielles

```
PLAN.IGN<!-- Plan IGN -->
ADMIN_EXPRESS<!-- Admin EXPRESS -->
```

### Ressources WMS Raster

```
IGNF_LIDAR-HD_MNH_ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW<!-- MNH issu de LiDAR HD -->
IGNF_LIDAR-HD_MNS_ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW<!-- MNS issu de LiDAR HD -->
IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW<!-- MNT issu de LiDAR HD -->
GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2<!-- Plan IGN -->
ORTHOIMAGERY.ORTHOPHOTOS<!-- Photographies aériennes -->
CADASTRALPARCELS.PARCELLAIRE_EXPRESS<!-- Parcelles cadastrales -->
LIMITES_ADMINISTRATIVES_EXPRESS.LATEST<!-- Admin Express -->
```

### Ressource WMS Vecteur

```
ORTHOIMAGERY.ORTHOPHOTOS.GRAPHE-MOSAIQUAGE<!-- Graphe de mosaïquage BD ORTHO® -->
```

### Ressources WFS

```
BDTOPO_V3:batiment<!-- BD TOPO®V3 - Bâtiment -->
BDTOPO_V3:troncon_de_route<!-- BD TOPO® V3 - Tronçon de route -->
CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle<!-- Parcellaire Express (PCI) - Parcelle -->
```

## 

Titre

Utiliser les services web dans votre application

Contenu

### Utilisation SIG

Vignette

Image

![Defaut_Documentation](https://geoservices.ign.fr/sites/default/files/styles/vignette_200x200_/public/2021-04/Defaut_Documentation.png?itok=yeQuFMdD)

### Utilisation Web

Vignette

Image

![Defaut_Documentation](https://geoservices.ign.fr/sites/default/files/styles/vignette_200x200_/public/2021-04/Defaut_Documentation.png?itok=yeQuFMdD)