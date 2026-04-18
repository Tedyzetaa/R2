import os
import shutil

print("🧹 [PROTOCOLO VASSOURA] Iniciando limpeza do cache do R2...\n")

# 1. Expurgar Lixo de Vídeo (yt-dlp e cortes temporários)
temp_dir = "temp_video"
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
    print(f"✅ Lixo residual de vídeo ({temp_dir}/) incinerado.")
else:
    print(f"🆗 Nenhum lixo de vídeo encontrado.")

# 2. Expurgar Memória Vetorial (RAG) - Preserva os PDFs
docs_dir = "static/docs"
arquivos_rag = ["faiss_index.bin", "rag_data.json"]
for arq in arquivos_rag:
    caminho = os.path.join(docs_dir, arq)
    if os.path.exists(caminho):
        os.remove(caminho)
        print(f"✅ Cache de memória RAG ({arq}) resetado.")

# 3. Limpar Cache de Sistema do Python (__pycache__)
pycache_count = 0
for root, dirs, files in os.walk("."):
    if "__pycache__" in dirs:
        caminho_pycache = os.path.join(root, "__pycache__")
        shutil.rmtree(caminho_pycache)
        pycache_count += 1
print(f"✅ {pycache_count} pastas de cache do Python (__pycache__) eliminadas.")

# 4. Opcional: Limpar Mídias Geradas (Descomente as linhas abaixo se quiser apagar os vídeos/imagens prontas)
# media_dir = "static/media"
# if os.path.exists(media_dir):
#     shutil.rmtree(media_dir)
#     os.makedirs(media_dir)
#     print(f"✅ Galeria de mídias geradas ({media_dir}/) esvaziada.")

print("\n🎯 [MISSÃO CUMPRIDA] O cache do R2 foi expurgado. A base está leve e pronta para operar!")