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

def init():
    """Charge la config et initialise les logs"""
    global CONFIG
    
    # 1. Chargement Config
    base_internal = get_base_path()
    
    # Par défaut on cherche config.json à la racine interne
    config_path = os.path.join(base_internal, 'config.json')
    
    # SI on est en mode EXE, on regarde si une config externe existe (pour surcharge)
    if getattr(sys, 'frozen', False):
        external_config = os.path.join(get_user_dir(), 'config.json')
        if os.path.exists(external_config):
            config_path = external_config

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                CONFIG = json.load(f)
        except Exception as e:
            print(f"ERREUR CRITIQUE: Impossible de lire config.json : {e}")
    else:
        print(f"ATTENTION: config.json introuvable à : {config_path}")
        CONFIG = {
            "network": {"verify_ssl": True, "timeout": 30},
            "app": {"log_level": "INFO"}
        }

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
        return f"<h3 style='color:red'>Erreur: Impossible de charger {filename}</h3>"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erreur lecture template {filename}: {e}")
        return f"Erreur lecture: {e}"