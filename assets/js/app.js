/**
 * BURGEAPLY JS CORE
 * Refactored for ES6+ and Modularity
 */

// Global Namespace
window.Burgeaply = {
    state: {
        viewport: null, // { center: {lat, lng}, zoom: int }
        selection: null // { lat: float, lng: float }
    },

    // Core Methods
    updateState(viewport, selection) {
        if (viewport) this.state.viewport = viewport;
        if (selection) this.state.selection = selection;
    },

    getState() {
        return this.state;
    }
};

// Legacy Global Accessors (for compatibility with Geotoolbox.js)
window.SHARED_STATE = window.Burgeaply.state;
window.updateSharedState = (v, s) => window.Burgeaply.updateState(v, s);
window.getSharedState = () => window.Burgeaply.getState();

/**
 * Smart Pan Helper
 */
function smartPanTo(map, latlng, zoom) {
    // Centre la carte en tenant compte de la sidebar (approx 400px)
    map.setView(latlng, zoom || map.getZoom(), { animate: false });
    map.panBy([-250, 0], { animate: true, duration: 0.5 });
}
window.smartPanTo = smartPanTo; // Expose for modules

// --- LOADING MANAGER ---
const LoadingManager = {
    progress: 0,
    interval: null,

    start() {
        // Start indeterminate loading (trickle up to 90%)
        if (this.interval) clearInterval(this.interval);
        this.interval = setInterval(() => {
            if (this.progress < 90) {
                // Decaying increment
                const increment = (95 - this.progress) * 0.05;
                this.progress += (increment < 0.1 ? 0.1 : increment);
                this.updateUI();
            }
        }, 50);
    },

    complete() {
        if (this.interval) clearInterval(this.interval);
        this.progress = 100;
        this.updateUI();

        // Remove splash after short delay
        setTimeout(() => {
            const splash = document.getElementById('splash-screen');
            if (splash) {
                splash.style.opacity = '0';
                setTimeout(() => {
                    splash.style.display = 'none';
                    const app = document.getElementById('app');
                    if (app) app.style.opacity = '1';
                    window.dispatchEvent(new Event('resize'));
                }, 600);
            }
        }, 400);
    },

    updateUI() {
        const bar = document.getElementById('splash-bar');
        if (bar) bar.style.width = this.progress + '%';
    }
};

// Start loading animation immediately on script load
LoadingManager.start();

/**
 * PYWEBVIEW ENTRY POINT
 */
window.addEventListener('pywebviewready', function () {
    console.log("[Core] PyWebView Ready");

    // Initial Load of Views from Python API
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.get_initial_content()
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                if (data.menu_html) {
                    const dock = document.getElementById('dock-menu-placeholder');
                    if (dock) dock.innerHTML = data.menu_html;
                }
                if (data.views_html) {
                    const content = document.getElementById('content-area-placeholder');
                    if (content) content.innerHTML = data.views_html;
                }
                if (data.version) {
                    const vList = ['app-version', 'dock-footer-version'];
                    vList.forEach(id => {
                        const el = document.getElementById(id);
                        if (el) el.innerText = 'v' + data.version;
                    });
                    document.title = 'BURGEAPLY v' + data.version;
                }

                // Finish loading
                LoadingManager.complete();

                // Check Updates safely
                setTimeout(() => window.pywebview.api.check_updates_ui(), 1000);
            })
            .catch(err => {
                console.error("Critical Error loading UI:", err);
                showToast('error', "Erreur chargement interface: " + err, 10000);
            });

        // EVENT DRIVEN ARCHITECTURE LISTENERS
        window.addEventListener('loader_update', (e) => {
            if (e.detail) {
                window.updateLoader(e.detail.percent, e.detail.message);
            }
        });

        window.addEventListener('loader_hide', () => {
            window.hideLoader();
        });

        // AutoLabo Step Progress Listener
        window.addEventListener('autolabo_step', (e) => {
            if (e.detail && e.detail.step) {
                const stepLabel = document.getElementById('step-label');
                if (stepLabel) {
                    stepLabel.innerText = e.detail.step;
                }
                // Also add to logs
                const logsBox = document.getElementById('autolabo-logs');
                if (logsBox) {
                    const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    const div = document.createElement('div');
                    div.innerText = `[${time}] ${e.detail.step}`;
                    logsBox.appendChild(div);
                    logsBox.scrollTop = logsBox.scrollHeight;
                }
            }
        });

    } else {
        console.error("PyWebView API not found. Are we running in the browser?");
    }
});


/**
 * UI UTILITIES
 */

// Toast Notification System
window.showToast = function (type, message, duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Icons
    let icon = '';
    if (type === 'success') icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
    if (type === 'error') icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

    toast.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">${icon} <span>${message}</span></div>
        <div style="position:absolute; bottom:0; left:0; height:3px; background:rgba(255,255,255,0.3); width:100%; animation: timeBar ${duration}ms linear forwards;"></div>
    `;

    // Dynamic Style for animation
    const style = document.createElement('style');
    style.innerHTML = `@keyframes timeBar { from { width: 100%; } to { width: 0%; } }`;
    toast.appendChild(style);

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.5s forwards';
        setTimeout(() => toast.remove(), 500);
    }, duration);
};

// View Switcher
window.switchView = function (viewId, menuEl) {
    document.querySelectorAll('.dock-item').forEach(el => el.classList.remove('active'));
    if (menuEl) menuEl.classList.add('active');

    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    const target = document.getElementById('view-' + viewId);
    if (target) {
        target.classList.add('active');
        // Force Leaflet/Map resize
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
    }

    // Execute legacy init function if exists
    const initFn = window['init_' + viewId];
    if (typeof initFn === 'function') {
        try { initFn(); } catch (e) { console.warn(`Error init ${viewId}`, e); }
    }
};

// Directory Browser
window.browseFolder = function () {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.select_directory().then(p => {
            if (p) {
                const input = document.getElementById('targetPath');
                if (input) input.value = p;
            }
        });
    }
};

/**
 * LOADING OVERLAY METHODS (Called by Python)
 */
window.showLoader = function (title) {
    const overlay = document.getElementById('processing-overlay');
    if (overlay) overlay.classList.add('active');

    const t = document.getElementById('proc-title');
    if (t) t.innerText = title;

    window.updateLoader(0, "Initialisation...");
};

window.hideLoader = function () {
    setTimeout(() => {
        const overlay = document.getElementById('processing-overlay');
        if (overlay) overlay.classList.remove('active');
    }, 500);
};

window.updateLoader = function (percent, message) {
    const bar = document.getElementById('proc-bar');
    const txt = document.getElementById('proc-percent');
    const desc = document.getElementById('proc-desc');

    if (bar) bar.style.width = percent + '%';
    if (txt) txt.innerText = Math.round(percent) + '%';
    // message is already a string (Python sends JSON string which pywebview auto-deserializes for evaluate_js arguments? 
    // No, evaluate_js executes string code. We pass json.dumps(msg) in python -> which is a JS string literal.
    // So 'message' here is a string.
    if (message && desc) desc.innerText = message;
};

/**
 * AUTOLABO MODULE LOGIC
 */
let autoLaboFiles = [];

window.init_autolabo = function () {
    const dropzone = document.getElementById('autolabo-dropzone');
    if (!dropzone) return;

    // Guard: Prevent re-initializing listeners on repeated calls
    if (dropzone.dataset.initialized) {
        renderFileList();
        return;
    }
    dropzone.dataset.initialized = 'true';

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropzone.addEventListener('drop', handleDrop, false);

    // Click to browse (uses Python Native Dialog for full paths)
    dropzone.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.select_files().then(files => {
                if (files && files.length > 0) {
                    addFiles(files);
                }
            });
        }
    });

    renderFileList();
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    const dz = document.getElementById('autolabo-dropzone');
    if (dz) dz.classList.add('drag-active');
}

function unhighlight(e) {
    const dz = document.getElementById('autolabo-dropzone');
    if (dz) dz.classList.remove('drag-active');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    let paths = [];
    let hasPath = false;
    for (let i = 0; i < files.length; i++) {
        if (files[i].path) {
            paths.push(files[i].path);
            hasPath = true;
        }
    }

    if (hasPath) {
        addFiles(paths);
    } else {
        window.showToast('error', "Navigateur: Chemin introuvable (sécurité). Utilisez 'Parcourir'.");
    }
}

function addFiles(newFiles) {
    if (!newFiles || !Array.isArray(newFiles)) return;
    newFiles.forEach(path => {
        if (!autoLaboFiles.includes(path)) {
            autoLaboFiles.push(path);
        }
    });
    renderFileList();

    // Call Preview API for first file
    if (autoLaboFiles.length > 0 && window.pywebview && window.pywebview.api) {
        window.pywebview.api.preview_autolabo_file(autoLaboFiles[0])
            .then(preview => {
                const card = document.getElementById('preview-card');
                if (card && preview) {
                    document.getElementById('preview-samples').innerText = preview.samples || '-';
                    document.getElementById('preview-params').innerText = preview.parameters || '-';
                    document.getElementById('preview-provider').innerText = (preview.provider_guess || 'inconnu').toUpperCase();
                    card.style.display = 'block';
                }
            })
            .catch(err => {
                console.warn('Preview failed:', err);
                // Show error state in preview card
                const card = document.getElementById('preview-card');
                if (card) {
                    document.getElementById('preview-samples').innerText = '?';
                    document.getElementById('preview-params').innerText = '?';
                    document.getElementById('preview-provider').innerText = 'ERREUR';
                    card.style.display = 'block';
                }
            });
    }
}

window.removeFile = function (index) {
    autoLaboFiles.splice(index, 1);
    renderFileList();
}

function renderFileList() {
    const list = document.getElementById('file-list');
    const count = document.getElementById('file-count'); // Unused in new TPL?
    const btnProcess = document.getElementById('btn-process-autolabo');
    const btnPreview = document.getElementById('btn-preview-autolabo');

    if (!list) return;

    if (btnProcess) btnProcess.disabled = autoLaboFiles.length === 0;
    if (btnPreview) btnPreview.disabled = autoLaboFiles.length === 0;

    if (autoLaboFiles.length === 0) {
        list.innerHTML = `<div style="text-align: center; padding: 20px; opacity: 0.5;">Aucun fichier</div>`;
        return;
    }

    list.innerHTML = '';
    autoLaboFiles.forEach((file, index) => {
        const name = file.replace(/^.*[\\\/]/, '');
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <div class="name">${name}</div>
            <div class="remove" onclick="removeFile(${index})">✖</div>
        `;
        list.appendChild(div);
    });
}

// AutoLabo Folder Browser
window.autoLaboBrowseFolder = function () {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.select_directory().then(p => {
            if (p) {
                const input = document.getElementById('autolabo-target-path');
                if (input) input.value = p;
            }
        });
    }
};

window.runAutoLabo = function () {
    if (autoLaboFiles.length === 0) return;

    const logsBox = document.getElementById('autolabo-logs');
    const addLog = (msg) => {
        if (!logsBox) return;
        const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        logsBox.innerHTML += `<div>[${time}] ${msg}</div>`;
        logsBox.scrollTop = logsBox.scrollHeight;
    };

    // Clear and start
    if (logsBox) logsBox.innerHTML = '';
    addLog('🚀 Démarrage du traitement...');
    addLog(`📂 ${autoLaboFiles.length} fichier(s) à traiter`);

    // Get target path
    const targetPathInput = document.getElementById('autolabo-target-path');
    const targetPath = targetPathInput ? targetPathInput.value : '';
    if (targetPath) {
        addLog(`📁 Dossier cible: ${targetPath}`);
    }

    window.showLoader("Traitement de " + autoLaboFiles.length + " fichier(s)...");

    // Get provider
    const providerSelect = document.getElementById('provider-select');
    const providerId = providerSelect ? providerSelect.value : 'agrolab';
    const providerName = providerSelect ? providerSelect.options[providerSelect.selectedIndex].text : 'AGROLAB';
    addLog(`🧪 Laboratoire: ${providerName}`);

    // Get matrix
    const modelSelect = document.getElementById('matrix-select');
    const modelId = modelSelect ? modelSelect.value : 'es';
    addLog(`📋 Matrice: ${modelId === 'es' ? 'Eaux Souterraines' : modelId === 'sols' ? 'Sols' : 'Eaux de Surface'}`);

    // Prepare Options
    const options = {};
    if (activeRegulatoryHeaders.size > 0 || currentPreviewHeaders.length > 0) {
        options.active_headers = Array.from(activeRegulatoryHeaders);
        addLog(`🔧 Options: ${options.active_headers.length} colonnes réglem. actives`);
    }

    // Call new function name
    window.pywebview.api.process_autolabo(autoLaboFiles, modelId, targetPath, providerId, JSON.stringify(options))
        .then(res => {
            window.hideLoader();
            if (res.success) {
                addLog('✅ Rapport généré avec succès !');
                if (res.output_path) {
                    addLog(`📁 Fichier: ${res.output_path.split(/[\\/]/).pop()}`);

                    // Add action buttons
                    if (logsBox) {
                        const btnContainer = document.createElement('div');
                        btnContainer.style.cssText = 'display: flex; gap: 8px; margin-top: 10px;';
                        btnContainer.innerHTML = `
                            <button onclick="openAutoLaboFile('${res.output_path.replace(/\\/g, '\\\\')}')" 
                                style="flex: 1; padding: 8px; border-radius: 8px; border: none; background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); color: white; cursor: pointer; font-size: 11px; font-weight: 600;">
                                📄 Ouvrir le fichier
                            </button>
                            <button onclick="openAutoLaboFolder('${res.output_path.replace(/\\/g, '\\\\')}')" 
                                style="flex: 1; padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: white; cursor: pointer; font-size: 11px;">
                                📂 Ouvrir le dossier
                            </button>
                        `;
                        logsBox.appendChild(btnContainer);
                        logsBox.scrollTop = logsBox.scrollHeight;
                    }
                }
                window.showToast('success', "Rapport généré !");
                autoLaboFiles = [];
                renderFileList();
            } else {
                addLog(`❌ Erreur: ${res.error}`);
                window.showToast('error', "Erreur: " + res.error);
            }
        })
        .catch(err => {
            window.hideLoader();
            addLog(`❌ Erreur Backend: ${err}`);
            window.showToast('error', "Erreur Backend: " + err);
        });
};

// AutoLabo: Open generated file
window.openAutoLaboFile = function (filePath) {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_file(filePath);
    }
};

// AutoLabo: Open containing folder
window.openAutoLaboFolder = function (filePath) {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_folder(filePath);
    }
};

/**
 * CUSTOM RULES EDITOR
 */
window.openRulesEditor = function () {
    const modal = document.getElementById('rules-modal');
    const matrixSelect = document.getElementById('matrix-select');
    const label = document.getElementById('rules-matrix-label');

    if (modal && matrixSelect) {
        const matrix = matrixSelect.value;
        if (label) label.innerText = matrix === 'es' ? 'Eaux Souterraines' : (matrix === 'sols' ? 'Sols' : matrix);
        modal.style.display = 'flex';
        loadRules(matrix);
    }
}

window.closeRulesEditor = function () {
    const modal = document.getElementById('rules-modal');
    if (modal) modal.style.display = 'none';
}

function loadRules(matrix) {
    const list = document.getElementById('rules-list');
    if (!list) return;

    list.innerHTML = '<div style="text-align:center; color:#64748b; margin-top:20px;">Chargement...</div>';

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.get_custom_rules(matrix).then(rules => {
            renderRules(rules, matrix);
        });
    }
}

function renderRules(rules, matrix) {
    const list = document.getElementById('rules-list');
    if (!list) return;

    list.innerHTML = '';

    // Check if empty
    if (!rules || Object.keys(rules).length === 0) {
        list.innerHTML = '<div style="text-align: center; color: #64748b; margin-top: 50px;">Aucune règle personnalisée.</div>';
        return;
    }

    // Sort parameters alphabetically
    const params = Object.keys(rules).sort();

    params.forEach(param => {
        const specs = rules[param];
        Object.keys(specs).forEach(col => {
            const val = specs[col];
            const div = document.createElement('div');
            div.className = 'rule-item';
            div.innerHTML = `
                <div style="font-weight:600; color:#e2e8f0;">${param}</div>
                <div style="color:#94a3b8;">${col}</div>
                <div style="color:#38bdf8; font-family:monospace;">${val}</div>
                <div class="delete-rule" onclick="deleteRule('${matrix}', '${param}')">×</div>
            `;
            list.appendChild(div);
        });
    });
}

window.addRule = function () {
    const paramInput = document.getElementById('rule-param');
    const colSelect = document.getElementById('rule-col');
    const valInput = document.getElementById('rule-value');
    const matrixSelect = document.getElementById('matrix-select');

    if (!paramInput || !colSelect || !valInput || !matrixSelect) return;

    const param = paramInput.value.trim();
    const col = colSelect.value;
    const val = valInput.value;
    const matrix = matrixSelect.value;

    if (!param || !val) {
        window.showToast('error', 'Veuillez remplir tous les champs');
        return;
    }

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.set_custom_rule(matrix, param, col, parseFloat(val)).then(success => {
            if (success) {
                window.showToast('success', 'Règle ajoutée !');
                paramInput.value = '';
                valInput.value = '';
                loadRules(matrix);
            } else {
                window.showToast('error', 'Erreur lors de l\'enregistrement');
            }
        });
    }
}


// AutoLabo: Toggle Preview Mode
// AutoLabo: Toggle Preview Mode
window.togglePreviewMode = function (show) {
    const viewDrop = document.getElementById('view-drop-mode');
    const viewPreview = document.getElementById('view-preview-mode');

    if (viewDrop && viewPreview) {
        viewDrop.style.display = show ? 'none' : 'flex';
        viewPreview.style.display = show ? 'flex' : 'none';

        // Show/Hide config panel
        const configPanel = document.getElementById('preview-config-panel');
        if (configPanel) configPanel.style.display = show ? 'block' : 'none';
    }
};

// Globals for Preview State
let currentPreviewHeaders = [];
let activeRegulatoryHeaders = new Set();

// AutoLabo: Run Detailed Preview
window.runPreview = function () {
    if (autoLaboFiles.length === 0) return;

    // Use first file for now
    const file = autoLaboFiles[0];

    const providerSelect = document.getElementById('provider-select');
    const providerId = providerSelect ? providerSelect.value : 'auto';

    const modelSelect = document.getElementById('matrix-select');
    const modelId = modelSelect ? modelSelect.value : 'es';

    window.showLoader("Analyse en cours...");

    window.pywebview.api.analyze_preview(file, modelId, providerId)
        .then(res => {
            window.hideLoader();
            if (res.success) {
                // res.data is now { rows: [], regulatory_headers: [] }
                // Or if old format, handle it? Python changes are done.

                // Store headers
                currentPreviewHeaders = res.data.regulatory_headers || [];
                // Reset active headers to all
                activeRegulatoryHeaders = new Set(currentPreviewHeaders.map(h => h.id));

                renderPreviewTable(res.data.rows);
                togglePreviewMode(true);

                // Update provider if auto-detected
                if (res.provider && providerSelect && providerId === 'auto') {
                    providerSelect.value = res.provider.toLowerCase();
                    // Update label manually if needed, but select change usually enough?
                    // Need to trigger change event if logic depends on it.
                }
            } else {
                window.showToast('error', "Erreur Preview: " + res.error);
            }
        })
        .catch(err => {
            window.hideLoader();
            window.showToast('error', "Err: " + err);
        });
};

function renderPreviewTable(rows) {
    const tbody = document.getElementById('preview-tbody');
    const thead = document.getElementById('preview-thead');
    const togglesContainer = document.getElementById('preview-header-toggles');

    if (!tbody || !thead) return;

    // 1. Render Toggles
    if (togglesContainer) {
        togglesContainer.innerHTML = '';
        currentPreviewHeaders.forEach(h => {
            const label = document.createElement('label');
            label.style.cssText = 'display: flex; align-items: center; gap: 8px; cursor: pointer; background: rgba(0,0,0,0.2); padding: 5px 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1); font-size: 0.85em;';
            label.innerHTML = `
                <input type="checkbox" checked onchange="toggleRegulatoryHeader(${h.id}, this.checked)">
                <span style="color: ${h.color || '#fff'}">${h.title}</span>
            `;
            togglesContainer.appendChild(label);
        });
    }

    // 2. Render Header
    let headerHTML = `
        <th style="padding: 12px;">Paramètre Brut</th>
        <th style="padding: 12px;">Statut</th>
        <th style="padding: 12px;">Paramètre Référentiel</th>
    `;

    // Dynamic headers
    currentPreviewHeaders.forEach(h => {
        headerHTML += `<th class="col-reg-${h.id}" style="padding: 12px; color: ${h.color || '#ccc'}; min-width: 100px;">${h.title}</th>`;
    });

    headerHTML += `<th style="padding: 12px; text-align: right;">Valeurs (Ech. 1)</th>`;
    thead.innerHTML = `<tr style="background: rgba(255,255,255,0.05); text-align: left; color: #94a3b8;">${headerHTML}</tr>`;

    // 3. Render Rows
    tbody.innerHTML = '';
    let hasData = false;

    rows.forEach(row => {
        // Filter out unmatched (requested by user)
        // if (!row.matched) return;

        hasData = true;
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';

        // Status Color
        const statusColor = row.matched ? '#4ade80' : '#f87171';
        const statusIcon = row.matched ? '✅ Trouvé' : '❌ Inconnu';

        // Value (First Sample)
        const val = (row.samples && row.samples.length > 0) ? row.samples[0].value : '-';

        // Dynamic Regulatory Values
        let regColsHTML = '';
        currentPreviewHeaders.forEach(h => {
            // row.regulatory_values is a dict mapping ID (int) to value
            // But JSON keys are strings
            const regVal = (row.regulatory_values && row.regulatory_values[String(h.id)]) || '-';
            regColsHTML += `<td class="col-reg-${h.id}" style="padding: 12px; font-family: monospace; font-size: 0.9em;">${regVal}</td>`;
        });

        tr.innerHTML = `
            <td style="padding: 12px; color: #f1f5f9; font-family: monospace;">${row.raw_name || '?'}</td>
            <td style="padding: 12px; color: ${statusColor}; font-weight: 500;">${statusIcon}</td>
            <td style="padding: 12px; color: var(--text-muted);">${row.ref_name || '-'}</td>
            ${regColsHTML}
            <td style="padding: 12px; text-align: right; font-family: monospace;">${val !== null ? val : ''}</td>
        `;
        tbody.appendChild(tr);
    });

    if (!hasData) {
        tbody.innerHTML = `<tr><td colspan="${4 + currentPreviewHeaders.length}" style="padding: 20px; text-align: center; color: var(--text-muted);">Aucun paramètre correspondant trouvé.</td></tr>`;
    }
}

// Helper: Toggle Column Visibility
window.toggleRegulatoryHeader = function (headerId, isChecked) {
    if (isChecked) {
        activeRegulatoryHeaders.add(headerId);
    } else {
        activeRegulatoryHeaders.delete(headerId);
    }

    // Toggle DOM Column visibility
    const cells = document.querySelectorAll(`.col-reg-${headerId}`);
    cells.forEach(el => {
        el.style.display = isChecked ? 'table-cell' : 'none';
    });
};
