1.  [ACCUEIL](https://geoservices.ign.fr/)
2.  [ACTUALITÉS](https://geoservices.ign.fr/actualites)
3.  Accès aux données non libres sur la Géoplateforme

Contenu

Texte

### Les données SCANs de l’IGN

L’Institut national de l’information géographique et forestière, établissement public de l’État à caractère administratif, immatriculé sous le numéro SIREN 180 067 019, dont le siège est au 73, avenue de Paris, 94160 SAINT-MANDÉ (ci-après « IGN ») produit et édite des données géographiques, dont le  
SCAN 25®, le SCAN 100® et le SCAN OACI, ainsi que différents outils et services géographiques permettant d’exploiter ces données.

Les données du SCAN 25®, du SCAN 100® et du SCAN OACI sont diffusées par l’IGN par différents moyens :

-   par lots prédéfinis de données téléchargeables sur le site geoservices.ign.fr ;
-   à travers les ressources en ligne accessibles par l’intermédiaire du site geoservices.ign.fr ;
-   sur support physique ou sur serveur FTP dédié.

**Les données SCAN 25®, SCAN 100® et SCAN OACI (et les services en lignes associés) ne sont pas libres de droit**, selon les termes de [la licence](https://geoservices.ign.fr/cgu-licences) les particuliers ne sont pas autorisés à les télécharger, même à des fins personnelles, sauf à se rendre contrefacteurs.

Ces conditions identifient notamment que sont soumis à de potentiels usages payants, d’une part les usages des données dans le cadre d’une offre à valeur ajoutée de produits ou services numériques gratuits ou payants destinés au marché grand public, d’autre part la reproduction des données sur un support imprimé ou sur un support graphique téléchargeable. Un barème est établi par la [décision n°2021-295](https://www.ign.fr/publications-de-l-ign/institut/informations_legales_administratives/Decision_2021-295_tarification.pdf) de l’Institut.

### Principes généraux d’accès aux données non libres sur la Géoplateforme

L’accès aux données non libres se fait sur la Géoplateforme via des points d’accès privés soumis à un contrôle des accès. Chaque service (à titre d’exemple WMTS) possède un unique point d’accès privé (URL) qui expose les données non libres. Pour y accéder (dans la limite des droits accordés à l'utilisateur), il est nécessaire de disposer d’une clé à déclarer en paramètre ou en en-tête des appels au point d’accès privé.

3 types de clés sont mobilisables :

-   Clé d’accès simple : de type HASH, créée de façon aléatoire (h7qvb44…) ou personnalisée (ma\_cle) et unique dans la Géoplateforme ;
-   Clé de type BASIC : sécurisée par un identifiant (unique dans la Géoplateforme) et un mot de passe paramétrés pour la clé ;
-   Clé de type OAUTH2 : sécurisation forte utilisant l’identifiant et le mot de passe du compte annuaire Géoplateforme associé (une seule clé OAUTH2 par utilisateur).

Des restrictions supplémentaires sont possibles pour tout type de clé :

-   Whitelist d’IPs : les IPs pour lesquelles l'accès aux données est autorisé ;
-   Blacklist d’IPs : les IPs pour lesquelles l'accès aux données est interdit ;
-   Referer : les URLs depuis lesquelles l'accès aux données est autorisé ;
-   User-agent : les noms techniques des applications depuis lesquelles l'accès aux données est autorisé.

## 

Titre

Demande d’accès à des données, configuration et paramétrage de la diffusion de données non libres sur la Géoplateforme et cartes.gouv.fr

Texte

La Géoplateforme offrira la possibilité pour tous les producteurs de diffuser des données sous une licence restreinte. Dans ce cadre, l’IGN au travers des données SCANs est le premier bêta testeur des fonctionnalités offertes.

A terme, sur la Géoplateforme, deux possibilités seront proposées aux producteurs pour paramétrer l’accès à leurs données :

-   Courant 2025, des interfaces dédiées, accessibles en mode connecté sur cartes.gouv.fr, vous offriront la possibilité de paramétrer simplement l’accès, les clés et les droits associés, mais aussi de demander l’accès à des données non libres ;
-   Dès à présent, pour les utilisateurs plus experts, vous pouvez utiliser l’API Entrepôt pour assurer ce paramétrage au travers de requêtes GET, POST, etc. La documentation de cette API est accessible [ici](https://geoplateforme.github.io/tutoriels/)

Image

Image

![](https://geoservices.ign.fr/sites/default/files/2023-11/IGN_donneesnonlibres_visuel.png)

Légende

IGN SCAN 25® - Antibes (06)

## 

Titre

Assurer la continuité dans votre accès aux SCANs

Texte

En attendant la mise en place des interfaces dédiées de gestion et d’accès sur cartes.gouv.fr, qui permettront un accès facilité aux clés, un fonctionnement transitoire est envisagé pour assurer la continuité d’accès aux données non libres offertes par l’IGN et prochainement par ses partenaires.

Selon que vos conditions d’utilisation des SCANs correspondent à un usage gratuit ou payant de ces données, deux possibilité sont mises en place :

-   Conditions d’utilisation des données SCAN entrainant un usage gratuit (voir décision résumée en préambule) :
    -   Vous pouvez tester dès à présent les données SCANs basculées sur Géoplateforme à partir des URLs suivantes :
        -   WMTS : [https://data.geopf.fr/private/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities&apikey=ign\_scan\_ws](https://data.geopf.fr/private/wmts?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities&apikey=ign_scan_ws)
        -   WMS : [https://data.geopf.fr/private/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&apikey=ign\_scan\_ws](https://data.geopf.fr/private/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&apikey=ign_scan_ws)
    -   Veuillez noter que l'accès à ces données se fait conformément aux indications de la [FAQ](https://geoservices.ign.fr/faq) et des [conditions de licence](https://geoservices.ign.fr/cgu-licences) du site des Géoservices.
    -   Cette clé partagée (ign\_scan\_ws pour WMTS et WMS) a une durée d’utilisation limitée. Nous vous invitons donc, dès que les interfaces seront disponibles, à créer votre clé d’accès aux données SCANs sur cartes.gouv.fr. Cette mise à disposition de l’interface fera l’objet d’une prochaine communication.
-   Conditions d’utilisation des données SCANs entrainant un usage payant (voir décision résumée en préambule) :
    -   Si vous n’avez pas encore été contactés par nos services, nous vous invitons à nous joindre à l'adresse mail [geoplateforme@ign.fr](mailto:geoplateforme@ign.fr)

Pour accéder aux SCAN 25/100/OACI à partir des URLs Géoplateforme dans QGIS, vous pouvez consulter notre tutoriel [ici](https://geoservices.ign.fr/documentation/services/utilisation-sig/tutoriel-qgis/gpf-wms-wmts-donneesnonlibres)

Pour accéder aux SCAN 25/100/OACI à partir des URLs Géoplateforme dans ArcGis, vous pouvez consulter notre tutoriel [ici](https://geoservices.ign.fr/documentation/services/utilisation-sig/tutoriel-arcgis/gpf-wms-wmts-donneesnonlibres)

## Commentaires

Commentaire

Bonjour,  
en vertu du document "Decision\_2021-295\_tarification.pdf" et dans le cadre d'un usage payant de type « streaming seul » : en quoi consistera (\*techniquement\*) sur la nouvelle géoplateforme une « transaction » de « lecture en continu des données » excluant le « téléchargement » et la « mise en cache » ?

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour,

Veuillez nous excuser pour le délai de réponse, les CGU précisent justement que, dans le cas du forfait "streaming seul", "le téléchargement et la mise en cache des Données Scan par l’Utilisateur sont interdits".  
Le passage en contexte Géoplateforme ne change pas cette précision.

Bonne journée  
Karim

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Ça sera donc de la diffusion hertzienne. Intéressant.

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour, l'utilisation de fonds de cartes est-il payant dans le cadre d'une étude (exemple : Etude d'Impacts) transmis à une administration (DDT par exemple) ? Merci.

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour,

Il s'agit d'un usage professionnel dans une mission de service public, l'utilisation est donc gratuite, vous retrouverez les éléments dans notre FAQ :https://geoservices.ign.fr/faq

Bonne journée  
Karim

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour,

pourquoi les fonds scans 25 et 100 ne sont plus téléchargeables par département ?  
C'est beaucoup plus simple d'utilisation sous arcgis et cela permet aussi de faire apparaitre les fonds de cartes seulement dans une emprise spécifique.  
Merci

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour,

Un incident nous empêche de mettre à disposition les liens de téléchargement dans les espaces logués (il ne s'agit pas de données libres), toutefois vous pouvez nous contacter à contact.geoservices@ign.fr pour nous faire part de votre besoin.

Bonne journée  
Karim

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour,  
Les diffusions en Lambert 93 seront elles disponibles sur le nouveau portail ?  
A ce jour ces services sont toujours donné comme "non publié"  
Merci,  
Bonne journée.  
Ludovic

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour,  
Nous espérons pouvoir les publier avant la fin des services du Géoportail (15 mars 2024), si tel n'était pas le cas, nous vous inviterons à utiliser le service de reprojection du WMS en attendant que les ressources soient disponibles en L93 pour le WMTS.

Bonne journée  
Karim

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

Commentaire

Bonjour  
J'utilise QMapShack, jusqu'à présent avec une clé que je collait dans un script .tms:  
<TMS>  
<Layer idx="0">  
<Title>IGN SCAN 25</Title>  
<MinZoomLevel>1</MinZoomLevel>  
<MaxZoomLevel>18</MaxZoomLevel>  
<ServerUrl>https://wxs.ign.fr/CLE/geoportail/tms/1.0.0/GEOGRAPHICALGRIDSYSTEMS.MAPS/%1/%2/%3.jpeg</ServerUrl>  
</Layer>  
<Copyright> © IGN – 2022 – Copie et reproduction interdite</Copyright>  
</TMS>

Mais depuis le changement, je ne vois pas comment faire!  
Pouvez vous m'aider?  
Merci d'avance. Marc

-   [Se connecter](https://geoservices.ign.fr/user/login?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) ou [s'inscrire](https://geoservices.ign.fr/user/register?destination=/actualites/2023-11-20-acces-donnesnonlibres-gpf%23comment-form) pour poster un commentaire

#### Pagination

-   [Page courante 1](https://geoservices.ign.fr/actualites/2023-11-20-acces-donnesnonlibres-gpf?page=0 "Page courante")
-   [Page 2](https://geoservices.ign.fr/actualites/2023-11-20-acces-donnesnonlibres-gpf?page=1 "Aller à la page 2")
-   [Page 3](https://geoservices.ign.fr/actualites/2023-11-20-acces-donnesnonlibres-gpf?page=2 "Aller à la page 3")
-   [Page suivante](https://geoservices.ign.fr/actualites/2023-11-20-acces-donnesnonlibres-gpf?page=1 "Aller à la page suivante")
-   [Dernière page](https://geoservices.ign.fr/actualites/2023-11-20-acces-donnesnonlibres-gpf?page=2 "Aller à la dernière page")