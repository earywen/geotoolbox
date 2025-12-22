# modules/version.py

# --- INFO ACTUELLE ---
CURRENT_VERSION = "1.1.0"  # Passage en 1.1.0 suite aux améliorations majeures
RELEASE_DATE = "22 Décembre 2025"

# --- HISTORIQUE (Le plus récent en haut) ---
CHANGELOG = [
    # --- DÉBUT DU NOUVEAU BLOC ---
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
    # --- FIN DU NOUVEAU BLOC ---

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