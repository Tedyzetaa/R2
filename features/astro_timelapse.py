import os
import time
import glob
from PIL import Image
from playwright.sync_api import sync_playwright

class AstroTimelapseSystem:
    def __init__(self):
        # Usamos o JPL da NASA pois ele tem botões de controle de tempo fáceis de clicar
        self.base_url = "https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={}"

    def gerar_gif_trajetoria(self, asteroid_id, asteroid_name):
        url = self.base_url.format(asteroid_id)
        
        # Pastas temporárias
        pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pasta_frames = os.path.join(pasta_raiz, "frames_temp")
        caminho_gif = os.path.join(pasta_raiz, "astro_animacao.gif")

        # Limpeza inicial
        if not os.path.exists(pasta_frames): os.makedirs(pasta_frames)
        # Limpa frames antigos
        for f in glob.glob(os.path.join(pasta_frames, "*.jpg")): os.remove(f)

        print(f"🎬 [CINE]: Iniciando produção de timelapse para: {asteroid_name}...")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--headless=new", "--no-sandbox", "--enable-webgl", "--high-dpi-support=1"]
                )
                
                # Contexto menor para o GIF não ficar gigante (800x600)
                context = browser.new_context(viewport={"width": 800, "height": 600})
                page = context.new_page()
                
                print("🎬 [CINE]: Acessando estúdio de simulação...")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # 1. Ativa o Diagrama de Órbita
                try:
                    page.locator("a:has-text('Orbit Diagram')").click(timeout=10000)
                    print("🎬 [CINE]: Motor físico ativado. Aguardando renderização...")
                    time.sleep(8) # Espera o Java carregar
                except:
                    print("❌ [CINE]: Falha ao ativar diagrama.")
                    return None

                # 2. Loop de Captura (10 Quadros)
                print("🎬 [CINE]: Capturando quadros de trajetória...")
                
                # Tenta localizar o botão de "Play" ou "Step Forward" no JPL
                # No JPL novo, os botões são ícones. Vamos tentar avançar o tempo via clique.
                # Se não achar o botão, faremos um GIF de Zoom (Aproximação)
                
                for i in range(10):
                    # Salva o frame
                    frame_path = os.path.join(pasta_frames, f"frame_{i:02d}.jpg")
                    
                    # Tira foto só do canvas (mapa) se possível
                    try:
                        page.locator("#orb_canvas").screenshot(path=frame_path, quality=70)
                    except:
                        page.screenshot(path=frame_path, quality=70)
                    
                    print(f"   📸 Frame {i+1}/10 capturado.")
                    
                    # Tenta avançar o tempo ou simular movimento
                    # No JPL, podemos simular interação injetando script para rotacionar ou avançar
                    # Aqui vamos tentar clicar na "seta para direita" do teclado para avançar o tempo
                    page.keyboard.press("ArrowRight") 
                    page.keyboard.press("ArrowRight") # 2 dias por frame
                    
                    time.sleep(0.5) # Pequena pausa para o render atualizar

                browser.close()

            # 3. Montagem do GIF (Pós-Processamento)
            print("🎬 [CINE]: Renderizando GIF final...")
            frames = []
            lista_imgs = sorted(glob.glob(os.path.join(pasta_frames, "*.jpg")))
            
            if not lista_imgs:
                return None

            for img_path in lista_imgs:
                frames.append(Image.open(img_path))

            # Salva o GIF: Duração de 200ms por frame, Loop infinito
            frames[0].save(
                caminho_gif,
                format='GIF',
                append_images=frames[1:],
                save_all=True,
                duration=200,
                loop=0,
                optimize=True
            )
            
            # Limpeza
            for f in glob.glob(os.path.join(pasta_frames, "*.jpg")): os.remove(f)
            
            if os.path.exists(caminho_gif):
                print(f"✅ [CINE]: Animação gerada: {caminho_gif}")
                return caminho_gif
            return None

        except Exception as e:
            print(f"❌ Erro Cine: {e}")
            return None