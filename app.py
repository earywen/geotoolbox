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
# ==========================================
# 3. UI GENERATOR
# ==========================================

# --- ICONS SVG (Lucide / Heroicons style) ---
ICONS = {
    "home": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>""",
    "geotoolbox": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>""",
    "orthohisto": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
    "feedback": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>""",
    "about": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>"""
}

GLOBAL_STYLES = """
    /* --- GOOGLE FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* --- VARIABLES --- */
    :root {
        --bg-dark: #0f172a;      /* Slate 950 */
        --bg-panel: #1e293b;     /* Slate 800 */
        --accent: #38bdf8;       /* Sky 400 */
        --accent-glow: rgba(56, 189, 248, 0.4);
        --text-main: #f1f5f9;
        --text-muted: #94a3b8;
        --glass-bg: rgba(30, 41, 59, 0.75);
        --glass-border: rgba(255, 255, 255, 0.08);
        --radius-xl: 24px;
        --radius-md: 12px;
        --dock-width: 80px;  /* Collapsed dock */
        --dock-width-expanded: 260px;
    }

    /* --- RESET & BASE --- */
    * { box-sizing: border-box; outline: none; }
    body, html { 
        margin: 0; padding: 0; width: 100%; height: 100%; 
        font-family: 'Inter', sans-serif; 
        background-color: var(--bg-dark); 
        color: var(--text-main); 
        overflow: hidden; 
        user-select: none; 
    }

    /* --- UTILS GLASSMORPHISM --- */
    .glass-panel {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
    
    .card {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.05);
        transition: transform 0.2s;
    }
    
    /* --- ANIMATIONS --- */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-6px); } 100% { transform: translateY(0px); } }

    /* --- BUTTONS --- */
    .btn-glow {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
        border: none; color: white; border-radius: 99px;
        padding: 10px 20px; font-weight: 600; font-size: 13px;
        cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
        display: inline-flex; align-items: center; gap: 8px; justify-content: center;
    }
    .btn-glow:hover {
        transform: scale(1.05) translateY(-2px);
        box-shadow: 0 8px 25px rgba(14, 165, 233, 0.5);
    }
    .btn-secondary {
        background: rgba(255,255,255,0.05);
        color: var(--text-muted);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .btn-secondary:hover { background: rgba(255,255,255,0.1); color: white; }

    /* --- INPUTS --- */
    .input-group { display: flex; align-items: center; gap: 8px; width: 100%; margin-bottom: 15px; }
    
    .input-pill {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #334155;
        border-radius: 99px;
        padding: 10px 15px;
        color: white; font-family: inherit; font-size: 13px;
        transition: all 0.3s;
        width: 100%;
        flex: 1; /* NEW: Takes available space */
    }
    .input-pill:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--accent-glow);
    }

    .btn-icon-input {
        height: 42px; width: 42px;
        display: flex; align-items: center; justify-content: center;
        background: rgba(255,255,255,0.05);
        border: 1px solid #334155;
        border-radius: 12px;
        color: var(--text-muted);
        cursor: pointer; transition: all 0.2s; flex-shrink: 0;
    }
    .btn-icon-input:hover {
        background: var(--accent); color: white; border-color: var(--accent);
    }

    /* --- SCROLLBAR --- */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }

    /* --- LAYOUT : DOCK --- */
    #dock-container {
        position: absolute; top: 20px; bottom: 20px; left: 20px;
        width: var(--dock-width);
        border-radius: var(--radius-xl);
        display: flex; flex-direction: column; align-items: center;
        padding: 20px 0;
        z-index: 5000;
        transition: width 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
        overflow: hidden;
    }
    #dock-container:hover { width: var(--dock-width-expanded); align-items: flex-start; }
    
    .dock-logo { margin-bottom: 30px; transition: all 0.3s; padding: 0 20px; display: flex; align-items: center; gap: 15px; width: 100%; justify-content: center; }
    #dock-container:hover .dock-logo { justify-content: flex-start; }
    .dock-logo img { width: 40px; height: 40px; animation: float 6s ease-in-out infinite; }
    .dock-title { font-weight: 800; font-size: 18px; color: white; display: none; white-space: nowrap; animation: fadeIn 0.4s; }
    #dock-container:hover .dock-title { display: block; }
    
    .dock-item {
        width: 100%; padding: 15px 0;
        display: flex; align-items: center;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.2s;
        position: relative;
    }
    /* Centered icon when collapsed */
    .dock-item .icon-box {
        width: var(--dock-width); min-width: var(--dock-width);
        display: flex; justify-content: center; align-items: center;
    }
    .dock-item .label {
        display: none; white-space: nowrap; font-weight: 500; font-size: 14px;
        opacity: 0; transition: opacity 0.2s;
    }
    #dock-container:hover .dock-item .label { display: block; opacity: 1; }
    
    .dock-item:hover { color: white; }
    .dock-item.active { color: var(--accent); }
    .dock-item.active::before {
        content: ''; position: absolute; left: 0; top: 10%; height: 80%; width: 4px;
        background: var(--accent); border-radius: 0 4px 4px 0;
        box-shadow: 2px 0 10px var(--accent);
    }

    #dock-footer { margin-top: auto; padding: 0 20px; font-size: 10px; color: #475569; text-align: center; white-space: nowrap; width: 100%; opacity: 0; transition: opacity 0.3s; }
    #dock-container:hover #dock-footer { opacity: 1; }

    /* --- CONTENT AREA --- */
    #content-area {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        padding-left: 0; /* Full screen logic, UI overlays on top */
        overflow: hidden;
    }
    
    /* --- SPLASH & LOADER --- */
    #splash-screen { position: fixed; inset: 0; background: var(--bg-dark); z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .loader-bar-bg { width: 200px; height: 4px; background: #334155; border-radius: 99px; overflow: hidden; margin-top: 20px; }
    .loader-bar-fill { height: 100%; background: var(--accent); width: 0%; transition: width 0.2s; }
    
    /* OVERLAY GLOBAL LOADER */
    #processing-overlay {
        background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px);
        display: none; flex-direction: column; align-items: center; justify-content: center;
        position: fixed; inset: 0; z-index: 9000; color: white;
    }
    #processing-overlay.active { display: flex; animation: fadeIn 0.3s; }

    /* --- VIEWS --- */
    .view-section { width: 100%; height: 100%; position: absolute; top: 0; left: 0; display: none; opacity: 0; transition: opacity 0.4s ease; }
    .view-section.active { display: flex; opacity: 1; }
    
    #view-home { flex-direction: column; justify-content: center; align-items: center; background: radial-gradient(circle at top right, #1e293b 0%, #0f172a 60%); }
    .home-hero { text-align: center; margin-bottom: 40px; }
    .home-hero h1 { font-size: 42px; margin: 0; background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* --- TOAST NOTIFICATIONS --- */
    #toast-container { position: fixed; bottom: 20px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px; pointer-events: none; }
    .toast {
        pointer-events: auto;
        min-width: 300px;
        background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.1);
        border-left: 4px solid var(--accent);
        color: white; padding: 15px 20px; border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        font-size: 13px; font-weight: 500;
        display: flex; align-items: center; justify-content: space-between;
        animation: slideUp 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
        overflow: hidden; position: relative;
    }
    .toast.success { border-left-color: #4ade80; }
    .toast.error { border-left-color: #f87171; }
    .toast.info { border-left-color: #38bdf8; }
    
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
    @keyframes fadeOut { to { opacity: 0; transform: translateY(-10px); } }

    /* --- LEAFLET CUSTOMIZATION --- */
    .leaflet-bar { border: none !important; box-shadow: none !important; }
    .leaflet-control-zoom a {
        background-color: var(--bg-panel) !important; color: white !important;
        border-radius: 50% !important; border: 1px solid var(--glass-border) !important;
        width: 36px !important; height: 36px !important; line-height: 36px !important;
        margin-bottom: 8px !important;
        font-weight: 300 !important; font-size: 18px !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
    .leaflet-control-zoom a:hover {
        background-color: var(--accent) !important;
        border-color: var(--accent) !important;
        transform: scale(1.1);
    }

    /* --- TYPOGRAPHY REFINEMENT --- */
    .section-title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-muted);
        font-weight: 700;
        margin-top: 25px; margin-bottom: 15px;
        display: flex; align-items: center; gap: 10px;
    }
    .section-title::after {
        content: ''; flex: 1; height: 1px;
        background: linear-gradient(to right, rgba(255,255,255,0.1), transparent);
    }

    /* --- PANEL ANIMATIONS --- */
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .slide-in-panel { animation: slideInLeft 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
"""

def generate_html_content():
    logo_b64 = AssetManager.get_logo_b64()
    
    # Menu Items Generation
    menu_html = ""
    views_html = ""
    
    try:
        for module in ACTIVE_MODULES:
            info = module.TOOL_INFO
            mod_id = info['id']
            # Selection de l'icône SVG mappée ou fallback
            svg_icon = ICONS.get(mod_id, ICONS.get('geotoolbox'))
            
            menu_html += f"""
            <div class="dock-item" onclick="switchView('{mod_id}', this)">
                <div class="icon-box">{svg_icon}</div>
                <div class="label">{info['name']}</div>
            </div>
            """
            
            views_html += f"""
            <div id="view-{mod_id}" class="view-section">
                {module.get_ui_content()}
            </div>
            """
    except Exception as e:
        views_html = f"<div style='color:red; padding:40px;'>Erreur Generation UI: {e}</div>"

    app_ver = version.CURRENT_VERSION

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BURGEAPLY v{app_ver}</title>
    <!-- LEAFLET & DEPS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    
    <style>{GLOBAL_STYLES}</style>
</head>
<body>

<!-- SPLASH SCREEN -->
<div id="splash-screen">
    <img src="{logo_b64}" style="width: 80px; margin-bottom: 20px; animation: float 3s infinite;">
    <div style="font-weight: 600; font-size: 24px; color:white;">BURGEAPLY</div>
    <div style="color:var(--text-muted); font-size:12px; margin-top:5px;">v{app_ver}</div>
    <div class="loader-bar-bg"><div class="loader-bar-fill" id="splash-bar"></div></div>
</div>

<!-- PROCESS OVERLAY -->
<div id="processing-overlay">
    <div style="font-size: 40px; margin-bottom: 20px; animation: float 2s infinite;">⚙️</div>
    <div id="proc-title" style="font-weight: 700; font-size: 22px;">Traitement en cours</div>
    <div id="proc-desc" style="color: var(--text-muted); margin-top: 5px;">Veuillez patienter...</div>
    <div class="loader-bar-bg" style="width: 300px; background: rgba(255,255,255,0.1);">
        <div class="loader-bar-fill" id="proc-bar"></div>
    </div>
    <div id="proc-percent" style="margin-top: 10px; font-family: monospace; font-weight: bold; color: var(--accent);">0%</div>
</div>

<!-- TOAST CONTAINER -->
<div id="toast-container"></div>

<div id="app" style="opacity:0; transition: opacity 1s;">
    
    <!-- 1. CONTENT AREA (BACKGROUND) -->
    <div id="content-area">
        <!-- HOME VIEW -->
        <div id="view-home" class="view-section active">
            <div class="home-hero">
                <img src="{logo_b64}" style="width: 100px; margin-bottom: 30px;">
                <h1>BURGEAPLY</h1>
                <p style="color: var(--text-muted); max-width: 400px; margin: 10px auto; line-height: 1.6;">
                    Plateforme d'ingénierie environnementale avancée.<br>
                    Exploration BSS, Cartographie et Outils SSP.
                </p>
                <div style="margin-top: 40px;">
                    <button class="btn-glow" onclick="switchView('geotoolbox', document.querySelectorAll('.dock-item')[1])">
                        {ICONS['geotoolbox']} Lancer GéoToolbox
                    </button>
                </div>
            </div>
        </div>
        
        {views_html}
    </div>

    <!-- 2. FLOATING DOCK (FOREGROUND) -->
    <div id="dock-container" class="glass-panel">
        <div class="dock-logo">
            <img src="{logo_b64}">
            <div class="dock-title">BURGEAPLY</div>
        </div>
        
        <div class="dock-item active" onclick="switchView('home', this)">
            <div class="icon-box">{ICONS['home']}</div>
            <div class="label">Accueil</div>
        </div>
        
        {menu_html}
        
        <div id="dock-footer">
            v{app_ver}<br>
            Développé par Laurent BRIGAUD<br>
            Idée originale : Amine El Mahlali<br>
            GINGER BURGEAP
        </div>
    </div>

</div>

<script>
    // --- GLOBAL SHARED STATE ---
    window.SHARED_STATE = {{
        viewport: null, // {{ center: {{lat, lng}}, zoom: int }}
        selection: null // {{ lat: float, lng: float }}
    }};

    function updateSharedState(viewport, selection) {{
        if(viewport) window.SHARED_STATE.viewport = viewport;
        if(selection) window.SHARED_STATE.selection = selection;
    }}

    function getSharedState() {{
        return window.SHARED_STATE;
    }}

    function smartPanTo(map, latlng, zoom) {{
        // Centre la carte en tenant compte de la sidebar (approx 400px)
        // On veut que le point soit centré dans l'espace restant à droite.
        // Screen Center X = W/2. Target X = 400 + (W-400)/2 = 200 + W/2.
        // Diff = +200px.
        // Donc on doit déplacer le contenu de +200px vers la droite.
        // Leaflet panBy(-x) déplace la vue vers la gauche (donc contenu vers droite).
        
        map.setView(latlng, zoom || map.getZoom(), {{ animate: false }});
        map.panBy([-250, 0], {{ animate: true, duration: 0.5 }});
    }}

    // --- SCRIPTS SYSTEM ---
    window.onload = function() {{
        let p = 0; const bar = document.getElementById('splash-bar');
        const interval = setInterval(() => {{
            p += 4; bar.style.width = p + '%';
            if (p >= 100) {{ 
                clearInterval(interval); 
                document.getElementById('splash-screen').style.opacity = '0';
                setTimeout(() => {{
                    document.getElementById('splash-screen').style.display = 'none';
                    document.getElementById('app').style.opacity = '1';
                    
                    // Trigger map resize if hidden
                    window.dispatchEvent(new Event('resize'));

                    setTimeout(() => {{
                        if (typeof pywebview !== 'undefined' && pywebview.api) {{
                            pywebview.api.check_updates_ui();
                        }}
                    }}, 1000);
                }}, 600);
            }}
        }}, 30);
    }};

    function showToast(type, message, duration = 4000) {{
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${{type}}`;

        // Icones selon le type
        let icon = '';
        if(type === 'success') icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
        if(type === 'error') icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

        toast.innerHTML = `
            <div style="display:flex; align-items:center; gap:10px;">${{icon}} <span>${{message}}</span></div>
            <div style="position:absolute; bottom:0; left:0; height:3px; background:rgba(255,255,255,0.3); width:100%; animation: timeBar ${{duration}}ms linear forwards;"></div>
        `;

        // Style animation barre
        const style = document.createElement('style');
        style.innerHTML = `@keyframes timeBar {{ from {{ width: 100%; }} to {{ width: 0%; }} }}`;
        toast.appendChild(style);

        container.appendChild(toast);

        // Auto remove
        setTimeout(() => {{
            toast.style.animation = 'fadeOut 0.5s forwards';
            setTimeout(() => toast.remove(), 500);
        }}, duration);
    }}

    function switchView(viewId, menuEl) {{
        document.querySelectorAll('.dock-item').forEach(el => el.classList.remove('active'));
        if(menuEl) menuEl.classList.add('active');
        
        document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
        const target = document.getElementById('view-' + viewId);
        if(target) {{
            target.classList.add('active');
            // Hack Leaflet pour redessiner la map si elle devient visible
            setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
        }}
        
        if (typeof window['init_' + viewId] === 'function') try {{ window['init_' + viewId](); }} catch(e) {{}}
    }}

    function browseFolder() {{
        pywebview.api.select_directory().then(p => {{ if(p) document.getElementById('targetPath').value = p; }});
    }}

    function showLoader(title) {{
        document.getElementById('processing-overlay').classList.add('active');
        document.getElementById('proc-title').innerText = title;
        updateLoader(0, "Initialisation...");
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
    def run_save_map(self, b64, path): return geotoolbox.save_map_image(b64, path)

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
    window_title = f'BURGEAPLY v{version.CURRENT_VERSION}'
    
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