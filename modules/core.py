import sys
import os
import json
import logging
import requests
import urllib.request
import urllib3
from requests.adapters import HTTPAdapter

# Configuration globale
CONFIG = {}

def get_base_path():
    """
    Récupère le chemin racine correct.
    Gère la différence entre le mode DEV (dossiers) et PROD (exe).
    """
    # 1. Si on est dans l'exécutable compilé (Frozen / PyInstaller)
    if getattr(sys, 'frozen', False):
        # On renvoie le chemin temporaire où PyInstaller a extrait les fichiers
        return sys._MEIPASS
    
    # 2. Si on est en mode développement (script Python classique)
    else:
        # Nous sommes ici : .../geotoolbox/modules/core.py
        current_file = os.path.abspath(__file__)
        
        # Dossier parent 1 : .../geotoolbox/modules
        modules_dir = os.path.dirname(current_file)
        
        # Dossier parent 2 (Racine du projet) : .../geotoolbox
        root_dir = os.path.dirname(modules_dir)
        
        return root_dir

def init():
    """Charge la config et initialise les logs"""
    global CONFIG
    
    # 1. Chargement Config
    base_internal = get_base_path()
    
    # Par défaut on cherche config.json à la racine du projet (ou dans _MEIPASS)
    config_path = os.path.join(base_internal, 'config.json')
    
    # SI on est en mode EXE, on peut aussi vouloir charger une config externe (sur le bureau)
    if getattr(sys, 'frozen', False):
        external_config = os.path.join(os.path.dirname(sys.executable), 'config.json')
        if os.path.exists(external_config):
            config_path = external_config

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                CONFIG = json.load(f)
        except Exception as e:
            print(f"ERREUR CRITIQUE: Impossible de lire config.json : {e}")
    else:
        # Message de debug utile pour savoir où il a cherché
        print(f"ATTENTION: config.json introuvable à : {config_path}")
        CONFIG = {
            "network": {"verify_ssl": True, "timeout": 30},
            "app": {"log_level": "INFO"}
        }

    # 2. Configuration Logs
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable) # Sur le bureau (à côté de l'exe)
    else:
        log_dir = base_internal # A la racine du projet en mode dev

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
    logging.info(f"Racine des fichiers : {base_internal}")

def get_session():
    """Renvoie une session HTTP pré-configurée et optimisée pour le multi-threading"""
    s = requests.Session()
    
    # --- OPTIMISATION DU POOL ---
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
    s.mount('https://', adapter)
    s.mount('http://', adapter)
    # ----------------------------

    verify = CONFIG.get('network', {}).get('verify_ssl', True)
    s.verify = verify
    
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    ua = CONFIG.get('network', {}).get('user_agent', 'BurgeaplyHub')
    s.headers.update({'User-Agent': ua})
    s.proxies.update(urllib.request.getproxies())
    
    return s

def load_template(filename):
    """Charge un fichier HTML depuis assets/templates/"""
    base = get_base_path()
    path = os.path.join(base, 'assets', 'templates', filename)
    
    if not os.path.exists(path):
        logging.error(f"Template introuvable: {path}")
        return f"<h3 style='color:red'>Erreur: Impossible de charger {filename}</h3><p>Chemin cherché : {path}</p>"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erreur lecture template {filename}: {e}")
        return f"Erreur lecture: {e}"