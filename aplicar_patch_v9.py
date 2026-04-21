#!/usr/bin/env python3
# filename: aplicar_patch_v9.py
"""
Patch de Correção V9.0 para R2 Tactical OS
Aplica as correções pontuais nos 10 arquivos usando substituição textual estrita.
Uso: python aplicar_patch_v9.py (executar na raiz do projeto)
"""

import os
import shutil
from datetime import datetime

# ----------------------------------------------------------------------
# 1. main2.py
# ----------------------------------------------------------------------
def patch_main2(conteudo: str) -> str:
    # 1.1 Remover import threading duplicado (linha 630)
    # Remove a segunda ocorrência exata da linha 'import threading'
    # Primeiro, encontrar a primeira ocorrência e depois remover a próxima igual
    linhas = conteudo.splitlines()
    novas = []
    encontrou_primeiro = False
    for linha in linhas:
        if linha.strip() == "import threading":
            if not encontrou_primeiro:
                encontrou_primeiro = True
                novas.append(linha)
            # senão, pula (remove duplicata)
        else:
            novas.append(linha)
    conteudo = "\n".join(novas)

    # 1.2 Instanciar AirTrafficControl e AstroDefenseSystem no lifespan e conectar rotas
    # Bloco original: após a criação do noaa_ops, inserir as novas instâncias
    bloco_original_inst = (
        "    noaa_ops = NOAAService() if NOAAService else None\n"
        "\n"
        "    # BUG FIX #2 (integração): Whisper é carregado PRIMEIRO e injetado no VideoSurgeon."
    )
    bloco_novo_inst = (
        "    noaa_ops = NOAAService() if NOAAService else None\n"
        "\n"
        "    # V9.0: Instanciar módulos táticos\n"
        "    AirTrafficControl = safe_import(\"air_traffic\", \"AirTrafficControl\")\n"
        "    AstroDefenseSystem = safe_import(\"astro_defense\", \"AstroDefenseSystem\")\n"
        "    air_ops = AirTrafficControl() if AirTrafficControl else None\n"
        "    astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None\n"
        "\n"
        "    # BUG FIX #2 (integração): Whisper é carregado PRIMEIRO e injetado no VideoSurgeon."
    )
    conteudo = conteudo.replace(bloco_original_inst, bloco_novo_inst)

    # Substituir o bloco do comando /cmd radar
    bloco_radar_original = (
        '                elif sub == "radar":\n'
        '                    await websocket.send_json({"type": "system", "text": "📡 Módulo de Radar não está conectado nesta sessão. Verifique se o serviço está ativo."})'
    )
    bloco_radar_novo = (
        '                elif sub == "radar":\n'
        '                    if air_ops:\n'
        '                        filename, qtd, msg = await asyncio.to_thread(air_ops.radar_scan, "Ivinhema")\n'
        '                        await websocket.send_json({"type": "system", "text": f"{msg}<br><img src=\'/{filename}\' style=\'max-width:100%; border-radius:8px;\'>"})\n'
        '                    else:\n'
        '                        await websocket.send_json({"type": "system", "text": "📡 Módulo de Radar não está disponível."})'
    )
    conteudo = conteudo.replace(bloco_radar_original, bloco_radar_novo)

    # Substituir o bloco do comando /cmd astro
    bloco_astro_original = (
        '                elif sub == "astro":\n'
        '                    await websocket.send_json({"type": "system", "text": "☄️ Módulo de Defesa Planetária não está conectado nesta sessão."})'
    )
    bloco_astro_novo = (
        '                elif sub == "astro":\n'
        '                    if astro_ops:\n'
        '                        texto, astro_id, astro_nome = await asyncio.to_thread(astro_ops.get_asteroid_report)\n'
        '                        await websocket.send_json({"type": "system", "text": texto})\n'
        '                    else:\n'
        '                        await websocket.send_json({"type": "system", "text": "☄️ Módulo de Defesa Planetária não está disponível."})'
    )
    conteudo = conteudo.replace(bloco_astro_original, bloco_astro_novo)

    # 1.3 Rotacionar historico_chat.json (manter últimas 500 entradas)
    # Modificar a função salvar_no_historico_json
    bloco_historico_original = (
        '    with historico_lock:\n'
        '        historico = []\n'
        '        if os.path.exists(LOG_HISTORICO):\n'
        '            try:\n'
        '                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:\n'
        '                    historico = json.load(f)\n'
        '            except Exception as e:\n'
        '                print(f"[AVISO] Erro ao ler histórico: {e}")\n'
        '        historico.append(interacao)\n'
        '        try:\n'
        '            with open(LOG_HISTORICO, "w", encoding="utf-8") as f:\n'
        '                json.dump(historico, f, ensure_ascii=False, indent=4)\n'
        '        except Exception as e:\n'
        '            print(f"[AVISO] Erro ao gravar histórico: {e}")'
    )
    bloco_historico_novo = (
        '    with historico_lock:\n'
        '        historico = []\n'
        '        if os.path.exists(LOG_HISTORICO):\n'
        '            try:\n'
        '                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:\n'
        '                    historico = json.load(f)\n'
        '            except Exception as e:\n'
        '                print(f"[AVISO] Erro ao ler histórico: {e}")\n'
        '        historico.append(interacao)\n'
        '        # V9.0: Manter apenas últimas 500 entradas\n'
        '        if len(historico) > 500:\n'
        '            historico = historico[-500:]\n'
        '        try:\n'
        '            with open(LOG_HISTORICO, "w", encoding="utf-8") as f:\n'
        '                json.dump(historico, f, ensure_ascii=False, indent=4)\n'
        '        except Exception as e:\n'
        '            print(f"[AVISO] Erro ao gravar histórico: {e}")'
    )
    conteudo = conteudo.replace(bloco_historico_original, bloco_historico_novo)

    return conteudo

# ----------------------------------------------------------------------
# 2. static/js/app.js
# ----------------------------------------------------------------------
def patch_app_js(conteudo: str) -> str:
    # 2.1 Em criarBarrasSom, armazenar setInterval em window._soundwaveIntervalId
    bloco_interval_original = (
        '    setInterval(function() {\n'
        '        if (!battleModeAtivo) return;\n'
        '        for (var j = 0; j < soundwaveBars.length; j++) {\n'
        '            var bar = soundwaveBars[j];\n'
        '            if (!bar.classList || bar.classList.contains(\'speaking\')) continue;\n'
        '            var novaAltura = 12 + Math.sin(Date.now() * 0.008 + j) * 30 + Math.random() * 10;\n'
        '            bar.style.height = Math.max(8, Math.min(90, novaAltura)) + \'px\';\n'
        '        }\n'
        '    }, 80);'
    )
    bloco_interval_novo = (
        '    window._soundwaveIntervalId = setInterval(function() {\n'
        '        if (!battleModeAtivo) return;\n'
        '        for (var j = 0; j < soundwaveBars.length; j++) {\n'
        '            var bar = soundwaveBars[j];\n'
        '            if (!bar.classList || bar.classList.contains(\'speaking\')) continue;\n'
        '            var novaAltura = 12 + Math.sin(Date.now() * 0.008 + j) * 30 + Math.random() * 10;\n'
        '            bar.style.height = Math.max(8, Math.min(90, novaAltura)) + \'px\';\n'
        '        }\n'
        '    }, 80);'
    )
    conteudo = conteudo.replace(bloco_interval_original, bloco_interval_novo)

    # 2.2 No toggleModoBatalha, quando desativar, chamar clearInterval
    bloco_desativar_original = (
        '    if (battleModeAtivo) {\n'
        '        battleModeAtivo = false;\n'
        '        telaBatalha.style.display = \'none\';\n'
        '        pararEscuta();\n'
        '        if (audioAtual) {\n'
        '            audioAtual.pause();\n'
        '            audioAtual = null;\n'
        '        }\n'
        '        showToast(\'Modo Safe ativado. Interface de chat restaurada.\');\n'
        '    } else {'
    )
    bloco_desativar_novo = (
        '    if (battleModeAtivo) {\n'
        '        battleModeAtivo = false;\n'
        '        telaBatalha.style.display = \'none\';\n'
        '        if (window._soundwaveIntervalId) {\n'
        '            clearInterval(window._soundwaveIntervalId);\n'
        '            window._soundwaveIntervalId = null;\n'
        '        }\n'
        '        pararEscuta();\n'
        '        if (audioAtual) {\n'
        '            audioAtual.pause();\n'
        '            audioAtual = null;\n'
        '        }\n'
        '        showToast(\'Modo Safe ativado. Interface de chat restaurada.\');\n'
        '    } else {'
    )
    conteudo = conteudo.replace(bloco_desativar_original, bloco_desativar_novo)

    # 2.3 Remover chamada redundante de initBattleMode() na função init (IIFE final)
    # A linha exata dentro da IIFE é 'initBattleMode();' no final
    # Vamos remover a linha que contém 'initBattleMode();' no final do arquivo
    # Localizar e substituir por vazio (cuidado para não remover outras ocorrências)
    # O arquivo termina com '}());' e antes tem 'initBattleMode();'
    bloco_init_original = (
        '    initBattleMode();\n'
        '}());'
    )
    bloco_init_novo = (
        '}());'
    )
    conteudo = conteudo.replace(bloco_init_original, bloco_init_novo)

    return conteudo

# ----------------------------------------------------------------------
# 3. video_ops.py
# ----------------------------------------------------------------------
def patch_video_ops(conteudo: str) -> str:
    # 3.1 Garantir exclusão do temp_yt_*.mp4 no finally
    # Localizar o bloco finally existente e adicionar a remoção
    bloco_finally_original = (
        '        finally:\n'
        '            if os.path.exists(temp_audio):\n'
        '                try:\n'
        '                    os.unlink(temp_audio)\n'
        '                except Exception:\n'
        '                    pass'
    )
    bloco_finally_novo = (
        '        finally:\n'
        '            if os.path.exists(temp_audio):\n'
        '                try:\n'
        '                    os.unlink(temp_audio)\n'
        '                except Exception:\n'
        '                    pass\n'
        '            # V9.0: Remover arquivo temporário do YouTube\n'
        '            if video_path and video_path.startswith("static/media/temp_yt_"):\n'
        '                try:\n'
        '                    os.unlink(video_path)\n'
        '                except Exception:\n'
        '                    pass'
    )
    conteudo = conteudo.replace(bloco_finally_original, bloco_finally_novo)

    # 3.2 Adicionar socket_timeout: 30 no dicionário ydl_opts
    bloco_ydl_original = (
        "            ydl_opts = {\n"
        "                'format': 'best',\n"
        "                'outtmpl': 'static/media/temp_yt_%(id)s.%(ext)s',\n"
        "                'quiet': True,\n"
        "                'no_warnings': True\n"
        "            }"
    )
    bloco_ydl_novo = (
        "            ydl_opts = {\n"
        "                'format': 'best',\n"
        "                'outtmpl': 'static/media/temp_yt_%(id)s.%(ext)s',\n"
        "                'quiet': True,\n"
        "                'no_warnings': True,\n"
        "                'socket_timeout': 30\n"
        "            }"
    )
    conteudo = conteudo.replace(bloco_ydl_original, bloco_ydl_novo)

    # 3.3 Validar existência dos campos tema, start, end e truncar tema para 40 chars
    # Inserir validação após o carregamento do JSON
    bloco_validacao_original = (
        "            cortes = json.loads(match.group(0))\n"
        "            \n"
        "            # 7. Ataque FFmpeg"
    )
    bloco_validacao_novo = (
        "            cortes = json.loads(match.group(0))\n"
        "            # V9.0: Validar e truncar campos\n"
        "            cortes_validos = []\n"
        "            for c in cortes:\n"
        "                if isinstance(c, dict) and \"tema\" in c and \"start\" in c and \"end\" in c:\n"
        "                    tema = c[\"tema\"]\n"
        "                    if len(tema) > 40:\n"
        "                        tema = tema[:40]\n"
        "                    c[\"tema\"] = tema\n"
        "                    cortes_validos.append(c)\n"
        "            cortes = cortes_validos\n"
        "            \n"
        "            # 7. Ataque FFmpeg"
    )
    conteudo = conteudo.replace(bloco_validacao_original, bloco_validacao_novo)

    return conteudo

# ----------------------------------------------------------------------
# 4. features/air_traffic.py
# ----------------------------------------------------------------------
def patch_air_traffic(conteudo: str) -> str:
    # 4.1 Remover plt.style.use('dark_background') global; usar Figure/Axes locais
    # Substituir a linha global por comentário e adicionar estilo local
    conteudo = conteudo.replace(
        "        plt.style.use('dark_background')",
        "        # plt.style.use('dark_background') # V9.0: removido global"
    )
    # Dentro de _plotar_radar, após fig, ax = plt.subplots, adicionar fundo preto
    bloco_axes_original = (
        "        fig, ax = plt.subplots(figsize=(8, 8))\n"
        "        \n"
        "        # Legenda do ponto central dinâmico"
    )
    bloco_axes_novo = (
        "        fig, ax = plt.subplots(figsize=(8, 8))\n"
        "        ax.set_facecolor('black')\n"
        "        fig.patch.set_facecolor('black')\n"
        "        \n"
        "        # Legenda do ponto central dinâmico"
    )
    conteudo = conteudo.replace(bloco_axes_original, bloco_axes_novo)

    # 4.2 Usar os.path.abspath() para definir caminho de radar_scan.png
    conteudo = conteudo.replace(
        '            filename = "radar_scan.png"',
        '            filename = os.path.abspath("radar_scan.png")'
    )
    return conteudo

# ----------------------------------------------------------------------
# 5. features/astro_defense.py
# ----------------------------------------------------------------------
def patch_astro_defense(conteudo: str) -> str:
    # 5.1 Trocar DEMO_KEY por os.environ.get("NASA_API_KEY", "DEMO_KEY")
    conteudo = conteudo.replace(
        '        self.api_key = "DEMO_KEY"',
        '        self.api_key = os.environ.get("NASA_API_KEY", "DEMO_KEY")'
    )
    # 5.2 Substituir except: genérico por except Exception as e:
    # Encontrar o bloco except: (linha vazia) e substituir
    conteudo = conteudo.replace(
        "        except:",
        "        except Exception as e:"
    )
    return conteudo

# ----------------------------------------------------------------------
# 6. features/system_monitor.py
# ----------------------------------------------------------------------
def patch_system_monitor(conteudo: str) -> str:
    # 6.1 Reescrever _get_time como síncrona e remover asyncio.run
    # Substituir a definição da função
    bloco_get_time_original = (
        "    async def _get_time(self):\n"
        "        from datetime import datetime\n"
        "        return datetime.now().strftime(\"%H:%M:%S\")"
    )
    bloco_get_time_novo = (
        "    def _get_time(self):\n"
        "        from datetime import datetime\n"
        "        return datetime.now().strftime(\"%H:%M:%S\")"
    )
    conteudo = conteudo.replace(bloco_get_time_original, bloco_get_time_novo)

    # Substituir a chamada asyncio.run(self._get_time())
    conteudo = conteudo.replace(
        "        report.append(f\"\\n⏱️ TIMESTAMP: {asyncio.run(self._get_time())}\")",
        "        report.append(f\"\\n⏱️ TIMESTAMP: {self._get_time()}\")"
    )
    return conteudo

# ----------------------------------------------------------------------
# 7. features/noaa_service.py
# ----------------------------------------------------------------------
def patch_noaa_service(conteudo: str) -> str:
    # 7.1 Aplicar .decode("utf-8", errors="replace") ao ler stderr
    # Localizar a linha onde imprime result.stderr e substituir
    bloco_stderr_original = (
        '            print(f"⚠️  [FFmpeg] Código de saída {result.returncode}: {result.stderr[-200:]}")'
    )
    bloco_stderr_novo = (
        '            stderr_str = result.stderr.decode("utf-8", errors="replace") if isinstance(result.stderr, bytes) else result.stderr\n'
        '            print(f"⚠️  [FFmpeg] Código de saída {result.returncode}: {stderr_str[-200:]}")'
    )
    conteudo = conteudo.replace(bloco_stderr_original, bloco_stderr_novo)
    return conteudo

# ----------------------------------------------------------------------
# 8. features/pizzint_service.py
# ----------------------------------------------------------------------
def patch_pizzint_service(conteudo: str) -> str:
    # 8.1 Adicionar from __future__ import annotations no topo
    if not conteudo.startswith("from __future__ import annotations"):
        conteudo = "from __future__ import annotations\n" + conteudo
    # 8.2 Adequar tipagem: substituir | None por Optional (para Python 3.8)
    # Primeiro, garantir import de Optional
    if "from typing import" not in conteudo:
        # Inserir após a linha de future
        linhas = conteudo.splitlines()
        for i, linha in enumerate(linhas):
            if linha.startswith("from __future__"):
                linhas.insert(i+1, "from typing import Optional, List, Dict")
                break
        conteudo = "\n".join(linhas)
    else:
        # Se já existe import typing, adicionar Optional, List, Dict se não estiverem
        if "Optional" not in conteudo:
            conteudo = conteudo.replace(
                "from typing import",
                "from typing import Optional,"
            )
        if "List" not in conteudo:
            conteudo = conteudo.replace(
                "from typing import",
                "from typing import List,"
            )
        if "Dict" not in conteudo:
            conteudo = conteudo.replace(
                "from typing import",
                "from typing import Dict,"
            )
    # Substituir 'Response | None' por 'Optional[Response]'
    conteudo = conteudo.replace(
        "requests.Response | None",
        "Optional[requests.Response]"
    )
    # Substituir 'list[dict]' por 'List[Dict]' (caso exista)
    conteudo = conteudo.replace("list[dict]", "List[Dict]")
    conteudo = conteudo.replace("list[Dict]", "List[Dict]")
    return conteudo

# ----------------------------------------------------------------------
# 9. features/volcano_monitor.py
# ----------------------------------------------------------------------
def patch_volcano_monitor(conteudo: str) -> str:
    # 9.1 Substituir item.find("title").text por item.findtext("title", default="")
    conteudo = conteudo.replace(
        '                title = item.find("title").text',
        '                title = item.findtext("title", default="")'
    )
    conteudo = conteudo.replace(
        '                description = item.find("description").text',
        '                description = item.findtext("description", default="")'
    )
    return conteudo

# ----------------------------------------------------------------------
# 10. features/radio_scanner.py
# ----------------------------------------------------------------------
def patch_radio_scanner(conteudo: str) -> str:
    # 10.1 Remover import random não utilizado
    # Remover a linha exata 'import random'
    linhas = conteudo.splitlines()
    novas = [linha for linha in linhas if not linha.strip().startswith("import random")]
    conteudo = "\n".join(novas)
    return conteudo

# ----------------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ----------------------------------------------------------------------
def aplicar_patches():
    # Mapeamento dos caminhos relativos (a partir da raiz do projeto)
    arquivos = {
        "main2.py": patch_main2,
        "video_ops.py": patch_video_ops,
        "static/js/app.js": patch_app_js,
        "features/air_traffic.py": patch_air_traffic,
        "features/astro_defense.py": patch_astro_defense,
        "features/system_monitor.py": patch_system_monitor,
        "features/noaa_service.py": patch_noaa_service,
        "features/pizzint_service.py": patch_pizzint_service,
        "features/volcano_monitor.py": patch_volcano_monitor,
        "features/radio_scanner.py": patch_radio_scanner,
    }

    # Criar backup
    backup_dir = f"backup_patch_v9_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)

    for caminho, patch_func in arquivos.items():
        if not os.path.exists(caminho):
            print(f"❌ Arquivo não encontrado: {caminho}")
            continue
        try:
            # Backup
            shutil.copy2(caminho, os.path.join(backup_dir, os.path.basename(caminho)))
            # Ler conteúdo
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
            # Aplicar patch
            novo_conteudo = patch_func(conteudo)
            # Escrever
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(novo_conteudo)
            print(f"✅ Patch aplicado com sucesso: {caminho}")
        except Exception as e:
            print(f"❌ Falha ao aplicar patch em {caminho}: {e}")

    print(f"\nBackup dos arquivos originais salvos em: {backup_dir}")

if __name__ == "__main__":
    aplicar_patches()