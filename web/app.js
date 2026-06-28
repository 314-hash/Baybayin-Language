// BBL Playground Frontend Application Logic

document.addEventListener('DOMContentLoaded', () => {
    const codeEditor = document.getElementById('code-editor');
    const btnCompile = document.getElementById('btn-compile');
    const consoleLogs = document.getElementById('console-logs');

    // Outputs
    const outPython = document.getElementById('output-python');
    const outJavascript = document.getElementById('output-javascript');
    const outSolidity = document.getElementById('output-solidity');
    const outAst = document.getElementById('output-ast');

    // Tabs
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // AI Chat elements
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const btnChatSend = document.getElementById('btn-chat-send');
    const btnQuickExplain = document.getElementById('btn-quick-explain');
    const btnQuickAudit = document.getElementById('btn-quick-audit');

    // --- Tab Switch Helper ---
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            
            // Toggle buttons
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle contents
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `tab-${target}`) {
                    content.classList.add('active');
                }
            });
        });
    });

    // --- Log Helper ---
    function log(message, type = 'info') {
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        line.innerText = `[${new Date().toLocaleTimeString()}] ${message}`;
        consoleLogs.appendChild(line);
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    }

    // --- Compilation Endpoint Caller ---
    async function performCompilation() {
        const code = codeEditor.value;
        if (!code.trim()) {
            log("Walang code na babasahin. Isulat muna ang BBL code.", "error");
            return;
        }

        log("Sinisimulan ang pag-transpile...", "info");
        btnCompile.disabled = true;
        btnCompile.innerHTML = '<span class="btn-icon">⌛</span> Binabasa...';

        const startTime = performance.now();

        try {
            const res = await fetch('/api/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });

            const data = await res.json();
            const elapsed = (performance.now() - startTime).toFixed(1);

            if (res.ok && data.success) {
                outPython.innerText = data.python;
                outJavascript.innerText = data.javascript;
                outSolidity.innerText = data.solidity;
                outAst.innerText = JSON.stringify(data.ast, null, 2);

                log(`Matagumpay na natapos ang pag-transpile sa loob ng ${elapsed}ms!`, "success");
            } else {
                const errMsg = data.error || "Hindi alam na error";
                log(`Failed: ${errMsg}`, "error");
                
                // Clear outputs on error
                outPython.innerText = `Error: ${errMsg}`;
                outJavascript.innerText = `Error: ${errMsg}`;
                outSolidity.innerText = `Error: ${errMsg}`;
                outAst.innerText = `Error: ${errMsg}`;
            }
        } catch (err) {
            log(`Network Error: ${err.message}`, "error");
        } finally {
            btnCompile.disabled = false;
            btnCompile.innerHTML = '<span class="btn-icon">⚡</span> Transpile Code';
        }
    }

    btnCompile.addEventListener('click', performCompilation);

    // --- AI Agent Dashboard Selector & Animations ---
    let selectedAgent = 'orchestrator';
    const agentTabs = document.querySelectorAll('.agent-tab');
    const nodeSubagent = document.getElementById('node-subagent');
    
    agentTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            agentTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            selectedAgent = tab.getAttribute('data-agent');
            
            if (selectedAgent === 'orchestrator') {
                nodeSubagent.innerText = 'Sub-Agent';
                nodeSubagent.className = 'flow-node';
            } else {
                nodeSubagent.innerText = selectedAgent.toUpperCase();
                let classColor = 'active';
                if (selectedAgent === 'writer') classColor = 'active-writer';
                else if (selectedAgent === 'auditor') classColor = 'active-auditor';
                else if (selectedAgent === 'explainer') classColor = 'active-explainer';
                else if (selectedAgent === 'guro') classColor = 'active-guro';
                nodeSubagent.className = `flow-node ${classColor}`;
            }
        });
    });

    function resetFlowchart() {
        document.getElementById('node-orchestrator').className = 'flow-node';
        document.getElementById('node-subagent').className = 'flow-node';
        document.getElementById('node-browser').className = 'flow-node';
        document.querySelectorAll('.flow-arrow').forEach(arr => arr.classList.remove('active'));
    }

    function animateFlowchart(routeTo, needsBrowser) {
        resetFlowchart();
        
        // 1. Activate orchestrator
        setTimeout(() => {
            document.getElementById('node-orchestrator').classList.add('active');
            document.querySelectorAll('.flow-arrow')[0].classList.add('active');
        }, 150);

        // 2. Activate target subagent node
        setTimeout(() => {
            nodeSubagent.innerText = routeTo.toUpperCase();
            let classColor = 'active';
            if (routeTo === 'writer') classColor = 'active-writer';
            else if (routeTo === 'auditor') classColor = 'active-auditor';
            else if (routeTo === 'explainer') classColor = 'active-explainer';
            else if (routeTo === 'guro') classColor = 'active-guro';
            
            nodeSubagent.className = `flow-node ${classColor}`;
            document.querySelectorAll('.flow-arrow')[1].classList.add('active');
        }, 600);

        // 3. Activate browser tool if used
        if (needsBrowser) {
            setTimeout(() => {
                document.getElementById('node-browser').classList.add('active');
                document.querySelectorAll('.flow-arrow')[2].classList.add('active');
            }, 1100);
        }
    }

    // --- AI Chat Helper ---
    function appendChatMessage(sender, text, type = 'user') {
        const msg = document.createElement('div');
        msg.className = `msg ${type}`;
        msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msg;
    }

    async function sendChatMessage(overrideQuery = null) {
        const query = overrideQuery || chatInput.value;
        const code = codeEditor.value;

        if (!query.trim()) return;

        if (!overrideQuery) {
            chatInput.value = '';
        }

        const agentTitle = selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1);
        appendChatMessage('Ikaw (Developer)', query, 'user');
        
        const thinkingBubble = appendChatMessage(`AI ${agentTitle}`, 'Nag-iisip at nag-oorkestra ng mga sub-agent...', 'assistant');

        try {
            const res = await fetch('/api/ai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, code, agent: selectedAgent })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                // Animate flowchart based on actual backend response routing
                const targetRoute = data.route || selectedAgent;
                const browserUsed = !!data.browser_used;
                
                animateFlowchart(targetRoute, browserUsed);
                
                thinkingBubble.innerHTML = `<strong>AI ${agentTitle}:</strong> ${data.response}`;
            } else {
                const errMsg = data.error || "Naka-encounter ng error ang AI module.";
                thinkingBubble.innerHTML = `<strong>AI ${agentTitle}:</strong> <span style="color:var(--accent-red)">Error: ${errMsg}</span>`;
            }
        } catch (err) {
            thinkingBubble.innerHTML = `<strong>AI ${agentTitle}:</strong> <span style="color:var(--accent-red)">Network Error: ${err.message}</span>`;
        }
    }

    btnChatSend.addEventListener('click', () => sendChatMessage());
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });

    // --- Quick Prompts ---
    btnQuickExplain.addEventListener('click', () => {
        sendChatMessage("Ipaliwanag ang kasalukuyang code sa editor line-by-line.");
    });

    btnQuickAudit.addEventListener('click', () => {
        sendChatMessage("Mag-audit ng kasalukuyang code sa editor para sa types at safety.");
    });
});
