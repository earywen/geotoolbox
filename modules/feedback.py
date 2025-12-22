import json
import logging
from datetime import datetime
from modules import core

# ==========================================
# 1. META-DONNÉES
# ==========================================
TOOL_INFO = {
    "id": "feedback",
    "name": "Feedback & Support",
    "icon": "📢", 
    "description": "Signaler un bug ou proposer une idée"
}

# ==========================================
# 2. LOGIQUE MÉTIER
# ==========================================
def send_discord_feedback(category, message, trigram, contact_info=""):
    # Récupération de l'URL depuis la configuration centralisée
    webhook_url = core.CONFIG.get('discord', {}).get('webhook_url')
    
    # Vérification basique
    if not webhook_url or "TON_URL" in webhook_url:
        logging.error("URL Discord non configurée ou invalide dans config.json")
        return {"success": False, "msg": "Erreur configuration serveur."}

    try:
        logging.info(f"Envoi feedback ({category}) de {trigram}")
        
        # Couleurs Discord
        color = 5763719 # Gris (Autre)
        if category == "bug": color = 15548997 # Rouge
        elif category == "idea": color = 5763719 # Vert

        titles = {
            "bug": "🪲 Rapport de Bug",
            "idea": "💡 Nouvelle Idée",
            "other": "✉️ Message Divers"
        }

        # Nettoyage
        trigram_clean = trigram.upper().strip()

        payload = {
            "username": "Burgeaply Hub",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/2921/2921226.png",
            "embeds": [
                {
                    "title": titles.get(category, "Feedback"),
                    "description": message,
                    "color": color,
                    "fields": [
                        {
                            "name": "👤 Auteur",
                            "value": f"**{trigram_clean}**",
                            "inline": True
                        }
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }

        # Envoi via la session centralisée (optimisée)
        session = core.get_session()
        response = session.post(
            webhook_url, 
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 204:
            logging.info("Feedback envoyé avec succès")
            return {"success": True}
        else:
            logging.error(f"Erreur Discord: {response.status_code} - {response.text}")
            return {"success": False, "msg": f"Erreur Discord: {response.status_code}"}

    except Exception as e:
        logging.exception("Exception lors de l'envoi du feedback")
        return {"success": False, "msg": str(e)}

# ==========================================
# 3. UI (TEMPLATE)
# ==========================================
def get_ui_content():
    # Chargement propre du fichier HTML externe
    return core.load_template("feedback.html")