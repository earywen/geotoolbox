import webview
import os
import sys
import base64
import json
import tempfile
import pathlib
import atexit 
import logging
import requests
import pandas
import xlsxwriter
import lxml
import webbrowser # Nécessaire pour ouvrir le lien de téléchargement
from modules import geotoolbox, orthohisto, feedback, about, version, core, updater 

# ==========================================
# 1. CONFIGURATION
# ==========================================
ACTIVE_MODULES = [
    geotoolbox,
    orthohisto,
    feedback,
    about 
]

# ==========================================
# 2. RESSOURCES
# ==========================================
class AssetManager:
    @staticmethod
    def get_base_path():
        if hasattr(sys, '_MEIPASS'): return sys._MEIPASS
        return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def get_logo_b64():
        try:
            path = os.path.join(AssetManager.get_base_path(), 'assets', 'logo.png')
            if not os.path.exists(path): return ""
            # Sécurité taille image pour éviter de ralentir le chargement
            if os.path.getsize(path) > 1_000_000: return "" 
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                return f"data:image/png;base64,{encoded}"
        except: return ""

# ==========================================
# 3. UI GENERATOR
# ==========================================
def generate_html_content():
    logo_b64 = AssetManager.get_logo_b64()
    logo_style = "display:block;" if logo_b64 else "display:none;"
    text_style = "display:none;" if logo_b64 else "display:block;"

    menu_html = ""
    views_html = ""
    
    try:
        for module in ACTIVE_MODULES:
            info = module.TOOL_INFO
            menu_html += f"""
            <div class="menu-item" onclick="switchView('{info['id']}', this)">
                {info['icon']} {info['name']}
            </div>
            """
            views_html += f"""
            <div id="view-{info['id']}" class="view-section">
                {module.get_ui_content()}
            </div>
            """
    except Exception as e:
        views_html = f"<div style='color:red; padding:20px;'>Erreur UI: {e}</div>"

    app_ver = version.CURRENT_VERSION

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Burgeaply Hub v{app_ver}</title>
    <style>
        /* --- VARIABLES CSS CORRIGÉES --- */
        :root {{ 
            --sidebar-width: 250px; 
            --toolbox-width: 350px;
            --primary: #0f172a; 
            --accent: #38bdf8; 
            --text: #f1f5f9; 
        }}
        
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Segoe UI', sans-serif; overflow: hidden; background: #e2e8f0; user-select: none; }}
        
        /* SPLASH */
        #splash-screen {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); z-index: 9999; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; transition: opacity 0.8s ease-out; }}
        .logo-img-splash {{ max-width: 150px; margin-bottom: 20px; animation: float 3s ease-in-out infinite; }}
        .loader-container {{ width: 300px; height: 4px; background: #334155; border-radius: 2px; overflow: hidden; margin-bottom: 20px; }}
        .loader-bar {{ height: 100%; width: 0%; background: var(--accent); border-radius: 2px; transition: width 0.2s linear; }}
        @keyframes float {{ 0% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} 100% {{ transform: translateY(0px); }} }}

        /* APP */
        #app {{ display: flex; width: 100%; height: 100%; opacity: 0; transition: opacity 1s ease; }}
        #app.visible {{ opacity: 1; }}
        
        /* SIDEBAR */
        #main-sidebar {{ width: var(--sidebar-width); background: var(--primary); color: var(--text); display: flex; flex-direction: column; padding-top: 40px; box-shadow: 2px 0 10px rgba(0,0,0,0.3); z-index: 2000; }}
        .logo-img-sidebar {{ max-width: 120px; margin: 0 auto 30px auto; }}
        .brand-text {{ font-size: 24px; font-weight: 800; color: var(--accent); text-align: center; margin-bottom: 30px; letter-spacing: 1px; }}
        .menu-item {{ padding: 15px 25px; cursor: pointer; transition: background 0.2s; font-weight: 500; display: flex; align-items: center; gap: 10px; border-left: 4px solid transparent; }}
        .menu-item:hover {{ background: #1e293b; color: white; }}
        .menu-item.active {{ background: #1e293b; color: var(--accent); border-left-color: var(--accent); }}
        
        /* COPYRIGHT FOOTER */
        .sidebar-footer {{ margin-top: auto; padding: 20px; font-size: 10px; color: #64748b; text-align: center; border-top: 1px solid #1e293b; line-height: 1.4; }}
        
        #content-area {{ flex: 1; position: relative; overflow: hidden; display: flex; }}
        
        /* VUES */
        .view-section {{ width: 100%; height: 100%; position: absolute; top: 0; left: 0; display: none; flex-direction: row; overflow-y: auto; }} 
        .view-section.active {{ display: flex; }}
        
        #view-home {{ background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); flex-direction: column; justify-content: center; align-items: center; text-align: center; color: #334155; }}
        .home-card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); max-width: 600px; }}
        
        #view-about {{ background: #0f172a; }} 
        #view-about.active {{ display: block; }} 

        /* COMMUNS */
        h2 {{ margin-top: 0; font-size: 18px; font-weight: 600; color: var(--accent); text-transform: uppercase; margin-bottom: 20px; }}
        .section-title {{ font-size: 11px; color: #94a3b8; font-weight: bold; margin-top: 15px; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 5px; }}
        .input-container {{ margin-bottom: 15px; background: #334155; padding: 10px; border-radius: 6px; color:white; }}
        .input-group {{ display: flex; gap: 5px; margin-top: 5px; }}
        input[type=text].folder-input {{ flex: 1; padding: 8px; border: 1px solid #475569; background: #1e293b; color: white; border-radius: 4px; }}
        .btn-browse {{ background: #475569; color: white; border: none; border-radius: 4px; cursor: pointer; padding: 0 10px; }}
        .btn {{ flex: 1; border: none; padding: 15px; cursor: pointer; border-radius: 8px; font-weight: bold; font-size: 13px; color:white; }}
        .btn-preview {{ background: #f59e0b; }} .btn-export {{ background: #0ea5e9; }}
        
        /* OVERLAY LOADER */
        #processing-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(5px); z-index: 5000; display: none; justify-content: center; align-items: center; color:white; flex-direction:column; }}
        #processing-overlay.active {{ display: flex; }}
        .proc-bar-bg {{ width: 400px; height: 10px; background: #334155; margin-top:15px; border-radius:5px; overflow:hidden; }}
        .proc-bar-fill {{ height: 100%; width: 0%; background: linear-gradient(90deg, #38bdf8, #2563eb); transition: width 0.3s ease; }}
        
        /* CSS MODULES */
        #geotoolbox-container, #ortho-container {{ display: flex; width: 100%; height: 100%; }}
        #toolbox-sidebar {{ width: var(--toolbox-width); background: #1e293b; color: #f1f5f9; display: flex; flex-direction: column; padding: 20px; overflow-y: auto; border-right: 1px solid #334155; flex-shrink: 0; }}
        #map, #orthoMap {{ flex: 1; height: 100%; background: #cbd5e1; }}
        .checkbox-group {{ background: #334155; padding: 10px; border-radius: 6px; color:white; }}
        .checkbox-wrapper {{ margin-bottom: 8px; display: flex; align-items: center; }}
        #logs-container {{ margin-top: auto; background: #0f172a; border-radius: 6px; padding: 10px; height: 150px; font-size: 11px; overflow-y: auto; font-family: monospace; border: 1px solid #334155; color: #cbd5e1; }}
        .log-error {{ color: #f87171; }} .log-success {{ color: #4ade80; }}
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
</head>
<body>

<div id="splash-screen">
    <img src="{logo_b64}" class="logo-img-splash" style="{logo_style}">
    <div class="loader-container"><div class="loader-bar" id="progress-bar"></div></div>
    <div class="loading-text">Initialisation...</div>
</div>

<div id="processing-overlay">
    <div style="font-size:40px; margin-bottom:20px;">⚙️</div>
    <div id="proc-title" style="font-weight:bold; font-size:20px;">Traitement en cours</div>
    <div id="proc-desc" style="color:#94a3b8; margin-top:5px;">Veuillez patienter...</div>
    <div class="proc-bar-bg"><div class="proc-bar-fill" id="proc-bar"></div></div>
    <div id="proc-percent" style="margin-top:5px; font-family:monospace; font-size:12px; color:#38bdf8">0%</div>
</div>

<div id="app">
    <div id="main-sidebar">
        <img src="{logo_b64}" class="logo-img-sidebar" style="{logo_style}">
        <div class="brand-text" style="{text_style}">Burgeaply</div>
        
        <div class="menu-item active" onclick="switchView('home', this)">🏠 Accueil</div>
        {menu_html}

        <div class="sidebar-footer">
            v{app_ver}<br>
            Développé par <b>Laurent BRIGAUD</b><br>
            Idée : <b>Amine El Mahlali</b><br>
            <span style="color:#38bdf8">Ginger BURGEAP</span>
        </div>
    </div>

    <div id="content-area">
        <div id="view-home" class="view-section active">
            <div class="home-card">
                <img src="{logo_b64}" class="logo-img-sidebar" style="max-width:80px; margin:0 auto 20px auto; {logo_style}">
                <div class="brand-text" style="font-size:32px; margin-bottom:10px;">Bienvenue</div>
                <p>Hub d'Ingénierie Environnementale</p>
                <div style="margin-top:20px; color:#94a3b8; font-size:12px;">Version {app_ver}</div>
            </div>
        </div>
        {views_html}
    </div>
</div>

<script>
    window.onload = function() {{
        let p = 0; const bar = document.getElementById('progress-bar');
        const interval = setInterval(() => {{
            p += 2; bar.style.width = p + '%';
            if (p >= 100) {{ 
                clearInterval(interval); 
                document.getElementById('splash-screen').style.opacity = '0';
                setTimeout(() => {{
                    document.getElementById('splash-screen').style.display = 'none';
                    document.getElementById('app').classList.add('visible');
                    window.dispatchEvent(new Event('resize'));
                    
                    // --- AUTO-UPDATE CHECK (DÉMARRAGE DIFFÉRÉ) ---
                    setTimeout(() => {{
                        if (typeof pywebview !== 'undefined' && pywebview.api) {{
                            pywebview.api.check_updates_ui();
                        }}
                    }}, 1500);
                    // --------------------------------------------

                }}, 800);
            }}
        }}, 30);
    }};

    function switchView(viewId, menuEl) {{
        document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
        if(menuEl) menuEl.classList.add('active');
        document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
        document.getElementById('view-' + viewId).classList.add('active');
        if (typeof window['init_' + viewId] === 'function') try {{ window['init_' + viewId](); }} catch(e) {{}}
    }}

    function browseFolder() {{
        pywebview.api.select_directory().then(p => {{ if(p) document.getElementById('targetPath').value = p; }});
    }}

    // --- LOADER SYSTEM ---
    function showLoader(title) {{
        document.getElementById('processing-overlay').classList.add('active');
        document.getElementById('proc-title').innerText = title;
        updateLoader(0, "Démarrage...");
    }}
    
    function hideLoader() {{
        setTimeout(() => {{ document.getElementById('processing-overlay').classList.remove('active'); }}, 500);
    }}

    function updateLoader(percent, message) {{
        document.getElementById('proc-bar').style.width = percent + '%';
        document.getElementById('proc-percent').innerText = Math.round(percent) + '%';
        if(message) document.getElementById('proc-desc').innerText = message;
    }}
</script>
</body>
</html>
"""

# ==========================================
# 4. API ROUTER
# ==========================================
class BurgeaplyApi:
    def select_directory(self):
        w = webview.active_window()
        res = w.create_file_dialog(webview.FOLDER_DIALOG) if w else None
        return res[0] if res else None

    def run_preview(self, bbox, layers): return geotoolbox.run_preview_logic(bbox, layers)
    def run_export(self, bbox, layers, folder, path): return geotoolbox.run_export_logic(bbox, layers, folder, path)

    def run_full_process(self, lat, lon, radius, path):
        def progress_callback(percent, msg):
            w = webview.active_window()
            if w:
                w.evaluate_js(f"updateLoader({percent}, {json.dumps(msg)})")
        return orthohisto.run_full_process(lat, lon, radius, path, progress_callback)

    def run_send_feedback(self, category, message, trigram, contact):
        return feedback.send_discord_feedback(category, message, trigram, contact)

    # --- MÉTHODE AJOUTÉE POUR L'UPDATER ---
    def check_updates_ui(self):
        """Vérifie les mises à jour et notifie l'utilisateur via popup"""
        try:
            update_info = updater.check_for_updates()
            if update_info and update_info['has_update']:
                w = webview.active_window()
                if w:
                    msg = (f"Une nouvelle version v{update_info['remote']} est disponible !\n\n"
                           f"Nouveautés :\n{update_info['message']}\n\n"
                           "Voulez-vous la télécharger maintenant ?")
                    
                    # Dialogue natif Windows
                    choice = w.create_confirmation_dialog("Mise à jour disponible", msg)
                    
                    if choice:
                        webbrowser.open(update_info['url'])
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de mise à jour: {e}")

if __name__ == '__main__':
    # Initialisation Core (Logs + Config)
    core.init()
    api = BurgeaplyApi()
    window_title = f'Burgeaply Hub v{version.CURRENT_VERSION}'
    
    # 1. Génération du HTML
    html_content = generate_html_content()
    
    # 2. FIX CRITIQUE : Création sécurisée et nettoyage automatique
    # On garde la référence au fichier pour pouvoir le supprimer
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8')
    temp_file.write(html_content)
    temp_file.close() # Important : on ferme le handle pour que WebView puisse l'ouvrir
    temp_path = temp_file.name
    
    # FONCTION DE NETTOYAGE
    def cleanup_temp():
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logging.info(f"Fichier temporaire nettoyé : {temp_path}")
        except Exception as e:
            logging.error(f"Erreur nettoyage temp: {e}")

    # Enregistrement du nettoyage à la fermeture du script
    atexit.register(cleanup_temp)
    
    # Conversion en URL fichier
    file_url = pathlib.Path(temp_path).as_uri()

    # 3. Lancement
    window = webview.create_window(window_title, url=file_url, js_api=api, width=1300, height=900)
    webview.start(gui='edge', debug=True)