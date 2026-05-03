import os

def adicionar_placar_visual():
    file_path = "alpha_module.py"
    if not os.path.exists(file_path): return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Adicionando contadores de Win/Loss na inicialização
    if "self.wins = 0" not in content:
        content = content.replace(
            "self.losses_seguidas = 0",
            "self.losses_seguidas = 0\\n        self.wins = 0\\n        self.losses = 0"
        )

    # Função para atualizar o placar no log
    log_logic = """
    def exibir_placar(self):
        print(f"\\n[PLACAR ATUAL]: ✅ {self.wins} WIN | ❌ {self.losses} LOSS")
        print(f"[GERENCIAMENTO]: Meta {self.meta_diaria} | Stop {self.stop_loss_diario}\\n")
"""
    if "def exibir_placar" not in content:
        content += log_logic

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Placar de Win/Loss registrado no motor Alpha!")

if __name__ == "__main__":
    adicionar_placar_visual()