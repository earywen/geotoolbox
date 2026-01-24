import os
import sys
import json
import logging
import webbrowser
from typing import List, Dict, Any, Optional, Union

import webview
from modules import feedback, about, version, core, updater, autolabo, cartographie

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
    cartographie,
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
            "cartographie": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>""",
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

    # --- CARTOGRAPHIE PROXIES ---
    def run_carto_preview(self, bbox: Dict[str, float], layers: List[str]) -> List[Dict[str, Any]]:
        """Proxy for Cartographie Preview Logic"""
        return cartographie.run_preview_logic(bbox, layers)

    def run_carto_export(self, bbox: Dict[str, float], layers: List[str], folder: str, path: str, 
                         options: Dict[str, Any] = None, emprise: Dict[str, Any] = None) -> Dict[str, Any]:
        """Proxy for Cartographie unified export (vectors + rasters)."""
        return cartographie.run_export_logic(bbox, layers, folder, path, options, emprise_geojson=emprise)

    def browse_folder(self) -> Optional[str]:
        """Opens native folder selection dialog (alias for select_directory)."""
        return self.select_directory()

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
    def process_autolabo(self, file_paths: Union[str, List[str]], model_id: str, target_path: str = "", provider_id: str = "auto", options: Union[str, Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Process AutoLabo files with options.
        
        Args:
            file_paths: Path(s) to raw lab file(s)
            model_id: Matrix ID (es, sols, sup)
            target_path: Optional target directory
            provider_id: Laboratory provider ID (agrolab, eurofins)
            options: Optional processing options (passed as JSON string or dict)
        """
        # DEBUG: Log immediately on entry to trace pywebview issues
        logging.info(f"APP: process_autolabo ENTRY - files={file_paths}, model={model_id}, provider={provider_id}, options_type={type(options)}")
        
        # Handle options (JSON string from JS to avoid pywebview kwarg unpacking)
        final_options = {}
        
        if isinstance(options, str):
            try:
                final_options = json.loads(options)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to decode options JSON: {e}")
        elif isinstance(options, dict):
            final_options = options
        
        # Merge kwargs (fallback)
        if kwargs:
            final_options.update(kwargs)

        # Ensure list
        logging.info(f"APP: process_autolabo called with {len(file_paths) if isinstance(file_paths, list) else 1} files. Options: {final_options}")
        if isinstance(file_paths, str):
            file_paths = [file_paths]
            
        # Dispatch Loader Event
        core.dispatch_event('loader_update', {'percent': 10, 'message': 'Analyse des fichiers...'})
        try:
            result = autolabo.process_and_export(file_paths, model_id, target_path, provider_id, final_options)
            core.dispatch_event('loader_update', {'percent': 100, 'message': 'Terminé !'})
            return result
        except Exception as e:
            logging.error(f"AutoLabo Error: {e}")
            core.dispatch_event('loader_hide', {})
            return {"success": False, "error": str(e)}

    def preview_autolabo_file(self, file_path: str) -> Dict[str, Any]:
        """Preview a lab file before processing.
        
        Returns summary info: samples count, parameters count, detected provider.
        """
        try:
            return autolabo.preview_file(file_path)
        except Exception as e:
            logging.error(f"AutoLabo Preview Error: {e}")
            return {"samples": 0, "parameters": 0, "provider_guess": "erreur"}
            
    def analyze_preview(self, file_path: str, model_id: str, provider_id: str) -> Dict[str, Any]:
        """Perform a dry-run analysis for detailed preview.
        
        Args:
            file_path: Path to the lab file.
            model_id: Matrix model ID (es, sols, etc.)
            provider_id: Provider ID (agrolab, eurofins, etc.)
            
        Returns:
            Dict with success, data (list of rows), or error.
        """
        try:
            logging.info(f"APP: analyze_preview ENTRY - file={file_path}, model={model_id}, provider={provider_id}")
            result = autolabo.analyze_preview(file_path, model_id, provider_id)
            logging.info(f"APP: analyze_preview EXIT - success={result.get('success', False)}")
            return result
        except Exception as e:
            logging.error(f"Analyze Preview Error: {e}")
            return {"success": False, "error": str(e)}
            
    # --- CUSTOM RULES API ---
    def get_custom_rules(self, matrix: str) -> Dict[str, Any]:
        """Get all custom rules for a matrix."""
        try:
            from modules.autolabo_core.rules import RuleManager
            return RuleManager().get_rules(matrix)
        except Exception as e:
            logging.error(f"Error fetching rules: {e}")
            return {}
            
    def set_custom_rule(self, matrix: str, parameter: str, column: str, value: float) -> bool:
        """Set a custom rule."""
        try:
            from modules.autolabo_core.rules import RuleManager
            return RuleManager().set_rule(matrix, parameter, column, value)
        except Exception as e:
            logging.error(f"Error setting rule: {e}")
            return False
            
    def delete_custom_rule(self, matrix: str, parameter: str) -> bool:
        """Delete a custom rule."""
        try:
            from modules.autolabo_core.rules import RuleManager
            return RuleManager().delete_rule(matrix, parameter)
        except Exception as e:
            logging.error(f"Error deleting rule: {e}")
            return False
            return {"samples": 0, "parameters": 0, "provider_guess": "erreur"}



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