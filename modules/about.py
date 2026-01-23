from modules import version, core

# ==========================================
# 1. META-DONNÉES
# ==========================================
TOOL_INFO = {
    "id": "about",
    "name": "À Propos",
    "icon": "ℹ️",
    "description": "Version et nouveautés"
}

# ==========================================
# 2. UI GENERATOR
# ==========================================
def get_ui_content():

    # Génération du HTML du Changelog
    changelog_html = ""

    for log in version.CHANGELOG:
        badge_color = "#3b82f6"
        if log['type'] == 'major': badge_color = "#f59e0b"
        if log['type'] == 'patch': badge_color = "#10b981"

        li_items = "".join([f"<li>{c}</li>" for c in log['changes']])

        changelog_html += f"""
        <div class="version-block">
            <div class="version-header">
                <span class="version-tag" style="background:{badge_color}">v{log['version']}</span>
                <span class="version-date">{log['date']}</span>
            </div>
            <ul class="version-list">
                {li_items}
            </ul>
        </div>
        """

    # Load Template
    template = core.load_template("about.html")

    # Injection
    html = template.replace("{{VERSION}}", version.CURRENT_VERSION)
    html = html.replace("{{CHANGELOG_HTML}}", changelog_html)
    html = html.replace("{{LOGO_B64}}", core.get_logo_b64())

    return html
