# filename: features/tiktok_publisher.py
import os
import time
import threading
import schedule

class TikTokCommander:
    def __init__(self):
        self.fila = []
        # Horários de pico definidos pelo Comandante
        self.horarios = ["09:00", "12:00", "18:00", "20:00"]
        self._armar_silo()
        print("📱 [TIKTOK COMMANDER]: Silo armado. Aguardando munição.")

    def _armar_silo(self):
        """Programa o relógio interno para os disparos"""
        for h in self.horarios:
            schedule.every().day.at(h).do(self.disparar_missil)
        
        # Inicia a thread do radar temporal em background
        threading.Thread(target=self._radar_loop, daemon=True).start()

    def _radar_loop(self):
        while True:
            schedule.run_pending()
            time.sleep(30)

    def enfileirar(self, video_path):
        """Prepara o vídeo e gera as descrições/hashtags virais baseadas no nome"""
        tema_bruto = os.path.basename(video_path).replace(".mp4", "")
        titulo_limpo = tema_bruto.replace("_", " ")
        
        # Gera hashtags extraindo as palavras principais do título
        tags_dinamicas = " ".join([f"#{palavra}" for palavra in titulo_limpo.split() if len(palavra) > 2])
        descricao_viral = f"{titulo_limpo} 🚀🔥 #fy #fyp #viral {tags_dinamicas}"

        missil = {"path": video_path, "desc": descricao_viral}
        self.fila.append(missil)
        print(f"📥 [TIKTOK]: Míssil enfileirado. Fila atual: {len(self.fila)} vídeos.")
        return len(self.fila)

    def disparar_missil(self):
        """Executa o upload automático no horário programado"""
        if not self.fila:
            print("📡 [TIKTOK] Horário de pico atingido, mas o silo de postagem está vazio.")
            return

        alvo = self.fila.pop(0)
        print(f"\n🚀 [TIKTOK] INICIANDO SEQUÊNCIA DE LANÇAMENTO...")
        print(f"🎬 Arquivo: {alvo['path']}")
        print(f"📝 Descrição: {alvo['desc']}")

        try:
            from tiktok_uploader.upload import upload_video
            
            # Requer o arquivo de cookies na raiz do projeto para autenticação
            caminho_cookies = os.path.abspath("tiktok_cookies.txt")
            if not os.path.exists(caminho_cookies):
                print("❌ [TIKTOK ERRO]: Arquivo 'tiktok_cookies.txt' não encontrado. Abortando lançamento.")
                self.fila.insert(0, alvo) # Devolve para a fila
                return

            # Executa a postagem (headless = invisível)
            upload_video(alvo['path'], description=alvo['desc'], cookies=caminho_cookies, headless=True)
            print("✅ [TIKTOK] Míssil atingiu o alvo com sucesso! Vídeo publicado.")
            
        except Exception as e:
            print(f"❌ [TIKTOK] Falha no lançamento: {e}")
            self.fila.insert(0, alvo) # Devolve para a fila em caso de erro