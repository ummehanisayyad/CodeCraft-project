/**
 * CodeCraft Workbench Controller
 * Manages CodeMirror editor, AJAX compiler pipeline execution, tabbed output rendering,
 * Mermaid.js diagram generation, token filtering, and intermediate code displays.
 */

document.addEventListener('DOMContentLoaded', function () {
    const editorTextarea = document.getElementById('code-editor');
    if (!editorTextarea) return;

    // 1. Initialize CodeMirror
    const editor = CodeMirror.fromTextArea(editorTextarea, {
        mode: 'text/x-csrc',
        theme: 'dracula',
        lineNumbers: true,
        matchBrackets: true,
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: true,
        autoCloseBrackets: true,
        extraKeys: {
            "Ctrl-Enter": function () { runAnalysis(); },
            "Cmd-Enter": function () { runAnalysis(); }
        }
    });

    // Editor info updates
    function updateEditorStats() {
        const text = editor.getValue();
        const lineCount = editor.lineCount();
        const charCount = text.length;
        const statsEl = document.getElementById('editor-stats-pill');
        if (statsEl) {
            statsEl.textContent = `${lineCount} lines, ${charCount} chars`;
        }
    }
    editor.on('change', updateEditorStats);
    updateEditorStats();

    // 2. DOM Elements
    const runBtn = document.getElementById('btn-run-analysis');
    const clearBtn = document.getElementById('btn-clear-code');
    const modeSelect = document.getElementById('analysis-mode-select');
    const titleInput = document.getElementById('analysis-title-input');
    const optimizeCheck = document.getElementById('analysis-optimize-check');
    const presetSelect = document.getElementById('example-preset-select');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    // Output DOM containers
    const emptyState = document.getElementById('output-empty-state');
    const resultsContainer = document.getElementById('output-results-container');
    const statusBadge = document.getElementById('status-badge');
    const executionLatency = document.getElementById('execution-latency');
    const savedRecordLink = document.getElementById('saved-record-link');
    const timingsGrid = document.getElementById('timings-grid');

    // Tab content containers
    const tokensTableBody = document.getElementById('tokens-table-body');
    const tokensCountBadge = document.getElementById('tokens-count-badge');
    const tokenSearchInput = document.getElementById('token-search-input');
    const syntaxTreeContainer = document.getElementById('syntax-tree-mermaid');
    const syntaxTextTree = document.getElementById('syntax-text-tree');
    const syntaxJsonTree = document.getElementById('syntax-json-tree');
    const symbolTableBody = document.getElementById('symbol-table-body');
    const symbolCountBadge = document.getElementById('symbol-count-badge');
    const semanticAlerts = document.getElementById('semantic-alerts-container');
    const tacInstructionsContainer = document.getElementById('tac-instructions-container');
    const quadruplesTableBody = document.getElementById('quadruples-table-body');
    const tacCountBadge = document.getElementById('tac-count-badge');
    const optimizedTacContainer = document.getElementById('optimized-tac-container');
    const optimizationsList = document.getElementById('optimizations-list');
    const optimizationStats = document.getElementById('optimization-stats');
    const errorDiagnosticsContainer = document.getElementById('error-diagnostics-container');

    let currentTokens = [];

    // 3. Clear Button
    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            if (confirm('Clear the code editor?')) {
                editor.setValue('');
                titleInput.value = 'Custom Code Analysis';
                editor.focus();
            }
        });
    }

    // 4. Example Preset Loader
    if (presetSelect) {
        presetSelect.addEventListener('change', function () {
            const exampleId = this.value;
            if (!exampleId) return;

            fetch(`/api/examples/${exampleId}/`)
                .then(res => res.json())
                .then(data => {
                    editor.setValue(data.code);
                    titleInput.value = data.title;
                    if (data.expected_stage && modeSelect) {
                        modeSelect.value = data.expected_stage;
                    }
                    editor.focus();
                })
                .catch(err => {
                    console.error('Error loading preset:', err);
                });
        });
    }

    // 5. Run Analysis
    function runAnalysis() {
        const sourceCode = editor.getValue();
        if (!sourceCode.trim()) {
            alert('Please enter or select source code to analyze.');
            editor.focus();
            return;
        }

        const mode = modeSelect ? modeSelect.value : 'all';
        const title = (titleInput && titleInput.value.trim()) ? titleInput.value.trim() : 'Interactive Analysis';
        const optimize = optimizeCheck ? optimizeCheck.checked : true;

        // Button state
        runBtn.disabled = true;
        const originalBtnHtml = runBtn.innerHTML;
        runBtn.innerHTML = '<span class="spinner-pulse me-2"></span> Analyzing Pipeline...';

        fetch('/api/analyze/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                source_code: sourceCode,
                mode: mode,
                title: title,
                optimize: optimize
            })
        })
        .then(res => res.json())
        .then(data => {
            runBtn.disabled = false;
            runBtn.innerHTML = originalBtnHtml;
            renderResults(data);
        })
        .catch(err => {
            runBtn.disabled = false;
            runBtn.innerHTML = originalBtnHtml;
            console.error('Analysis request error:', err);
            alert('Server error while running compiler analysis. Please check console.');
        });
    }

    if (runBtn) {
        runBtn.addEventListener('click', runAnalysis);
    }

    // 6. Render Output Results
    function renderResults(data) {
        if (emptyState) emptyState.classList.add('d-none');
        if (resultsContainer) resultsContainer.classList.remove('d-none');

        // Status Badge & Header Info
        if (data.is_success) {
            statusBadge.className = 'badge bg-success px-3 py-2 text-white';
            statusBadge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Compilation Successful';
        } else {
            statusBadge.className = 'badge bg-danger px-3 py-2 text-white';
            statusBadge.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i> ${data.error_stage ? data.error_stage.toUpperCase() + ' ERROR' : 'ERROR'}`;
        }

        if (executionLatency) {
            executionLatency.textContent = `${data.total_time_ms} ms`;
        }

        // Saved history link
        if (savedRecordLink) {
            if (data.record_id) {
                savedRecordLink.innerHTML = `<a href="/history/${data.record_id}/" class="badge bg-indigo-500 text-white text-decoration-none py-2 px-3"><i class="bi bi-clock-history me-1"></i> Saved #REC-${data.record_id}</a>`;
            } else {
                savedRecordLink.innerHTML = '<span class="badge bg-secondary py-2 px-2 text-muted-2">Guest Run (Unsaved)</span>';
            }
        }

        // Render Phase Latencies
        if (timingsGrid && data.timings) {
            let html = '';
            for (const [phase, ms] of Object.entries(data.timings)) {
                const label = phase.replace('_ms', '').toUpperCase();
                html += `
                    <div class="col-6 col-md-3">
                        <div class="p-2 rounded bg-surface border border-subtle text-center">
                            <div class="small text-muted">${label}</div>
                            <div class="fw-bold text-cyan">${ms} ms</div>
                        </div>
                    </div>
                `;
            }
            timingsGrid.innerHTML = html;
        }

        // A. Render Tokens
        currentTokens = data.tokens || [];
        if (tokensCountBadge) tokensCountBadge.textContent = currentTokens.length;
        renderTokensTable(currentTokens);

        // B. Render Syntax AST
        renderSyntaxTree(data);

        // C. Render Symbol Table & Semantic Checks
        renderSymbolTable(data);

        // D. Render Intermediate Code (TAC & Quadruples)
        renderIntermediateCode(data);

        // E. Render Code Optimization
        renderOptimizations(data);

        // F. Render Error Diagnostics (if any)
        renderErrorDiagnostics(data);

        // Automatically switch to Errors tab if an error occurred
        if (!data.is_success) {
            const errorTabTrigger = document.querySelector('#tab-error-diagnostics-btn');
            if (errorTabTrigger) {
                const tab = new bootstrap.Tab(errorTabTrigger);
                tab.show();
            }
        }
    }

    // A1. Tokens Table Renderer
    function renderTokensTable(tokens) {
        if (!tokensTableBody) return;
        if (!tokens || tokens.length === 0) {
            tokensTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No tokens extracted.</td></tr>';
            return;
        }

        let html = '';
        tokens.forEach(tok => {
            const badgeClass = getTokenBadgeClass(tok.type);
            const isError = tok.type === 'INVALID';
            html += `
                <tr class="${isError ? 'table-danger' : ''}">
                    <td class="text-muted fw-bold">${tok.index}</td>
                    <td><code class="px-2 py-1 bg-code rounded text-info">${escapeHtml(tok.lexeme)}</code></td>
                    <td><span class="badge ${badgeClass}">${tok.type}</span></td>
                    <td>${tok.line}</td>
                    <td>${tok.column}</td>
                    <td class="small text-secondary">${escapeHtml(tok.description)}</td>
                </tr>
            `;
        });
        tokensTableBody.innerHTML = html;
    }

    function getTokenBadgeClass(type) {
        switch (type) {
            case 'KEYWORD': return 'badge-token-keyword';
            case 'IDENTIFIER': return 'badge-token-identifier';
            case 'INT_LITERAL': return 'badge-token-int';
            case 'FLOAT_LITERAL': return 'badge-token-float';
            case 'STRING_LITERAL': return 'badge-token-string';
            case 'CHAR_LITERAL': return 'badge-token-char';
            case 'OP_ARITHMETIC':
            case 'OP_RELATIONAL':
            case 'OP_LOGICAL':
            case 'OP_ASSIGNMENT':
            case 'OP_INCREMENT': return 'badge-token-operator';
            case 'SEPARATOR': return 'badge-token-separator';
            case 'COMMENT': return 'badge-token-comment';
            case 'INVALID': return 'badge-token-invalid';
            default: return 'bg-secondary';
        }
    }

    // Token Search Filter
    if (tokenSearchInput) {
        tokenSearchInput.addEventListener('input', function () {
            const q = this.value.toLowerCase().trim();
            if (!q) {
                renderTokensTable(currentTokens);
                return;
            }
            const filtered = currentTokens.filter(t => 
                t.lexeme.toLowerCase().includes(q) ||
                t.type.toLowerCase().includes(q) ||
                t.description.toLowerCase().includes(q)
            );
            renderTokensTable(filtered);
        });
    }

    // B1. Syntax Tree (Mermaid.js + ASCII + JSON)
    function renderSyntaxTree(data) {
        if (syntaxTextTree) {
            syntaxTextTree.textContent = data.text_tree || '(Syntax tree unavailable)';
        }
        if (syntaxJsonTree) {
            syntaxJsonTree.textContent = data.ast ? JSON.stringify(data.ast, null, 2) : '{\n  "ast": null\n}';
        }

        if (syntaxTreeContainer) {
            if (data.mermaid_graph && window.mermaid) {
                syntaxTreeContainer.innerHTML = `<div class="mermaid">${data.mermaid_graph}</div>`;
                try {
                    mermaid.init(undefined, syntaxTreeContainer.querySelectorAll('.mermaid'));
                } catch (e) {
                    console.warn('Mermaid rendering warning:', e);
                    syntaxTreeContainer.innerHTML = `<pre class="code-viewer-block">${escapeHtml(data.text_tree)}</pre>`;
                }
            } else if (data.text_tree) {
                syntaxTreeContainer.innerHTML = `<pre class="code-viewer-block">${escapeHtml(data.text_tree)}</pre>`;
            } else {
                syntaxTreeContainer.innerHTML = '<div class="text-muted p-4 text-center">Syntax Tree is empty or not generated.</div>';
            }
        }
    }

    // C1. Symbol Table & Semantic Diagnostics
    function renderSymbolTable(data) {
        if (symbolCountBadge) symbolCountBadge.textContent = (data.symbols || []).length;

        if (symbolTableBody) {
            const symbols = data.symbols || [];
            if (symbols.length === 0) {
                symbolTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No symbols declared.</td></tr>';
            } else {
                let html = '';
                symbols.forEach(sym => {
                    const initBadge = sym.is_initialized 
                        ? '<span class="badge bg-success-subtle text-success">Initialized</span>' 
                        : '<span class="badge bg-warning-subtle text-warning">Uninitialized</span>';
                    html += `
                        <tr>
                            <td><strong class="text-indigo">${escapeHtml(sym.name)}</strong></td>
                            <td><span class="badge bg-info-subtle text-info">${sym.type}</span></td>
                            <td>${sym.scope_name} (L${sym.scope_level})</td>
                            <td>Line ${sym.line}</td>
                            <td>${initBadge}</td>
                            <td>${sym.memory_bytes} B</td>
                            <td class="small text-muted">${sym.kind}</td>
                        </tr>
                    `;
                });
                symbolTableBody.innerHTML = html;
            }
        }

        // Semantic alerts (Errors & Warnings)
        if (semanticAlerts) {
            let html = '';
            const errs = data.semantic_errors || [];
            const warns = data.semantic_warnings || [];

            errs.forEach(err => {
                html += `
                    <div class="alert alert-danger py-2 px-3 mb-2 d-flex align-items-center">
                        <i class="bi bi-x-octagon-fill fs-5 me-2"></i>
                        <div><strong>Semantic Error:</strong> ${escapeHtml(err.message)} <span class="badge bg-dark ms-2">Line ${err.line}</span></div>
                    </div>
                `;
            });

            warns.forEach(w => {
                html += `
                    <div class="alert alert-warning py-2 px-3 mb-2 d-flex align-items-center">
                        <i class="bi bi-exclamation-triangle-fill fs-5 me-2"></i>
                        <div><strong>Warning:</strong> ${escapeHtml(w.message)} <span class="badge bg-dark ms-2">Line ${w.line}</span></div>
                    </div>
                `;
            });

            if (errs.length === 0 && warns.length === 0) {
                html = `
                    <div class="alert alert-success py-2 px-3 mb-0 d-flex align-items-center">
                        <i class="bi bi-check-circle-fill me-2"></i>
                        <div>Semantic validation passed without errors or warnings.</div>
                    </div>
                `;
            }
            semanticAlerts.innerHTML = html;
        }
    }

    // D1. Intermediate Code Generation
    function renderIntermediateCode(data) {
        const instrs = data.tac_instructions || [];
        const quads = data.quadruples || [];
        if (tacCountBadge) tacCountBadge.textContent = quads.length;

        if (tacInstructionsContainer) {
            if (instrs.length === 0) {
                tacInstructionsContainer.innerHTML = '<div class="text-muted p-4 text-center">No Three-Address Code generated.</div>';
            } else {
                let html = '<div class="p-3 font-monospace">';
                instrs.forEach((inst, idx) => {
                    html += `<div class="d-flex"><span class="text-muted me-3 user-select-none">${String(idx + 1).padStart(2, '0')}:</span><span class="text-light">${escapeHtml(inst)}</span></div>`;
                });
                html += '</div>';
                tacInstructionsContainer.innerHTML = html;
            }
        }

        if (quadruplesTableBody) {
            if (quads.length === 0) {
                quadruplesTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No quadruples produced.</td></tr>';
            } else {
                let html = '';
                quads.forEach(q => {
                    html += `
                        <tr>
                            <td class="text-muted fw-bold">(${q.index})</td>
                            <td><span class="badge bg-indigo-500">${q.op}</span></td>
                            <td><code class="text-info">${escapeHtml(q.arg1)}</code></td>
                            <td><code class="text-cyan">${escapeHtml(q.arg2)}</code></td>
                            <td><code class="text-warning">${escapeHtml(q.result)}</code></td>
                        </tr>
                    `;
                });
                quadruplesTableBody.innerHTML = html;
            }
        }
    }

    // E1. Code Optimization
    function renderOptimizations(data) {
        const optTac = data.optimized_tac || [];
        const origTac = data.tac_instructions || [];
        const transforms = data.optimizations || [];

        if (optimizedTacContainer) {
            if (optTac.length === 0) {
                optimizedTacContainer.innerHTML = '<div class="text-muted p-4 text-center">No optimized instructions.</div>';
            } else {
                let html = '<div class="p-3 font-monospace">';
                optTac.forEach((inst, idx) => {
                    html += `<div class="d-flex"><span class="text-muted me-3 user-select-none">${String(idx + 1).padStart(2, '0')}:</span><span class="text-emerald">${escapeHtml(inst)}</span></div>`;
                });
                html += '</div>';
                optimizedTacContainer.innerHTML = html;
            }
        }

        if (optimizationsList) {
            if (transforms.length === 0) {
                optimizationsList.innerHTML = '<div class="text-muted p-3 text-center">No constant folding or algebraic identities were applicable.</div>';
            } else {
                let html = '';
                transforms.forEach(tr => {
                    html += `
                        <div class="p-2 mb-2 rounded bg-surface border border-subtle">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="badge bg-emerald-500 text-white">${tr.type}</span>
                                <span class="small text-muted">${tr.rationale}</span>
                            </div>
                            <div class="font-monospace small">
                                <span class="text-danger text-decoration-line-through">${tr.before}</span>
                                <i class="bi bi-arrow-right mx-2 text-muted"></i>
                                <span class="text-success fw-bold">${tr.after}</span>
                            </div>
                        </div>
                    `;
                });
                optimizationsList.innerHTML = html;
            }
        }

        if (optimizationStats) {
            const origLen = origTac.length;
            const optLen = optTac.length;
            optimizationStats.innerHTML = `
                <div class="d-flex justify-content-between small text-secondary">
                    <span>Original Instructions: <strong>${origLen}</strong></span>
                    <span>Optimized Instructions: <strong>${optLen}</strong></span>
                    <span>Transformations: <strong>${transforms.length}</strong></span>
                </div>
            `;
        }
    }

    // F1. Error Diagnostics
    function renderErrorDiagnostics(data) {
        if (!errorDiagnosticsContainer) return;

        if (data.is_success) {
            errorDiagnosticsContainer.innerHTML = `
                <div class="alert alert-success d-flex align-items-center">
                    <i class="bi bi-shield-check fs-4 me-3"></i>
                    <div>
                        <h6 class="mb-1">No Errors Detected</h6>
                        <p class="mb-0 small text-secondary">The source code passed all lexical, syntactic, and semantic verification rules.</p>
                    </div>
                </div>
            `;
            return;
        }

        let html = `
            <div class="alert alert-danger mb-4">
                <div class="d-flex align-items-center mb-2">
                    <i class="bi bi-exclamation-triangle-fill fs-4 me-2"></i>
                    <h5 class="mb-0">Compilation Failed in ${data.error_stage ? data.error_stage.toUpperCase() : 'PIPELINE'} Stage</h5>
                </div>
                <p class="mb-0">${escapeHtml(data.error_message || 'An error occurred during compilation.')}</p>
            </div>
        `;

        // Render detailed errors by stage
        if (data.lexer_errors && data.lexer_errors.length > 0) {
            html += '<h6 class="text-danger fw-bold"><i class="bi bi-bug me-1"></i> Lexical Errors:</h6><ul class="list-group mb-3">';
            data.lexer_errors.forEach(e => {
                html += `<li class="list-group-item bg-surface text-light border-subtle d-flex justify-content-between align-items-center">
                    <span>${escapeHtml(e.message)}</span>
                    <span class="badge bg-danger">Line ${e.line}, Col ${e.column}</span>
                </li>`;
            });
            html += '</ul>';
        }

        if (data.syntax_errors && data.syntax_errors.length > 0) {
            html += '<h6 class="text-danger fw-bold"><i class="bi bi-code-slash me-1"></i> Syntax Errors:</h6><ul class="list-group mb-3">';
            data.syntax_errors.forEach(e => {
                html += `<li class="list-group-item bg-surface text-light border-subtle d-flex justify-content-between align-items-center">
                    <span>${escapeHtml(e.message)}</span>
                    <span class="badge bg-danger">Line ${e.line}, Col ${e.column}</span>
                </li>`;
            });
            html += '</ul>';
        }

        if (data.semantic_errors && data.semantic_errors.length > 0) {
            html += '<h6 class="text-danger fw-bold"><i class="bi bi-shield-x me-1"></i> Semantic Errors:</h6><ul class="list-group mb-3">';
            data.semantic_errors.forEach(e => {
                html += `<li class="list-group-item bg-surface text-light border-subtle d-flex justify-content-between align-items-center">
                    <span>${escapeHtml(e.message)}</span>
                    <span class="badge bg-danger">Line ${e.line}, Col ${e.column}</span>
                </li>`;
            });
            html += '</ul>';
        }

        errorDiagnosticsContainer.innerHTML = html;
    }

    // Helper: Escape HTML
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
