# filename: patch_upgrades.py
import re
import os

FILE_PATH = "main2.py"

def apply_upgrades():
    print("🚀 Iniciando upgrades no Cérebro do R2...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return
        
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remoção do Limite de Tempo (Timeout)
    content = content.replace(
        "stdout, stderr = proc.communicate(timeout=60)", 
        "stdout, stderr = proc.communicate() # SEM TIMEOUT"
    )
    # Remove o bloco de exceção de timeout usando Regex para evitar erros de quebra de linha
    content = re.sub(
        r' +except subprocess\.TimeoutExpired:.*?demorou mais de 60 segundos\."\}', 
        '', content, flags=re.DOTALL
    )

    # 2. Expansão Visual do Terminal e Input (Faz o prompt aparecer todo)
    content = content.replace("max-height: 260px;", "max-height: none; /* Exibe todo o terminal */")
    content = content.replace("max-height: 130px;", "max-height: 50vh; /* Permite input maior */")

    # 3. Novo Comando: Leitor de Arquivos Direto (/ler)
    old_llm_start = """            # ── IA (LLM) ───────────────────────────────────
            if ai_brain:
                memoria_ram.append(f"Teddy: {comando}")
                ctx = await asyncio.to_thread(rag_ops.search, comando)"""

    new_llm_start = """            # ── IA (LLM) ───────────────────────────────────
            if ai_brain:
                # Interceptador de Arquivos (Comandos: /ler arquivo.ext)
                arquivos_injetados = ""
                matches = re.findall(r'/ler\\s+([\\w.\\-]+)', comando, re.IGNORECASE)
                cmd_limpo = comando
                for arq in matches:
                    caminho_arq = WORKSPACE / arq
                    if caminho_arq.exists():
                        conteudo = caminho_arq.read_text(encoding="utf-8", errors="replace")
                        arquivos_injetados += f"\\n\\n[CONTEÚDO DO ARQUIVO: {arq}]\\n```python\\n{conteudo}\\n```\\n"
                    else:
                        arquivos_injetados += f"\\n\\n[AVISO: Arquivo '{arq}' não encontrado no workspace.]\\n"
                    
                    # Remove o comando de leitura da string original
                    cmd_limpo = re.sub(fr'/ler\\s+{re.escape(arq)}', '', cmd_limpo, flags=re.IGNORECASE).strip()

                if not cmd_limpo and arquivos_injetados:
                    cmd_limpo = "Analise o(s) arquivo(s) acima e aguarde instruções."

                comando_final = f"{cmd_limpo}{arquivos_injetados}"

                memoria_ram.append(f"Teddy: {comando}") # Salva apenas o texto curto na memória
                ctx = await asyncio.to_thread(rag_ops.search, cmd_limpo)"""
    
    content = content.replace(old_llm_start, new_llm_start)

    # Atualiza a injeção do comando final no Cérebro da IA
    old_prompt_user = '                prompt += f"<|im_start|>user\\n{comando}<|im_end|>\\n<|im_start|>assistant\\n"'
    new_prompt_user = '                prompt += f"<|im_start|>user\\n{comando_final}<|im_end|>\\n<|im_start|>assistant\\n"'
    content = content.replace(old_prompt_user, new_prompt_user)

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("✅ Upgrades aplicados com sucesso! Reinicie o Uvicorn e dê Ctrl+F5 no navegador.")

if __name__ == "__main__":
    apply_upgrades()