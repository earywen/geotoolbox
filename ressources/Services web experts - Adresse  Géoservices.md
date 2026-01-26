![République française](https://geoservices.ign.fr/themes/custom/ignpro/images/svg/logo-rf.svg) [![Accueil](https://geoservices.ign.fr/themes/custom/ignpro/logo.svg)](https://geoservices.ign.fr/ "Accueil")

1.  [ACCUEIL](https://geoservices.ign.fr/)
2.  [SERVICES WEB](https://geoservices.ign.fr/services-web)
3.  Services web experts - Adresse

Contenu

Texte

La thématique "adresse" des services web experts comprend :

-   les données Adresse provenant de la BAN, les flux sont actualisés chaque semaine
-   les données « BAN PLUS » permettant l’association des points adresse de la BAN avec les éléments bâti, parcelles, et voies de la BD TOPO<sup>®</sup>. Ces données sont actualisées trimestriellement en synchronisation avec la publication de la BD TOPO<sup>®</sup>.

Les ressources présentées dans cette page sont utilisables via l'**URL** indiquée pour chaque protocole.

## 

Titre

Données "adresse" en WMS Vecteur

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wms-v/ows?service=wms&version=1.3.0&request=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique adresse (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wms-v/adresse.xml
```

Liste des données :

| Donnée | Nom technique |
| --- | --- |
| Base Adresse Nationale **BAN** (DATA.GOUV.FR) | BAN.DATA.GOUV |

## 

Titre

Données "adresse" en WFS

Texte

Les caractéristiques du service sont accessibles via l'URL suivante :

```
https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities
```

Nous proposons également une URL d'accès aux données filtrés sur la thématique adresse (attention cette URL ne fonctionne pas avec toutes les applications) :

```
https://data.geopf.fr/annexes/ressources/wfs/adresse.xml
```

Liste des données :

| Donnée | Nom technique |
| --- | --- |
| Base Adresse Nationale **BAN** (DATA.GOUV.FR) | BAN.DATA.GOUV:ban |
| BAN PLUS Lien adresse | BAN-PLUS:adresse |
| BAN PLUS Lien adresse\_bati | BAN-PLUS:lien\_adresse\_bati |
| BAN PLUS Lien adresse\_parcelle | BAN-PLUS:lien\_adresse\_parcelle |
| BAN PLUS Lien adresse\_support | BAN-PLUS:lien\_adresse\_support |
| BAN PLUS Lien bati\_parcelle | BAN-PLUS:lien\_bati\_parcelle |