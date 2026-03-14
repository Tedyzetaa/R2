import json
import os

class ImageGenerator:
    def __init__(self, db_path="models/personagens.json"):
        self.db_path = db_path
        self._check_db()

    def _check_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({}, f)

    def salvar_personagem(self, nome, descricao):
        with open(self.db_path, "r") as f:
            data = json.load(f)
        
        # DNA Visual: Forçamos termos de realismo extremo
        dna_visual = f"High-end hyper-realistic photography, 8k UHD, highly detailed skin texture, raw photo, masterwork, {descricao}"
        data[nome.lower()] = dna_visual
        
        with open(self.db_path, "w") as f:
            json.dump(data, f)
        return f"✅ Personagem '{nome}' salvo na Galeria Tática."

    def listar_personagens(self):
        with open(self.db_path, "r") as f:
            data = json.load(f)
        return list(data.keys())

    def preparar_prompt(self, nome, acao):
        with open(self.db_path, "r") as f:
            data = json.load(f)
        
        nome_chave = nome.lower()
        if nome_chave in data:
            # Combina os traços fixos com a nova ação/cenário
            return f"{data[nome_chave]}, {acao}, cinematic lighting, depth of field."
        return None
