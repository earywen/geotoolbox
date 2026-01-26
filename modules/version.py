# modules/version.py

# --- INFO ACTUELLE ---
CURRENT_VERSION = "2.1.1"  # Hotfix Build
RELEASE_DATE = "26 Janvier 2026"

# --- HISTORIQUE (Le plus récent en haut) ---
CHANGELOG = [
    {
        "version": "2.1.1",
        "date": "26 Janvier 2026",
        "type": "patch",
        "changes": [
            "✅ AutoLabo : Correction de la détection des laboratoires qui pouvait échouer sur certains postes.",
            "🗺️ Cartographie : Réparation de l'export des données (Excel/GIS) qui bloquait l'application.",
            "🔧 Système : Mise à jour des composants internes pour une meilleure stabilité."
        ]
    },
    {
        "version": "2.1.0",
        "date": "17 Janvier 2026",
        "type": "minor",
        "changes": [
            "🛡️ Sécurité Renforcée : Protection 'Path Traversal', vérification SSL stricte (configurable), et gestion des secrets (.env)",
            "🏗️ Refonte AutoLabo : Nouvelle architecture modulaire (GenericLabProcessor) pour un support Eurofins/Carso robuste",
            "✅ Qualité Code : Couverture de tests à 100% sur le cœur de l'application (Core, GéoToolbox, Orthohisto)",
            "🔧 Fiabilité : Validation des fichiers Excel en entrée et messages d'erreurs plus clairs pour l'utilisateur",
            "⚡ Optimisation : Réduction des dépendances graphiques (UI Decoupling) pour une meilleure stabilité"
        ]
    },
    {
        "version": "2.0.0",
        "date": "23 Décembre 2025",
        "type": "major",
        "changes": [
            "🎨 Refonte UI v2 : Interface Glassmorphism complète (Dark Mode, Transparence)",
            "💅 Style Modernisé : Bento Grid, animations fluides et typographie épurée",
            "🛠️ Architecture Technique : Séparation HTML/CSS/JS et suppression du CSS inline",
            "📂 Structure Modulaire : Templates HTML externes pour une meilleure maintenabilité"
        ]
    },
    {
        "version": "1.1.1",
        "date": "22 Décembre 2025",
        "type": "patch",
        "changes": [
            "🐛 Correction critique : Les fichiers téléchargés (Chronologie) sont désormais sauvegardés à côté de l'application et non dans un dossier temporaire caché."
        ]
    },
    {
        "version": "1.1.0",
        "date": "22 Décembre 2025",
        "type": "minor",
        "changes": [
            "🏔️ Nouvel Algo Amont/Aval : Basé sur vecteur pente locale (150m) + validation altimétrique (Z)",
            "📊 Export Excel amélioré : Séparation Distance/Position, centrage et alertes visuelles (Jaune)",
            "🔌 API IGN : Migration vers la Géoplateforme & gestion robuste des Quotas/Proxy",
            "⚡ Performance : Optimisation majeure (Calcul du relief global unique)",
            "🐛 Correction : Déblocage de la barre de progression durant l'export"
        ]
    },
    {
        "version": "1.0.1",
        "date": "22 Décembre 2025",
        "type": "patch",
        "changes": [
            "🐞 Correction d'un bug mineur sur l'affichage",
            "🔧 Optimisation du chargement des modules"
        ]
    },
    {
        "version": "1.0.0",
        "date": "21 Décembre 2025",
        "type": "major",
        "changes": [
            "🚀 Lancement officiel de Burgeaply Hub",
            "🌍 Module GéoToolbox (WFS, Polygones, BSS)",
            "📋 Module Chronologie Complète",
            "💬 Module Feedback & Support"
        ]
    }
]
