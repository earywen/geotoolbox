
const orgChart = {
    chart: null,
    data: null,
    currentNodeId: null,

    // Default sample data
    defaultData: [
        { id: "1", parentId: null, name: "Directeur de Projet", role: "Directeur", imageUrl: "https://ui-avatars.com/api/?name=Directeur+Projet&background=4f46e5&color=fff" },
        { id: "2", parentId: "1", name: "Chef de Projet", role: "Manager", imageUrl: "https://ui-avatars.com/api/?name=Chef+Projet&background=0ea5e9&color=fff" },
        { id: "3", parentId: "1", name: "Expert Technique", role: "Expert", imageUrl: "https://ui-avatars.com/api/?name=Expert+Tech&background=10b981&color=fff" },
        { id: "4", parentId: "2", name: "Ingénieur d'Études", role: "Ingénieur", imageUrl: "https://ui-avatars.com/api/?name=Ingenieur&background=f59e0b&color=fff" }
    ],

    init: function () {
        console.log("Organigramme Init");
        this.data = JSON.parse(JSON.stringify(this.defaultData));
        this.render();
    },

    render: function () {
        if (!this.data || this.data.length === 0) return;

        // Clear container
        document.getElementById('org-chart-container').innerHTML = '';

        this.chart = new d3.OrgChart()
            .container('#org-chart-container')
            .data(JSON.parse(JSON.stringify(this.data)))
            .nodeId(d => String(d.id))
            .parentNodeId(d => {
                if (d.parentId === "" || d.parentId === null || d.parentId === undefined || d.parentId === "null") {
                    return null;
                }
                return String(d.parentId);
            })
            .nodeHeight(d => 100)
            .nodeWidth(d => 250)
            .childrenMargin(d => 50)
            .compactMarginBetween(d => 35)
            .compact(false)
            .onNodeClick(d => this.openModal(d))
            .nodeContent(function (d) {
                // Determine color based on depth or arbitrary logic if needed
                const color = '#4f46e5';
                return `
                    <div class="org-node-card" style="font-family: 'Inter', sans-serif; position:absolute; margin-top:-1px; margin-left:-1px; width:${d.width}px; height:${d.height}px;">
                        <div style="display:flex; align-items:center; padding: 16px; height: 100%; gap: 12px;">
                            <img src="${d.data.imageUrl || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(d.data.name) + '&background=random'}" style="border-radius: 50%; width: 56px; height: 56px; object-fit: cover; border: 2px solid rgba(255,255,255,0.1);" />
                            <div style="flex:1; overflow:hidden;">
                                <div style="font-size: 15px; color: #f1f5f9; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${d.data.name}</div>
                                <div style="font-size: 13px; color: #94a3b8; font-weight: 500; margin-top: 2px;">${d.data.role}</div>
                            </div>
                        </div>
                        <!-- Stripe decoration -->
                        <div style="position: absolute; left: 0; top: 12px; bottom: 12px; width: 4px; background-color: ${color}; border-radius: 0 4px 4px 0; box-shadow: 2px 0 8px ${color};"></div>
                    </div>
                `;
            })
            .render();

        this.chart.expandAll();

        // Enable Drag & Drop
        this.setupDragDrop();
    },

    setupDragDrop: function () {
        if (!this.chart) return;
        const self = this;

        // Select all nodes in the chart
        d3.selectAll('.node')
            .call(d3.drag()
                .on("start", function (event, d) {
                    this.isDragging = false;
                    this.startX = event.x;
                    this.startY = event.y;
                })
                .on("drag", function (event, d) {
                    if (!this.isDragging && (Math.abs(event.x - this.startX) > 5 || Math.abs(event.y - this.startY) > 5)) {
                        this.isDragging = true;
                        d3.select(this).raise().attr("opacity", 0.7);
                    }

                    if (this.isDragging) {
                        d3.select(this).attr("transform", `translate(${event.x}, ${event.y})`);
                    }
                })
                .on("end", function (event, d) {
                    d3.select(this).attr("opacity", 1);

                    if (!this.isDragging) {
                        self.openModal(d.data.id);
                        return;
                    }

                    d3.select(this).style("display", "none");
                    const elemBelow = document.elementFromPoint(event.sourceEvent.clientX, event.sourceEvent.clientY);
                    d3.select(this).style("display", "block");

                    if (!elemBelow) {
                        self.render();
                        return;
                    }

                    const targetNodeEl = elemBelow.closest('.node');
                    if (!targetNodeEl) {
                        self.render();
                        return;
                    }

                    const targetNodeData = d3.select(targetNodeEl).data()[0];
                    if (!targetNodeData) {
                        self.render();
                        return;
                    }

                    const sourceId = String(d.data.id);
                    const targetId = String(targetNodeData.data.id);

                    if (sourceId === targetId) {
                        self.render();
                        return;
                    }

                    console.log(`Dropped ${sourceId} on ${targetId}`);

                    if (self.isDescendant(sourceId, targetId)) {
                        alert("Impossible de déplacer un parent sous un de ses enfants.");
                        self.render();
                        return;
                    }

                    if (confirm(`Déplacer "${d.data.name}" sous "${targetNodeData.data.name}" ?`)) {
                        const nodeIndex = self.data.findIndex(n => String(n.id) === sourceId);
                        if (nodeIndex > -1) {
                            self.data[nodeIndex].parentId = targetId;
                            self.render();
                        }
                    } else {
                        self.render();
                    }
                })
            );
    },

    isDescendant: function (parentId, potentialChildId) {
        if (parentId === potentialChildId) return true;

        const children = this.data.filter(d => String(d.parentId) === String(parentId));
        for (const child of children) {
            if (String(child.id) === String(potentialChildId)) return true;
            if (this.isDescendant(child.id, potentialChildId)) return true;
        }
        return false;
    },

    fit: function () {
        if (this.chart) this.chart.fit();
    },

    // --- Node Editing ---

    openModal: function (nodeId) {
        if (typeof nodeId === 'object' && nodeId !== null) {
            nodeId = nodeId.data?.id || nodeId.id || nodeId;
        }

        console.log("Opening modal for ID:", nodeId);

        this.currentNodeId = nodeId;
        const nodeData = this.data.find(d => String(d.id) === String(nodeId));

        if (!nodeData) return;

        const form = document.getElementById('node-edit-form');
        form.nodeId.value = nodeData.id;
        form.name.value = nodeData.name;
        form.role.value = nodeData.role;
        form.imageUrl.value = nodeData.imageUrl || "";

        // Populate Parent Select
        const parentSelect = form.parentId;
        parentSelect.innerHTML = '<option value="">Aucun (Racine)</option>';

        this.data.forEach(node => {
            if (String(node.id) !== String(nodeData.id)) {
                const option = document.createElement('option');
                option.value = node.id;
                option.textContent = node.name + " (" + node.role + ")";
                if (String(node.id) === String(nodeData.parentId)) {
                    option.selected = true;
                }
                parentSelect.appendChild(option);
            }
        });

        if (!nodeData.parentId) parentSelect.value = "";

        document.getElementById('node-edit-modal').classList.add('open');
    },

    closeModal: function () {
        document.getElementById('node-edit-modal').classList.remove('open');
        this.currentNodeId = null;
    },

    updateNodeData: function (e) {
        e.preventDefault();
        const form = e.target;
        const nodeId = form.nodeId.value;

        const nodeIndex = this.data.findIndex(d => d.id === nodeId);
        if (nodeIndex > -1) {
            this.data[nodeIndex].name = form.name.value;
            this.data[nodeIndex].role = form.role.value;
            this.data[nodeIndex].imageUrl = form.imageUrl.value;

            let newParentId = form.parentId.value;
            if (newParentId === "") newParentId = null;

            this.data[nodeIndex].parentId = newParentId;

            this.render();
            this.closeModal();
        }
    },

    addNode: function () {
        const newId = Math.random().toString(36).substr(2, 9);
        let parentId = this.currentNodeId || (this.data.length > 0 ? this.data[0].id : null);

        if (typeof parentId === 'object') parentId = parentId.id || parentId.data?.id;

        if (!parentId && this.data.length > 0) {
            alert("Veuillez sélectionner un parent en cliquant sur sa carte.");
            return;
        }

        const newNode = {
            id: newId,
            parentId: parentId, // Null if it's the very first node
            name: "Nouveau Membre",
            role: "Poste",
            imageUrl: ""
        };

        this.data.push(newNode);
        this.render();

        setTimeout(() => this.openModal(newId), 500);
    },

    deleteCurrentNode: function () {
        if (!this.currentNodeId) return;

        const node = this.data.find(d => d.id === this.currentNodeId);
        if (!node.parentId && this.data.length > 1) {
            alert("Impossible de supprimer la racine s'il reste d'autres nœuds.");
            return;
        }

        if (confirm("Supprimer ce membre et tous ses descendants ?")) {
            const removeRecursive = (id) => {
                const children = this.data.filter(d => d.parentId === id);
                children.forEach(c => removeRecursive(c.id));
                this.data = this.data.filter(d => d.id !== id);
            };

            removeRecursive(this.currentNodeId);
            this.render();
            this.closeModal();
        }
    },

    // --- IO ---

    save: async function () {
        try {
            const content = JSON.stringify(this.data, null, 2);
            const path = await pywebview.api.save_file_dialog("organigramme.json");
            if (path) {
                const res = await pywebview.api.save_content(path, content);
                if (res.success) {
                    alert("Sauvegarde réussie !");
                } else {
                    alert("Erreur: " + res.error);
                }
            }
        } catch (e) {
            console.error(e);
            alert("Impossible de sauvegarder: " + e.message);
        }
    },

    load: async function () {
        try {
            const paths = await pywebview.api.select_files();
            if (paths && paths.length > 0) {
                const path = paths[0];
                const res = await pywebview.api.read_file_content(path);
                if (res.success) {
                    this.data = JSON.parse(res.data);
                    this.render();
                } else {
                    alert("Erreur de lecture: " + res.error);
                }
            }
        } catch (e) {
            console.error(e);
            alert("Erreur lors du chargement: " + e.message);
        }
    },

    exportPdf: function () {
        if (!this.chart) return;
        this.chart.exportImg({
            full: true,
            scale: 2,
            onLoad: (base64) => {
                const pdf = new jspdf.jsPDF({
                    orientation: 'landscape',
                });
                const imgProps = pdf.getImageProperties(base64);
                const pdfWidth = pdf.internal.pageSize.getWidth();
                const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

                pdf.addImage(base64, 'PNG', 0, 0, pdfWidth, pdfHeight);
                pdf.save('organigramme.pdf');
            }
        });
    }
};

// Bind form submit
// Init called by app.js when view is switched
window.init_organigramme = function () {
    console.log("Organigramme View Init");

    // Bind form event listener here, when the DOM is ready
    const form = document.getElementById('node-edit-form');
    if (form) {
        form.onsubmit = (e) => orgChart.updateNodeData(e);
    }

    // Initial render if empty or not initialized
    if (!orgChart.chart || !orgChart.data) {
        orgChart.init();
    } else {
        // Just refit if already exists
        setTimeout(() => orgChart.fit(), 200);
    }
};

// Expose to window for inline onclick handlers
window.orgChart = orgChart;
