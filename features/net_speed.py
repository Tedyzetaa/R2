import speedtest

class NetSpeedModule:
    def run_test(self):
        try:
            # O print ajuda a saber que não travou
            print("⚡ [SPEEDTEST]: Iniciando drivers (secure=True)...")
            st = speedtest.Speedtest(secure=True)
            
            print("⚡ [SPEEDTEST]: Buscando melhor servidor...")
            st.get_best_server()
            
            print("⚡ [SPEEDTEST]: Testando Download (Aguarde)...")
            # Convertendo para Mbps
            download_speed = st.download() / 1_000_000 
            
            # Vamos pular o Upload para ser mais rápido (já que o Download funcionou no teste)
            # Se quiser testar upload, descomente a linha abaixo:
            # upload_speed = st.upload() / 1_000_000
            
            ping = st.results.ping
            
            relatorio = (
                "⚡ **RELATÓRIO DE REDE**\n"
                f"📥 Download: {download_speed:.2f} Mbps\n"
                f"📶 Latência: {ping:.0f} ms"
            )
            return relatorio

        except Exception as e:
            print(f"Erro detalhado speedtest: {e}")
            return f"❌ Erro no teste: {e}"