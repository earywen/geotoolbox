import os

TOOL_INFO = {
    'id': 'organigramme',
    'name': 'Organigramme'
}

def get_ui_content():
    """Returns the HTML content for the module."""
    # Robust path finding
    base_path = os.getcwd()
    template_path = os.path.join(base_path, 'assets', 'templates', 'organigramme.html')
    
    # Fallback if running from a different context
    if not os.path.exists(template_path):
        # Try relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels: modules/organigramme -> root
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        template_path = os.path.join(root_dir, 'assets', 'templates', 'organigramme.html')

    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"<div class='p-10 text-red-500'>Erreur: Template introuvable à {template_path}</div>"
