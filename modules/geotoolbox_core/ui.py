from typing import Dict, Any

def generate_checkboxes_html(layers_config: Dict[str, Any]) -> str:
    """Generates the HTML for layer checkboxes."""
    checkboxes_html = ""
    for k, c in layers_config.items():
        # Ensure values are safe strings
        color = c.get("color", "#000000")
        label = c.get("label", k)

        checkboxes_html += f'''
        <div class="checkbox-wrapper">
            <input type="checkbox" id="chk_{k}" value="{k}" checked>
            <label for="chk_{k}" style="color:{color}">{label}</label>
        </div>
        '''
    return checkboxes_html
