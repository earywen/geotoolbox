# modules/updater.py
import logging
import semver
from modules import core, version

# URL brute vers ton fichier JSON sur GitHub
# Remplace 'TON_PSEUDO' par ton vrai nom d'utilisateur GitHub
UPDATE_URL = "https://raw.githubusercontent.com/earywen/geotoolbox-dist/main/latest_version.json"

def check_for_updates():
    """
    Vérifie si une version supérieure existe sur GitHub.
    Retourne un dictionnaire d'infos ou None.
    """
    try:
        logging.info("🔍 Recherche de mises à jour...")
        session = core.get_session() # On réutilise ta session configurée (proxy etc)

        # Timeout court (3s) pour ne pas bloquer l'app si le réseau est lent
        response = session.get(UPDATE_URL, timeout=3)

        if response.status_code == 200:
            data = response.json()
            remote_ver_str = data.get("version", "0.0.0")
            local_ver_str = version.CURRENT_VERSION

            # Comparaison propre avec semver (installé dans ton requirements.txt)
            # On parse les versions pour pouvoir les comparer mathématiquement
            remote_ver = semver.Version.parse(remote_ver_str)
            local_ver = semver.Version.parse(local_ver_str)

            if remote_ver > local_ver:
                logging.info(f"✨ Update disponible: {remote_ver_str} (Local: {local_ver_str})")
                return {
                    "has_update": True,
                    "local": local_ver_str,
                    "remote": remote_ver_str,
                    "url": data.get("download_url"),
                    "message": data.get("message", "Nouvelle version disponible.")
                }

        logging.info("✅ Application à jour.")
        return None

    except Exception as e:
        # On log l'erreur mais on ne fait pas crasher l'app pour ça
        logging.warning(f"Impossible de vérifier les mises à jour : {e}")
        return None
