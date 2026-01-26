![République française](https://geoservices.ign.fr/themes/custom/ignpro/images/svg/logo-rf.svg) [![Accueil](https://geoservices.ign.fr/themes/custom/ignpro/logo.svg)](https://geoservices.ign.fr/ "Accueil")

1.  [ACCUEIL](https://geoservices.ign.fr/)
2.  [SERVICES WEB](https://geoservices.ign.fr/services-web)
3.  Services web experts - Cartes

Contenu

Texte

La thématique "cartes" des services web experts comprend des données Plan IGN, PLAN IGN J+1, SCAN 1000®, SCAN Départemental®, SCAN Régional®, SCAN 50® 1950, Carte de l'état-major, Carte de Guyane, Carte de Paris de 1906, Mini-carte...

Les ressources présentées dans cette page sont utilisables via l'**URL** indiquée pour chaque protocole.

## 

Titre

Données "cartes" en WMTS

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique cartes (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wmts/cartes.xml
```

Liste des données :

| Donnée | Nom technique |
| --- | --- |
| Carte de Cassini | BNF-IGNF\_GEOGRAPHICALGRIDSYSTEMS.CASSINI |
| Carte de Guyane (1780 - Col Bonne) | GEOGRAPHICALGRIDSYSTEMS.BONNE |
| Carte de l'état-major 1 : 10 000 (Environs de Paris 1818-1824) | GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR10 |
| Carte de l'état-major 1 : 40 000 (1820-1866) | GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40 |
| Carte de Paris de 1906 | GEOGRAPHICALGRIDSYSTEMS.1900TYPEMAPS |
| Mini-carte | GEOGRAPHICALGRIDSYSTEMS.MAPS.OVERVIEW |
| PLAN IGN | GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2 |
| PLAN IGN J+1 | GEOGRAPHICALGRIDSYSTEMS.MAPS.BDUNI.J1 |
| Plan Terrier de Corse (XVIIIe siècle) V1 | GEOGRAPHICALGRIDSYSTEMS.TERRIER\_V1 |
| Plan Terrier de Corse (XVIIIe siècle) V2 | GEOGRAPHICALGRIDSYSTEMS.TERRIER\_V2 |
| SCAN 1000® | IGNF\_CARTES\_SCAN-1000 |
| SCAN Régional® | IGNF\_CARTES\_SCAN-REGIONAL |
| SCAN 50 Historique 1950 | GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN50.1950 |

## 

Titre

Données "cartes" en tuiles vectorielles

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/tms/1.0.0/PLAN.IGN/metadata.json/
```

Liste des données :

| Donnée | Nom technique |
| --- | --- |
| PLAN IGN | PLAN.IGN |

Vous pouvez accéder à la [documentation](https://geoservices.ign.fr/documentation/services/services-geoplateforme/diffusion#70064) des tuiles vectorielles et aux [fichiers de style](https://geoservices.ign.fr/documentation/services/api-et-services-ogc/tuiles-vectorielles-tmswmts/styles) associés.

## 

Titre

Données "cartes" en WMS Raster

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique cartes (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wms-r/cartes.xml
```

Liste des données :

| Donnée | Nom technique |
| --- | --- |
| Carte de Cassini | BNF-IGNF\_GEOGRAPHICALGRIDSYSTEMS.CASSINI |
| Carte de l'état-major 1 : 10 000 (Environs de Paris 1818-1824) | GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR10 |
| Carte de l'état-major 1 : 40 000 (1820-1866) | GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40 |
| PLAN IGN | GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2 |
| PLAN IGN J+1 | GEOGRAPHICALGRIDSYSTEMS.MAPS.BDUNI.J1 |
| Plan Terrier de Corse (XVIIIe siècle) V1 | GEOGRAPHICALGRIDSYSTEMS.TERRIER\_V1 |
| Plan Terrier de Corse (XVIIIe siècle) V2 | GEOGRAPHICALGRIDSYSTEMS.TERRIER\_V2 |
| SCAN 1000® | SCAN1000\_PYR-JPEG\_WLD\_WM |
| SCAN 50® 1950 | GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN50.1950 |
| SCAN Régional® | SCANREG\_PYR-JPEG\_WLD\_WM |

## 

Titre

Données "cartes" en WMS Vecteur

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wms-v/ows?service=wms&version=1.3.0&request=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique cartes (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wms-v/cartes.xml
```

Liste des données :

| Donnée | Nom technique |
| --- | --- |
| Graphe de mosaïquage SCAN 25 | GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25.GRAPHE-MOSAIQUAGE |

## 

Titre

Données "cartes" en WFS

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique cartes (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wfs/cartes.xml
```

Liste des données :

| Donnée | Nom technique |
| --- | --- |
| Graphe de mosaïquage SCAN 25 | GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25.GRAPHE-MOSAIQUAGE:graphe\_scan25 |
| Graphe de mosaïquage SCAN 50 1950 | GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN50.1950.GRAPHE:ta\_france\_cartes\_50k\_1950\_date\_wm |