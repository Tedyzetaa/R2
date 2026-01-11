import cv2
import speedtest

print("--- INICIANDO DIAGNÓSTICO DE HARDWARE ---")

# 1. TESTE DE CÂMERA (Varredura de Portas)
print("\n👁️ Testando Câmeras...")
for index in range(3): # Tenta porta 0, 1 e 2
    print(f"   > Tentando conectar na câmera índice {index}...")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"   ✅ SUCESSO! Câmera encontrada no índice {index}.")
            cap.release()
        else:
            print(f"   ⚠️ Câmera {index} abriu mas a imagem veio vazia (Escura/Bloqueada).")
    else:
        print(f"   ❌ Nenhuma câmera no índice {index}.")

# 2. TESTE DE REDE
print("\n⚡ Testando Speedtest (Isso pode travar)...")
try:
    st = speedtest.Speedtest(secure=True)
    print("   > Buscando servidor...")
    st.get_best_server()
    print("   > Testando Download...")
    down = st.download() / 1000000
    print(f"   ✅ SUCESSO! Download: {down:.2f} Mbps")
except Exception as e:
    print(f"   ❌ ERRO NO SPEEDTEST: {e}")

print("\n--- FIM DO DIAGNÓSTICO ---")
input("Pressione ENTER para sair...")