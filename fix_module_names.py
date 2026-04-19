# filename: fix_module_names.py
import os

def fix_mismatches():
    print("🛠️ [HARMONIZADOR]: Corrigindo conflitos de nomes nas Features...")

    # 1. Correção do NetSpeed
    net_speed_path = os.path.join("features", "net_speed.py")
    if os.path.exists(net_speed_path):
        with open(net_speed_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "class SpeedTestModule:" in content:
            content = content.replace("class SpeedTestModule:", "class NetSpeedModule:")
            with open(net_speed_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ NetSpeed: SpeedTestModule -> NetSpeedModule")

    # 2. Correção do NOAA (Garante que a classe exista para o import)
    noaa_path = os.path.join("features", "noaa_service.py")
    if os.path.exists(noaa_path):
        with open(noaa_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Se o arquivo for apenas funções, vamos envolver em uma classe para o core
        if "class NOAAService" not in content:
            # Adiciona a casca da classe no final do arquivo para compatibilidade
            wrapper = "\\n\\nclass NOAAService:\\n    def __init__(self): pass\\n    def get_full_intel(self): return get_full_intel()\\n"
            with open(noaa_path, "a", encoding="utf-8") as f:
                f.write(wrapper)
            print("✅ NOAA: Classe de compatibilidade injetada.")

    # 3. Correção do NewsBriefing (Garante padrão de nome)
    news_path = os.path.join("features", "news_briefing.py")
    if os.path.exists(news_path):
        with open(news_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "class NewsBriefing" not in content and "class NewsBrief" in content:
            content = content.replace("class NewsBrief:", "class NewsBriefing:")
            with open(news_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ NewsBriefing: Nome harmonizado.")

    print("\\n🚀 [PRONTO]: Nomes sincronizados com o Cérebro Principal.")

if __name__ == "__main__":
    fix_mismatches()