import os
import shutil
import re
from datetime import datetime

def apply_patch():
    print("Iniciando Patch v16: Módulo Alpha (Vazamento de Ativo e Trava de Aquecimento)")
    
    # Validação do arquivo alvo
    target_file = 'alpha_module.py'
    if not os.path.exists(target_file):
        print(f"[ERRO] {target_file} não encontrado. Certifique-se de executar este script em c:\\R2")
        return

    # 1. Sistema de Backup de Segurança
    backup_dir = "backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"alpha_module_bak_{timestamp}.py")
    
    try:
        shutil.copy2(target_file, backup_path)
        print(f"[OK] Backup de segurança criado: {backup_path}")
    except Exception as e:
        print(f"[ERRO] Falha ao criar backup: {e}")
        return

    # 2. Leitura do Código Fonte
    with open(target_file, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    modificado = False

    # 3. Patch A: Correção do Vazamento de Ativo (Mover _data_lock para baixo)
    # Usa Regex (re.DOTALL) para capturar o bloco independente de quebras de linha/espaços extras
    padrao_vazamento = r"(asset_id\s*=\s*int\(match_id\.group\(1\)\))\s*\n\s*with\s+self\._data_lock:\s*\n\s*self\._last_asset_id\s*=\s*asset_id(.*?)(if\s+asset_id\s*!=\s*76:\s*\n\s*return)"
    
    substituicao_vazamento = r"\1\2\3\n\n            # [PATCH v16] Só atualiza a variável de estado se passar pelo filtro de ativo\n            with self._data_lock:\n                self._last_asset_id = asset_id"
    
    novo_conteudo, num_subs1 = re.subn(padrao_vazamento, substituicao_vazamento, conteudo, flags=re.DOTALL)
    
    if num_subs1 > 0:
        print(f"[OK] Patch A aplicado: Filtro de ativo ({num_subs1} ocorrência) isolado com sucesso.")
        conteudo = novo_conteudo
        modificado = True
    else:
        print("[AVISO] Patch A ignorado: O código original já foi alterado ou o bloco não foi localizado.")

    # 4. Patch B: Correção da Trava de Aquecimento (10 -> 20 Velas)
    novo_conteudo, num_subs2_a = re.subn(r'if\s+history_len\s*<\s*10:', 'if history_len < 20:', conteudo)
    novo_conteudo, num_subs2_b = re.subn(r'Aquecimento:\s*\{history_len\}/10\s*velas', 'Aquecimento: {history_len}/20 velas', novo_conteudo)
    
    if num_subs2_a > 0 or num_subs2_b > 0:
        print(f"[OK] Patch B aplicado: Trava de aquecimento alinhada com as exigências matemáticas (20 velas).")
        conteudo = novo_conteudo
        modificado = True
    else:
         print("[AVISO] Patch B ignorado: Variável de '10 velas' não encontrada.")

    # 5. Gravação Segura
    if modificado:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"\n[SUCESSO] Sistema atualizado. O arquivo {target_file} está pronto para operação.")
    else:
        print("\n[INFO] Nenhuma modificação foi necessária. O sistema já parece estar atualizado.")

if __name__ == "__main__":
    apply_patch()