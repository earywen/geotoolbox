import sys
import os
import json
import base64
import logging
import requests
import urllib.request
import urllib3
from requests.adapters import HTTPAdapter

# Configuration globale
CONFIG = {}

def get_base_path():
    """
    Récupère le chemin racine interne (ressources).
    - En EXE : Dossier temporaire _MEIPASS (pour lire html, assets, config par défaut)
    - En DEV : Dossier racine du projet
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        current_file = os.path.abspath(__file__)
        modules_dir = os.path.dirname(current_file)
        root_dir = os.path.dirname(modules_dir)
        return root_dir

def get_user_dir():
    """
    Récupère le dossier 'physique' où se trouve l'application.
    C'est ici qu'on doit sauvegarder les fichiers (Exports, Logs, etc).
    - En EXE : Le dossier contenant le .exe
    - En DEV : La racine du projet
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return get_base_path()

def get_app_data_dir():
    """
    Récupère le dossier de données persistantes de l'application.
    - Windows: %APPDATA%/Geotoolbox
    - Linux/Mac: ~/.local/share/geotoolbox
    """
    # Windows
    if os.name == 'nt':
        app_data = os.getenv('APPDATA')
        if not app_data:
            app_data = os.path.expanduser('~')
        path = os.path.join(app_data, 'Geotoolbox')
    # Unix
    else:
        home = os.path.expanduser('~')
        path = os.path.join(home, '.local', 'share', 'geotoolbox')
    
    # Ensure it exists
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        
    return path

def init():
    """Charge la config et initialise les logs"""
    global CONFIG

    # 1. Chargement Config
    base_internal = get_base_path()

    # Defaults
    DEFAULTS = {
        "network": {"verify_ssl": True, "timeout": 30, "user_agent": "BurgeaplyHub/2.0"},
        "app": {"log_level": "INFO", "log_file": "burgeaply.log", "debug": False},
        "geotoolbox": {
            "georisques_url": "https://georisques.gouv.fr/services",
            "brgm_wfs_url": "https://geoservices.brgm.fr/geologie",
            "ign_wfs_url": "https://data.geopf.fr/wfs/ows",
            "infoterre_url": "http://infoterre.brgm.fr/fiche/"
        },
        "orthohisto": {
            "wms_url": "https://wxs.ign.fr/ortho/geoportail/r/wms",
            "wfs_url": "https://wxs.ign.fr/ortho/geoportail/wfs",
            "download_url": "https://wxs.ign.fr/ortho/geoportail/r/wms"
        }
    }

    # Par défaut on cherche config.json à la racine interne
    config_path = os.path.join(base_internal, 'config.json')

    # SI on est en mode EXE, on regarde si une config externe existe (pour surcharge)
    if getattr(sys, 'frozen', False):
        external_config = os.path.join(get_user_dir(), 'config.json')
        if os.path.exists(external_config):
            config_path = external_config

    loaded_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
        except Exception as e:
            print(f"ERREUR CRITIQUE: Impossible de lire config.json : {e}")
    else:
        print(f"INFO: Aucun fichier config.json trouvé à : {config_path}. Utilisation des défauts.")

    # Merge Loading Config into Defaults (Recursive merge could be better but shallow merge of sections is enough here)
    CONFIG = DEFAULTS.copy()
    for section, values in loaded_config.items():
        if section in CONFIG and isinstance(values, dict):
            CONFIG[section].update(values)
        else:
            CONFIG[section] = values

    # 2. Configuration Logs (Toujours à côté de l'exécutable ou du script)
    log_dir = get_user_dir()
    log_file = os.path.join(log_dir, CONFIG.get('app', {}).get('log_file', 'burgeaply.log'))

    logging.basicConfig(
        level=getattr(logging, CONFIG.get('app', {}).get('log_level', 'INFO').upper()),
        format='%(asctime)s [%(levelname)s] %(module)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info("=== Démarrage de l'application ===")
    logging.info(f"Mode détecté : {'EXE (Frozen)' if getattr(sys, 'frozen', False) else 'DEV (Script)'}")
    logging.info(f"Dossier interne (Ressources) : {base_internal}")
    logging.info(f"Dossier utilisateur (Sorties) : {log_dir}")

def get_session():
    """Renvoie une session HTTP pré-configurée et optimisée"""
    s = requests.Session()

    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
    s.mount('https://', adapter)
    s.mount('http://', adapter)

    verify = CONFIG.get('network', {}).get('verify_ssl', True)
    s.verify = verify

    if not verify:
        logging.warning("⚠️  SSL VERIFICATION DISABLED - This should only be used in development!")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ua = CONFIG.get('network', {}).get('user_agent', 'BurgeaplyHub')
    s.headers.update({'User-Agent': ua})
    s.proxies.update(urllib.request.getproxies())

    return s

def load_template(filename):
    """
    Charge un fichier HTML depuis assets/templates/ avec protection path traversal.
    
    Args:
        filename: Nom du fichier template (ex: 'feedback.html')
        
    Returns:
        str: Contenu du fichier HTML
        
    Raises:
        SecurityError: Si le chemin contient une tentative de path traversal
        FileNotFoundError: Si le fichier n'existe pas
    """
    from pathlib import Path

    base = get_base_path()
    base_path = Path(base) / 'assets' / 'templates'

    # Résoudre les chemins absolus
    base_resolved = base_path.resolve()
    requested_path = base_path / filename
    requested_resolved = requested_path.resolve()

    # Vérifier que le chemin résolu est bien dans le dossier autorisé
    try:
        requested_resolved.relative_to(base_resolved)
    except ValueError:
        error_msg = f"Security Error: Path traversal attempt detected - {filename}"
        logging.error(error_msg)
        raise SecurityError(error_msg)

    # Vérifier que le fichier existe
    if not requested_resolved.exists():
        logging.error(f"Template introuvable: {requested_resolved}")
        return f"<h3 style='color:red'>Erreur: Impossible de charger {filename}</h3>"

    # Charger le fichier
    try:
        with open(requested_resolved, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erreur lecture template {filename}: {e}")
        return f"Erreur lecture: {e}"


class SecurityError(Exception):
    """Exception levée lors de violations de sécurité."""
    pass

def get_logo_b64():
    """Récupère le logo en base64 de manière centralisée"""
    try:
        path = os.path.join(get_base_path(), 'assets', 'logo.png')
        if not os.path.exists(path): return ""
        # Sécurité taille image
        if os.path.getsize(path) > 1_000_000: return ""
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logging.error(f"Erreur chargement logo: {e}")
        return ""

# ==========================================
# UI ADAPTER (Testability Pattern)
# ==========================================
class UIAdapter:
    """Interface for UI interactions."""
    def dispatch(self, event_name: str, payload: dict):
        pass

class WebviewAdapter(UIAdapter):
    """Real implementation using pywebview."""
    def dispatch(self, event_name: str, payload: dict):
        try:
            import webview
            window = webview.active_window()
            if window:
                # Ensure payload is safe JSON
                safe_payload = json.dumps(payload)
                # Create and dispatch the event in the WebView
                script = f"window.dispatchEvent(new CustomEvent('{event_name}', {{ 'detail': {safe_payload} }}));"
                window.evaluate_js(script)
        except Exception as e:
            logging.error(f"Event Dispatch Error ({event_name}): {e}")

class MockAdapter(UIAdapter):
    """Mock implementation for testing."""
    def __init__(self):
        self.events = []

    def dispatch(self, event_name: str, payload: dict):
        self.events.append((event_name, payload))

# Global Adapter Instance
UI_ADAPTER: UIAdapter = WebviewAdapter()


def dispatch_event(event_name: str, payload: dict):
    """
    Dispatches a CustomEvent to the UI via the configured adapter.
    This allows the backend to be decoupled from specific JS function names
    and enables headless unit testing.
    """
    UI_ADAPTER.dispatch(event_name, payload)
