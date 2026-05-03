import os

def aplicar_filtros_avancados():
    file_path = "alpha_module.py"
    if not os.path.exists(file_path): return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Proteção contra Cliques Múltiplos (Anti-Spam de ordens)
    # 2. Filtro de Vela de Exaustão (Vídeo 2)
    
    new_filters = """
    def filtro_avancado_v5(self, current_candle, history):
        # Filtro de Exaustão: Evita entrar em velas gigantes
        avg_body = sum(abs(c['close'] - c['open']) for c in history[-10:]) / 10
        current_body = abs(current_candle['close'] - current_candle['open'])
        
        if current_body > (avg_body * 2.5):
            return False, "EXAUSTAO_DETECTADA"

        # Trava de Segurança: Não permite mais de 1 ordem no mesmo ciclo de tempo
        if hasattr(self, 'last_candle_time') and self.last_candle_time == current_candle['time']:
            return False, "ORDEM_JA_EXECUTADA_NESTA_VELA"
            
        self.last_candle_time = current_candle['time']
        return True, "FILTROS_OK"
"""
    # Inserindo os novos filtros na classe AlphaEngine
    if "def filtro_avancado_v5" not in content:
        content = content.replace("class AlphaEngine:", "class AlphaEngine:\\n" + new_filters)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("🚀 Estratégias dos vídeos integradas: Anti-Exaustão e Trava de Ordem Única ativas.")

if __name__ == "__main__":
    aplicar_filtros_avancados()