import subprocess
import os
import threading

class QuantumCoreManager:
    def __init__(self):
        # Caminho absoluto ou relativo para o executável do trade
        self.bat_path = r"C:\R1\QuantumCore_Pro\trade.bat"

    def execute_trade_protocol(self, callback_msg):
        """Executa o arquivo .bat em uma thread separada para não travar o R2"""
        def run():
            if os.path.exists(self.bat_path):
                try:
                    # Define o diretório de trabalho para a pasta do arquivo bat
                    work_dir = os.path.dirname(self.bat_path)
                    
                    # Inicia o processo em uma nova janela de terminal (estilo Sci-Fi)
                    subprocess.Popen(
                        [self.bat_path],
                        cwd=work_dir,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                    callback_msg("✅ [QUANTUM CORE]: Protocolo de Trade iniciado com sucesso.")
                except Exception as e:
                    callback_msg(f"❌ [ERRO CRÍTICO]: Falha ao disparar QuantumCore: {e}")
            else:
                callback_msg(f"⚠️ [ALERTA]: Arquivo trade.bat não encontrado em {self.bat_path}")

        threading.Thread(target=run, daemon=True).start()