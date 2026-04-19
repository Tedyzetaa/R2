# filename: fix_r2_logic.py
import os

FILE_PATH = "main2.py"

def fix_javascript_syntax():
    print("🧠 [CIRURGIA]: Corrigindo erros de sintaxe no JavaScript...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Corrige a quebra de linha fatal nos comandos .replace()
    # Substituímos por um método que não usa regex com barra invertida perigosa
    content = content.replace(".replace(/\n/g, '<br>')", ".split('\\n').join('<br>')")
    content = content.replace(".replace(/\n/g, '<br>')", ".split('\\n').join('<br>')") # Duplo check
    
    # Caso a quebra de linha tenha sido literal no arquivo (como no seu log)
    broken_replace = ".replace(/\n/g"
    if broken_replace not in content:
        # Tenta localizar a versão onde a barra n virou uma quebra de linha real
        content = content.replace(".replace(/\n", ".split('\\n")

    # 2. Corrige o erro 'Share' removendo escapes desnecessários nas fontes
    content = content.replace("font-family:\\'Share Tech Mono\\'", "font-family:Share Tech Mono")
    content = content.replace("font-family:'Share Tech Mono'", "font-family:Share Tech Mono")

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ [SUCESSO]: Sintaxe harmonizada. O JavaScript agora deve carregar totalmente.")

if __name__ == "__main__":
    fix_javascript_syntax()