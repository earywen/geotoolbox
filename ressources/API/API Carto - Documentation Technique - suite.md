## Module pour rechercher dans tous les flux WFS Géoportail ```
 2.10.0 
``` 

```
OAS 3.1
```

[wfs-geoportail.yml](https://apicarto.ign.fr/api/doc/wfs-geoportail.yml)

Ce module permet d’intersecter les couche WFS du géoportail. Un tri sémantique sur un attribut devra être fait en aval par l'application cliente. Toutes les requêtes du module peuvent se faire en POST ou en GET. Sur cette page, vous pouvez uniquement tester les modules avec des requêtes en GET.

Consultez la [documentation utilisateur](https://apicarto.ign.fr/api/doc/pdf/docUser_moduleWfsGeoportail.pdf) pour plus d’informations sur les paramètres d’appel disponibles et le format des résultats.

## Couche source

Les couches WFS disponibles sur le géoportail peuvent être listée via l’URL [https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities](https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities)

Le nom technique de la couche source doit être utilisé. Celui-ci est indiqué par la balise `<Name>`.

**Exemple pour le champ _source_** : BDTOPO\_V3:zone\_de\_vegetation

## Géométrie

La géometrie doit être exprimée en valeur décimale dans le référentiel WGS84

**Exemples de géométrie** : (référentiel EPSG:4326)

-   Point :
    
    `{"type": "Point","coordinates":[-1.691634,48.104237]}`
    
-   MultiPolygon :
    
    `{"type":"MultiPolygon","coordinates":[[[[-0.288863182067871,48.963666607295977],[-0.299592018127441,48.959299208576141],[-0.296330451965332,48.955325952385039],[-0.282125473022461,48.950675995388366],[-0.279722213745117,48.967019382922331],[-0.288863182067871,48.963666607295977]]]]}`
    
-   Polygone troué :
    
    `{"type":"Polygon","coordinates":[[[1.2,48.85],[1.3,48.85],[1.3,48.9],[1.2,48.9],[1.2,48.85]],[[1.23,48.86],[1.23,48.88],[1.26,48.88],[1.26,48.86],[1.23,48.86]]]}`
    
-   Linéaire :
    
    `{"type":"LineString","coordinates":[[4.681549,47.793784],[4.741974,47.788248]]}`
    

## Historique des changements

-   Utilisation des flux WFS de la geoplateforme
-   Suppression du paramètre _apikey_
-   Suppression des contraintes sur le nom de la géométrie et le CRS