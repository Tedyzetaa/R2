import os
import requests
import subprocess
import shutil
from imageio_ffmpeg import get_ffmpeg_exe

class NOAAService:
    def __init__(self):
        # 1. CME (NASA SOHO)
        self.url_cme = "https://soho.nascom.nasa.gov/data/LATEST/current_c3.gif"
        
        # 2. SDO (NASA)
        self.url_sdo = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0193.mp4"
        
        # 3. ENLIL (NOAA JSON)
        self.url_enlil_json = "https://services.swpc.noaa.gov/products/animations/enlil.json"
        self.base_url_noaa = "https://services.swpc.noaa.gov"
        
        # 4. D-RAP
        self.url_drap = "https://services.swpc.noaa.gov/images/animations/d-rap/global/d-rap/latest.png"

        try:
            self.ffmpeg_path = get_ffmpeg_exe()
        except:
            self.ffmpeg_path = "ffmpeg"

    def _get_headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _converter_gif_para_mp4(self, input_path, output_path):
        try:
            if not os.path.exists(input_path) or os.path.getsize(input_path) < 1000:
                return False
            cmd = [
                self.ffmpeg_path, '-y', '-i', input_path,
                '-vf', "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-movflags', 'faststart', output_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
            return True
        except: return False

    def get_cme_video(self):
        gif_path = "temp_cme.gif"
        mp4_path = "intel_cme.mp4"
        try:
            print("⏳ Baixando CME...")
            res = requests.get(self.url_cme, headers=self._get_headers(), timeout=30)
            if res.status_code == 200:
                with open(gif_path, "wb") as f: f.write(res.content)
                if self._converter_gif_para_mp4(gif_path, mp4_path):
                    if os.path.exists(gif_path): os.remove(gif_path)
                    return mp4_path, "video"
            return None, None
        except: return None, None

    def get_sdo_video(self):
        path = "intel_sdo.mp4"
        try:
            print("⏳ Baixando SDO...")
            res = requests.get(self.url_sdo, stream=True, timeout=60)
            if res.status_code == 200:
                with open(path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=4096): f.write(chunk)
                return path, "video"
            return None, None
        except: return None, None

    def get_enlil_video(self):
        """Constrói o vídeo baixando TODOS os frames disponíveis (Ciclo Completo)"""
        mp4_path = "intel_enlil.mp4"
        temp_dir = "temp_enlil_frames"
        
        try:
            print("⏳ Acessando telemetria bruta do Enlil...")
            
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            # Baixa o JSON com a lista de imagens
            res = requests.get(self.url_enlil_json, headers=self._get_headers(), timeout=20)
            data = res.json()
            
            # --- MODIFICAÇÃO TÁTICA ---
            # Removemos o limite. Pegamos todos os frames disponíveis.
            frames = data 
            total_frames = len(frames)
            print(f"📥 Detectados {total_frames} frames no ciclo de simulação. Baixando...")

            # Download Loop
            downloaded_count = 0
            for i, frame in enumerate(frames):
                img_url = self.base_url_noaa + frame["url"]
                save_path = os.path.join(temp_dir, f"frame_{i:03d}.jpg")
                
                try:
                    img_res = requests.get(img_url, timeout=5)
                    if img_res.status_code == 200:
                        with open(save_path, "wb") as f: f.write(img_res.content)
                        downloaded_count += 1
                except: pass
                
                # Feedback visual no terminal a cada 20 frames para você saber que não travou
                if i % 20 == 0:
                    print(f"   ↳ Progresso: {i}/{total_frames}...")

            if downloaded_count < 10:
                print("❌ Falha: Dados insuficientes para vídeo.")
                shutil.rmtree(temp_dir)
                return self._fallback_enlil_static()

            # Renderização via FFmpeg
            # framerate 18 = Video mais fluido e rápido para cobrir todos os frames
            print(f"⚙️ Renderizando {downloaded_count} frames em alta definição...")
            cmd = [
                self.ffmpeg_path, '-y', 
                '-framerate', '18', 
                '-i', f'{temp_dir}/frame_%03d.jpg', 
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', 
                mp4_path
            ]
            
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
            
            shutil.rmtree(temp_dir) # Limpa a sujeira
            
            if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 1000:
                return mp4_path, "video"
            else:
                return self._fallback_enlil_static()

        except Exception as e:
            print(f"❌ Erro na reconstrução Enlil: {e}")
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            return self._fallback_enlil_static()

    def _fallback_enlil_static(self):
        print("⚠️ Ativando imagem estática de backup.")
        path = "intel_enlil.jpg"
        url = "https://services.swpc.noaa.gov/images/animations/enlil/latest.jpg"
        try:
            res = requests.get(url, headers=self._get_headers())
            with open(path, "wb") as f: f.write(res.content)
            return path, "foto"
        except: return None, None

    def get_drap_map(self):
        path = "intel_drap.png"
        try:
            res = requests.get(self.url_drap, headers=self._get_headers(), timeout=30)
            if res.status_code == 200:
                with open(path, "wb") as f: f.write(res.content)
                return path, "foto"
            return None, None
        except: return None, None