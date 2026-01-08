import os
import sys
import json
import logging
import webbrowser
from typing import List, Dict, Any, Optional, Union

import webview
from modules import geotoolbox, orthohisto, feedback, about, version, core, updater, autolabo

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Priority: Env Var > Config.json > Default False
_env_debug = os.environ.get('BURGEAPLY_DEBUG')
if _env_debug is not None:
    DEBUG_MODE = _env_debug.lower() == 'true'
else:
    # Ensure core is init to load config
    core.init() 
    DEBUG_MODE = core.CONFIG.get('app', {}).get('debug', False)

# Module Interface Protocol (informal)
# Expected: module.TOOL_INFO (dict), module.get_ui_content() (str)
ACTIVE_MODULES: List[Any] = [
    geotoolbox,
    orthohisto,
    autolabo,
    feedback,
    about
]

# ==========================================
# 2. API ROUTER
# ==========================================
class BurgeaplyApi:
    """
    Main Bridge API exposed to JavaScript.
    Handles UI requests and dispatches them to appropriate modules.
    """

    def get_initial_content(self) -> Dict[str, str]:
        """
        Returns the HTML content for the dynamic parts of the UI.
        This allows the frontend to be static while still loading dynamic modules.
        """
        menu_html: str = ""
        views_html: str = ""

        # SVG Icons mapping
        icons: Dict[str, str] = {
            "geotoolbox": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>""",
            "orthohisto": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
            "autolabo": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.31"/><path d="M14 2v7.31"/><path d="M8.5 2h7"/><path d="M14 9.3a6.5 6.5 0 1 1-4 0"/><path d="M5.52 16h12.96"/></svg>""",

            "feedback": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>""",
            "about": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>"""
        }

        try:
            for module in ACTIVE_MODULES:
                info: Dict[str, Any] = getattr(module, 'TOOL_INFO', {})
                if not info:
                    continue

                mod_id: str = info.get('id', 'unknown')
                mod_name: str = info.get('name', 'Module')
                svg_icon: str = icons.get(mod_id, icons.get('geotoolbox', ''))

                menu_html += f"""
                <div class="dock-item" onclick="switchView('{mod_id}', this)">
                    <div class="icon-box">{svg_icon}</div>
                    <div class="label">{mod_name}</div>
                </div>
                """

                # Safe execution of ui content generation
                content_method = getattr(module, 'get_ui_content', lambda: "")
                views_html += f"""
                <div id="view-{mod_id}" class="view-section">
                    {content_method()}
                </div>
                """

        except Exception as e:
            logging.error(f"Error generating UI content: {e}")
            return {"error": str(e)}

        return {
            "menu_html": menu_html,
            "views_html": views_html,
            "version": version.CURRENT_VERSION
        }

    def select_directory(self) -> Optional[str]:
        """Opens a native directory selection dialog."""
        w = webview.active_window()
        if not w:
            return None
        res = w.create_file_dialog(webview.FileDialog.FOLDER)
        return res[0] if res else None

    def select_files(self) -> List[str]:
        """Opens a native file selection dialog."""
        w = webview.active_window()
        if not w:
            return []
        # Allow multiple files, compatible with Lab formats
        file_types = ('Fichiers Labo (*.xlsx;*.xls;*.csv)', 'Tous les fichiers (*.*)')
        res = w.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=file_types)
        return res if res else []

    def open_file(self, file_path: str) -> bool:
        """Opens a file with the default system application."""
        try:
            if os.path.exists(file_path):
                os.startfile(file_path)
                return True
            return False
        except Exception as e:
            logging.error(f"Error opening file: {e}")
            return False

    def open_folder(self, file_path: str) -> bool:
        """Opens the folder containing the file and selects it."""
        try:
            if os.path.exists(file_path):
                # Windows: explorer /select,<path>
                import subprocess
                subprocess.run(['explorer', '/select,', file_path])
                return True
            return False
        except Exception as e:
            logging.error(f"Error opening folder: {e}")
            return False

    # --- GEOTOOLBOX PROXIES ---
    def run_preview(self, bbox: Dict[str, float], layers: List[str]) -> List[Dict[str, Any]]:
        """Proxy for Geotoolbox Preview Logic"""
        # Context7 recommends validation here ideally
        return geotoolbox.run_preview_logic(bbox, layers)

    def run_export(self, bbox: Dict[str, float], layers: List[str], folder: str, path: str) -> Dict[str, Any]:
        """Proxy for Geotoolbox Export Logic"""
        return geotoolbox.run_export_logic(bbox, layers, folder, path)

    def run_save_map(self, b64: str, path: str) -> Optional[str]:
        """Proxy for saving map images"""
        return geotoolbox.save_map_image(b64, path)

    # --- ORTHOHISTO PROXIES ---
    def run_full_process(self, lat: float, lon: float, radius: int, path: str) -> Dict[str, Any]:
        """Proxy for Orthohisto Full Process"""
        def progress_callback(percent: float, msg: str) -> None:
            # Architecture Decoupling: Use generic event dispatch
            # JS side: window.addEventListener('loader_update', e => updateLoader(e.detail.percent, e.detail.message))
            core.dispatch_event('loader_update', {'percent': percent, 'message': msg})

        return orthohisto.run_full_process(lat, lon, radius, path, progress_callback)

    # --- FEEDBACK PROXIES ---
    def run_send_feedback(self, category: str, message: str, trigram: str, contact: str) -> bool:
        """Proxy for Feedback sending"""
        return feedback.send_discord_feedback(category, message, trigram, contact)

    # --- UPDATER PROXIES ---
    def check_updates_ui(self) -> None:
        """Checks for updates and prompts user if available."""
        try:
            update_info = updater.check_for_updates()
            if update_info and update_info.get('has_update'):
                w = webview.active_window()
                if w:
                    msg = (f"Une nouvelle version v{update_info.get('remote')} est disponible !\n\n"
                           f"Nouveautés :\n{update_info.get('message')}\n\n"
                           "Voulez-vous la télécharger maintenant ?")
                    choice = w.create_confirmation_dialog("Mise à jour disponible", msg)
                    if choice:
                        webbrowser.open(update_info.get('url', ''))
        except Exception as e:
            logging.error(f"Error checking updates: {e}")

    # --- AUTOLABO PROXIES ---
    # --- AUTOLABO PROXIES ---
    def run_autolabo_process(self, file_paths: Union[str, List[str]], model_id: str = "es", target_path: str = "", provider_id: str = "agrolab") -> Dict[str, Any]:
        """Proxy for AutoLabo Processing
        
        Args:
            file_paths: Path(s) to raw lab file(s)
            model_id: Matrix ID (es, sols, sup)
            target_path: Optional target directory
            provider_id: Laboratory provider ID (agrolab, eurofins)
        """
        # Ensure list
        if isinstance(file_paths, str):
            file_paths = [file_paths]
            
        # Dispatch Loader Event
        core.dispatch_event('loader_update', {'percent': 10, 'message': 'Analyse des fichiers...'})
        try:
            result = autolabo.process_and_export(file_paths, model_id, target_path, provider_id)
            core.dispatch_event('loader_update', {'percent': 100, 'message': 'Terminé !'})
            return result
        except Exception as e:
            logging.error(f"AutoLabo Error: {e}")
            core.dispatch_event('loader_hide', {})
            return {"success": False, "error": str(e)}



if __name__ == '__main__':
    # Core Initialization (already called above for DEBUG_MODE but safe to ensure)
    # core.init() is idempotent enough or we can skip if we trust the above.
    # actually, let's keep it safe. If core.init is called twice, we should ensure it's safe. 
    # But wait, core.init reloads config. Let's just comment it out or leave it if safe.
    # The previous edit called core.init() at module level? No, at global scope execution time?
    # Yes, lines 11-15 run on import/exec. 
    # Let's remove this one to avoid double log init.
    pass
    api = BurgeaplyApi()
    window_title = f'BURGEAPLY v{version.CURRENT_VERSION}'

    # Path Resolution
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    assets_dir = os.path.join(base_path, 'assets')

    # Security: Using context7 best practices
    # 1. SSL could be enabled if certificates were available, defaulting to standard HTTP server for local app.
    # 2. Debug mode controlled by environment.

    window = webview.create_window(
        window_title,
        url='assets/index.html',
        js_api=api,
        width=1300,
        height=900
    )

    webview.start(
        gui='edge',
        debug=DEBUG_MODE,
        http_server=True
    )