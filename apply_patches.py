import os
import shutil

# ─────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DE ARQUIVOS
# ─────────────────────────────────────────────────────────────────
MAIN_FILE = "main2.py"
JS_FILE = "static/js/app.js"

def backup_file(filepath):
    if os.path.exists(filepath):
        shutil.copy2(filepath, filepath + ".bak")
        print(f"✅ Backup criado: {filepath}.bak")

def apply_patches():
    print("🚀 Iniciando Protocolo de Patching R2 v9.2...")

    # --- PATCHES NO main2.py ---
    if os.path.exists(MAIN_FILE):
        backup_file(MAIN_FILE)
        with open(MAIN_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # Patch 1: BrokerOperator Init
        p1_antes = 'BrokerOperator = safe_import("broker_operator", "BrokerOperator")\n    broker_ops = BrokerOperator() if BrokerOperator else None'
        p1_depois = 'BrokerOperator = safe_import("broker_operator", "BrokerOperator")\n    broker_ops = BrokerOperator(alpha_engine=alpha_engine) if BrokerOperator else None'
        content = content.replace(p1_antes, p1_depois)

        # Patch 2: Analyze Endpoint (Thread-Safe)
        p2_antes = '''@app.post("/api/alpha/analyze")
def alpha_analyze():
    page = get_alpha_page()
    if not page:
        raise HTTPException(status_code=503, detail="Nenhuma sessão tática (Broker ou TikTok) aberta.")
    alpha_engine.attach(page)
    return alpha_engine.perceive_and_act()'''
        
        p2_depois = '''@app.post("/api/alpha/analyze")
def alpha_analyze():
    """Rota de análise. Usa a ponte thread-safe do BrokerOperator."""
    if broker_ops and broker_ops._is_running:
        return broker_ops.execute_safe("ANALYZE")
    page = get_alpha_page()
    if not page:
        raise HTTPException(status_code=503, detail="Nenhuma sessão tática (Broker ou TikTok) aberta.")
    alpha_engine.attach(page)
    return alpha_engine.perceive_and_act()'''
        content = content.replace(p2_antes, p2_depois)

        # Patch 3 e 4: Autopilot Reforçado + Novos Endpoints
        p3_antes = '''@app.post("/api/alpha/autopilot")
def alpha_autopilot():
    page = get_alpha_page()
    if not page:
        raise HTTPException(status_code=503, detail="Nenhuma sessão tática aberta.")
    alpha_engine.attach(page)
    return alpha_engine.run_until_success(max_cycles=9999, delay_between=0.5)'''

        p3_depois = '''@app.post("/api/alpha/autopilot")
def alpha_autopilot():
    """Inicia o autopilot de forma não-bloqueante."""
    if not broker_ops or not broker_ops._is_running:
        raise HTTPException(status_code=503, detail="Sessão Broker10 inativa. Clique em 'Abrir Broker10' primeiro.")
    return broker_ops.execute_safe("AUTOPILOT_START")

@app.post("/api/broker/stop_autopilot")
def stop_autopilot():
    """Para o autopilot de forma limpa."""
    if not broker_ops:
        raise HTTPException(status_code=503, detail="Módulo BrokerOperator offline.")
    return broker_ops.execute_safe("AUTOPILOT_STOP")

@app.get("/api/alpha/autopilot_status")
def autopilot_status():
    """Estado atual para polling do frontend."""
    if not broker_ops:
        return {"running": False, "cycles": 0, "last_result": None}
    return broker_ops.get_autopilot_status()

@app.post("/api/broker/navigate")
def broker_navigate(body: dict):
    """Navega a sessão do broker via ponte."""
    if not broker_ops or not broker_ops._is_running:
        raise HTTPException(status_code=503, detail="Sessão Broker10 inativa.")
    url = body.get("url", "https://broker10.com")
    return broker_ops.execute_safe("NAVIGATE", args={"url": url})'''
        
        content = content.replace(p3_antes, p3_depois)

        with open(MAIN_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Patches aplicados no main2.py")

    # --- PATCHES NO app.js ---
    if os.path.exists(JS_FILE):
        backup_file(JS_FILE)
        with open(JS_FILE, "r", encoding="utf-8") as f:
            js_lines = f.readlines()

        new_js = []
        skip = False
        helpers_added = False

        for line in js_lines:
            # 1. Substituir a função toggleAutopilot
            if "function toggleAutopilot()" in line:
                new_js.append('    function toggleAutopilot() {\n        var btn = _el("btn-autopilot");\n        if (!_autopilotOn) {\n            _autopilotOn = true;\n            if (btn) {\n                btn.innerHTML = \'<span class="alpha-btn-icon">&#9646;&#9646;</span> Parar Autopilot\';\n                btn.className = "alpha-btn alpha-btn-autopilot running";\n            }\n            _log("AUTOPILOT ATIVADO — modo Blitz (0.5s)...", "warn");\n            var xhrStart = new XMLHttpRequest();\n            xhrStart.open("POST", "/api/alpha/autopilot", true);\n            xhrStart.setRequestHeader("Content-Type", "application/json");\n            xhrStart.onreadystatechange = function() {\n                if (xhrStart.readyState === 4) {\n                    if (xhrStart.status === 200) {\n                        var data;\n                        try { data = JSON.parse(xhrStart.responseText); } catch(e) { data = {}; }\n                        _log("Autopilot confirmado: " + (data.msg || "ativo"), "ok");\n                        _startAutopilotPoll();\n                    } else {\n                        _log("Erro ao iniciar autopilot: " + xhrStart.status, "error");\n                        _autopilotOn = false;\n                        if (btn) {\n                            btn.innerHTML = \'<span class="alpha-btn-icon">&#9658;</span> Ativar Autopilot\';\n                            btn.className = "alpha-btn alpha-btn-autopilot";\n                        }\n                    }\n                }\n            };\n            xhrStart.send();\n        } else {\n            _autopilotOn = false;\n            _stopAutopilotPoll();\n            if (btn) {\n                btn.innerHTML = \'<span class="alpha-btn-icon">&#9658;</span> Ativar Autopilot\';\n                btn.className = "alpha-btn alpha-btn-autopilot";\n            }\n            _log("Enviando sinal de parada...", "warn");\n            var xhrStop = new XMLHttpRequest();\n            xhrStop.open("POST", "/api/broker/stop_autopilot", true);\n            xhrStop.setRequestHeader("Content-Type", "application/json");\n            xhrStop.onreadystatechange = function() {\n                if (xhrStop.readyState === 4 && xhrStop.status === 200) {\n                    var data;\n                    try { data = JSON.parse(xhrStop.responseText); } catch(e) { data = {}; }\n                    _log("Autopilot parado. Ciclos: " + (data.total_cycles || "--"), "warn");\n                }\n            };\n            xhrStop.send();\n        }\n    }\n')
                skip = True
                continue
            
            # Pula as linhas da função antiga até encontrar o fechamento
            if skip:
                if line.strip() == "}":
                    skip = False
                continue

            # 2. Inserir Helpers antes do return do alphaPanel
            if "return {" in line and "open:" in line and not helpers_added:
                new_js.append('\n    var _autopilotPollTimer = null;\n    function _startAutopilotPoll() { if (_autopilotPollTimer) return; _autopilotPollTimer = setInterval(_pollAutopilotStatus, 2000); }\n    function _stopAutopilotPoll() { if (_autopilotPollTimer) { clearInterval(_autopilotPollTimer); _autopilotPollTimer = null; } }\n    function _pollAutopilotStatus() {\n        var xhr = new XMLHttpRequest();\n        xhr.open("GET", "/api/alpha/autopilot_status", true);\n        xhr.onreadystatechange = function() {\n            if (xhr.readyState === 4 && xhr.status === 200) {\n                var data;\n                try { data = JSON.parse(xhr.responseText); } catch(e) { return; }\n                var cycleEl = _el("alpha-cycle-count");\n                if (cycleEl && data.cycles !== undefined) cycleEl.textContent = data.cycles;\n                if (!data.running && _autopilotOn) {\n                    _autopilotOn = false;\n                    _stopAutopilotPoll();\n                    var btn = _el("btn-autopilot");\n                    if (btn) {\n                        btn.innerHTML = \'<span class="alpha-btn-icon">&#9658;</span> Ativar Autopilot\';\n                        btn.className = "alpha-btn alpha-btn-autopilot";\n                    }\n                    _log("Autopilot parou automaticamente no servidor.", "warn");\n                }\n                if (data.last_result) {\n                    _renderState(data.last_result);\n                    var act = data.last_result.recommended_action;\n                    if (act && act !== "WAIT" && act !== "DEBOUNCED") {\n                        _log("Ciclo #" + data.cycles + " | " + (data.last_result.state || "--") + " → " + act, "state");\n                    }\n                }\n            }\n        };\n        xhr.send();\n    }\n\n')
                helpers_added = True
            
            new_js.append(line)

        with open(JS_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_js)
        print("✅ Patches aplicados no app.js")

    print("\n🏁 Processo concluído. Reinicie o R2 Tactical OS.")

if __name__ == "__main__":
    apply_patches()