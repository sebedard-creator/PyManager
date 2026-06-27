function pymanager() {
    return {
        scripts: [],
        showAddModal: false,
        showLogModal: false,
        isEditing: false,
        editingId: null,
        newScript: { name: '', path: '', args: '', cwd: '', github_url: '', auto_start: false },
        
        currentLogScript: null,
        logs: [],
        ws: null,
        wsConnected: false,
        // Theme management
        theme: localStorage.getItem('theme') || 'dark',
        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', this.theme);
            localStorage.setItem('theme', this.theme);
        },
        pollingInterval: null,

        init() {
            // Apply saved theme on load
            document.documentElement.setAttribute('data-theme', this.theme);
            
            this.fetchScripts();
            // Poll for status updates every 2 seconds
            this.pollingInterval = setInterval(() => {
                this.fetchScripts();
            }, 2000);
        },

        async fetchScripts() {
            try {
                const res = await fetch('/api/scripts');
                if (res.ok) {
                    let data = await res.json();
                    // Tri alphabétique par nom (insensible à la casse)
                    data.sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' }));
                    this.scripts = data;
                }
            } catch (err) {
                console.error("Failed to fetch scripts:", err);
            }
        },

        async browseFile() {
            try {
                const res = await fetch('/api/browse');
                if (res.ok) {
                    const data = await res.json();
                    if (data.path) {
                        this.newScript.path = data.path;
                        
                        // Auto-fill CWD if it's empty
                        if (!this.newScript.cwd) {
                            // Extract directory from path
                            const parts = data.path.split(/[/\\]/);
                            parts.pop();
                            this.newScript.cwd = parts.join('\\');
                        }
                    }
                }
            } catch (err) {
                console.error("Failed to browse file:", err);
            }
        },

        async browseFolder() {
            try {
                const res = await fetch('/api/browse_folder');
                if (res.ok) {
                    const data = await res.json();
                    if (data.path) {
                        this.newScript.cwd = data.path;
                    }
                }
            } catch (err) {
                console.error("Failed to browse folder:", err);
            }
        },

        async browseArgsFile() {
            try {
                const res = await fetch('/api/browse');
                if (res.ok) {
                    const data = await res.json();
                    if (data.path) {
                        // Enclose in quotes if there are spaces, just in case
                        const pathToAdd = data.path.includes(' ') ? `"${data.path}"` : data.path;
                        if (this.newScript.args && this.newScript.args.trim() !== '') {
                            this.newScript.args += ' ' + pathToAdd;
                        } else {
                            this.newScript.args = pathToAdd;
                        }
                    }
                }
            } catch (err) {
                console.error("Failed to browse args file:", err);
            }
        },

        openEditModal(script) {
            this.isEditing = true;
            this.editingId = script.id;
            this.newScript = {
                name: script.name,
                path: script.path,
                args: script.args,
                cwd: script.cwd,
                github_url: script.github_url || '',
                auto_start: script.auto_start
            };
            this.showAddModal = true;
        },

        openAddModal() {
            this.isEditing = false;
            this.editingId = null;
            this.newScript = { name: '', path: '', args: '', cwd: '', github_url: '', auto_start: false };
            this.showAddModal = true;
        },

        async submitAddScript() {
            try {
                let res;
                if (this.isEditing) {
                    res = await fetch(`/api/scripts/${this.editingId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: this.editingId,
                            name: this.newScript.name,
                            path: this.newScript.path,
                            args: this.newScript.args,
                            cwd: this.newScript.cwd,
                            github_url: this.newScript.github_url,
                            auto_start: this.newScript.auto_start
                        })
                    });
                } else {
                    const id = this.newScript.name.toLowerCase().replace(/[^a-z0-9]/g, '-') + '-' + Date.now();
                    res = await fetch('/api/scripts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: id,
                            name: this.newScript.name,
                            path: this.newScript.path,
                            args: this.newScript.args,
                            cwd: this.newScript.cwd,
                            github_url: this.newScript.github_url,
                            auto_start: this.newScript.auto_start
                        })
                    });
                }
                
                if (res.ok) {
                    this.showAddModal = false;
                    await this.fetchScripts();
                } else {
                    alert("Erreur lors de la sauvegarde du script");
                }
            } catch (err) {
                console.error(err);
            }
        },

        async deleteScript(id) {
            if (!confirm("Voulez-vous vraiment supprimer ce script ?")) return;
            try {
                await fetch(`/api/scripts/${id}`, { method: 'DELETE' });
                await this.fetchScripts();
            } catch (err) {
                console.error(err);
            }
        },

        async startScript(id) {
            try {
                await fetch(`/api/scripts/${id}/start`, { method: 'POST' });
                // Optimistic UI update
                const script = this.scripts.find(s => s.id === id);
                if (script) script.is_running = true;
                setTimeout(() => this.fetchScripts(), 500); // re-sync
            } catch (err) {
                console.error(err);
            }
        },

        async stopScript(id) {
            try {
                await fetch(`/api/scripts/${id}/stop`, { method: 'POST' });
                // Optimistic UI update
                const script = this.scripts.find(s => s.id === id);
                if (script) {
                    script.is_running = false;
                    script.pid = null;
                }
                setTimeout(() => this.fetchScripts(), 500); // re-sync
            } catch (err) {
                console.error(err);
            }
        },

        // --- WebSocket Terminal Logic ---
        
        openLogModal(script) {
            this.currentLogScript = script;
            this.logs = [];
            this.showLogModal = true;
            this.connectWebSocket(script.id);
        },

        closeLogModal() {
            this.showLogModal = false;
            this.currentLogScript = null;
            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
            this.wsConnected = false;
        },

        connectWebSocket(scriptId) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/logs/${scriptId}`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.wsConnected = true;
            };
            
            this.ws.onmessage = (event) => {
                this.logs.push(event.data);
                this.scrollToBottom();
            };
            
            this.ws.onclose = () => {
                this.wsConnected = false;
                // Don't auto-reconnect here to keep it simple, 
                // the user just closes/opens the modal if they want.
            };
            
            this.ws.onerror = (err) => {
                console.error("WebSocket error:", err);
                this.wsConnected = false;
            };
        },

        scrollToBottom() {
            // Use nextTick to ensure DOM is updated before scrolling
            this.$nextTick(() => {
                if (this.$refs.terminalOutput) {
                    this.$refs.terminalOutput.scrollTop = this.$refs.terminalOutput.scrollHeight;
                }
            });
        }
    }
}
