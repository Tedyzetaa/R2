import os
import json

print("🧠 [DIAGNÓSTICO] Acessando a caixa preta do R2...\n")

arquivo_memoria = "static/logs/historico_chat.json"

if not os.path.exists(arquivo_memoria):
    print("⚠️ O R2 ainda não tem memórias gravadas. O arquivo JSON está vazio ou não foi criado.")
else:
    try:
        with open(arquivo_memoria, "r", encoding="utf-8") as f:
            historico = json.load(f)
            
        print(f"✅ Memória localizada! O R2 possui {len(historico)} interações gravadas no HD.\n")
        print("ÚLTIMOS REGISTROS NA MEMÓRIA DE LONGO PRAZO:")
        print("=" * 50)
        
        # Pega as últimas 5 interações para não poluir a tela
        for i, interacao in enumerate(historico[-5:]):
            print(f"[{interacao.get('timestamp', 'Data Indisponível')}]")
            print(f"👤 TEDDY: {interacao.get('teddy', '')}")
            print(f"🤖 R2:    {interacao.get('r2', '')}")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Falha ao ler a memória: {e}")

print("\n🎯 Diagnóstico concluído. Descanse, Comandante. O sistema está a vigiar a base.")