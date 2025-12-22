from modules import version

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

    return f"""
    <style>
        .about-container {{
            max-width: 800px; margin: 0 auto; padding: 40px; color: #f1f5f9;
        }}
        .app-header {{
            text-align: center; margin-bottom: 50px;
            background: #1e293b; padding: 30px; border-radius: 16px; border: 1px solid #334155;
        }}
        .app-title {{ font-size: 32px; font-weight: 800; color: #38bdf8; margin: 0; }}
        .app-desc {{ color: #94a3b8; margin-top: 10px; font-size: 14px; line-height: 1.6; }}
        
        .current-ver {{ 
            display: inline-block; margin-top: 15px; padding: 5px 15px; 
            background: rgba(56, 189, 248, 0.1); color: #38bdf8; 
            border-radius: 20px; font-weight: bold; font-size: 12px; border: 1px solid rgba(56, 189, 248, 0.2);
        }}

        h3 {{ border-bottom: 2px solid #334155; padding-bottom: 10px; color: #cbd5e1; margin-top: 40px; }}

        /* TIMELINE STYLE */
        .version-block {{
            margin-bottom: 25px; padding-left: 20px; border-left: 2px solid #334155;
            position: relative;
        }}
        .version-block::before {{
            content: ''; position: absolute; left: -6px; top: 0; width: 10px; height: 10px;
            background: #64748b; border-radius: 50%;
        }}
        .version-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
        .version-tag {{ 
            padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: white; 
        }}
        .version-date {{ font-size: 12px; color: #64748b; font-style: italic; }}
        
        .version-list {{ margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 13px; }}
        .version-list li {{ margin-bottom: 4px; }}
        
        .credits {{ font-size: 12px; color: #64748b; margin-top: 30px; border-top: 1px solid #334155; padding-top: 20px; line-height: 1.6; }}
        .credits b {{ color: #e2e8f0; }}
    </style>

    <div class="about-container">
        
        <div class="app-header">
            <div style="font-size:40px; margin-bottom:10px;">🔷</div>
            <h1 class="app-title">Burgeaply Hub</h1>
            <div class="current-ver">Version {version.CURRENT_VERSION}</div>
            <p class="app-desc">
                Une suite d'outils dédiée à l'ingénierie environnementale.<br>
                Développé pour simplifier l'accès aux données géographiques et historiques.
            </p>
            
            <div class="credits">
                Développé par <b>Laurent BRIGAUD</b><br>
                Idée originale de <b>Amine El Mahlali</b><br>
                <span style="color:#38bdf8; font-weight:bold; letter-spacing:0.5px;">Ginger BURGEAP</span>
            </div>
        </div>

        <h3>📜 Historique des mises à jour</h3>
        <div class="changelog-feed">
            {changelog_html}
        </div>

    </div>
    """