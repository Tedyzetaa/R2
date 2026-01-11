import asyncio
import edge_tts
import pygame
import os
import uuid  # Biblioteca para gerar nomes únicos

# Configuração da Voz (pode testar 'pt-BR-FranciscaNeural' se preferir)
VOZ = "pt-BR-AntonioNeural"

def falar(texto):
    """Gera um arquivo único para cada fala, evitando erros de arquivo corrompido"""
    if not texto: return

    # Gera um nome aleatório (ex: tts_4f8a1...mp3)
    arquivo_temp = f"tts_{uuid.uuid4().hex}.mp3"

    try:
        # 1. Limpeza de Lixo (Remove áudios velhos que já tocaram)
        _limpar_audios_antigos()

        # 2. Geração do Áudio
        async def gerar():
            communicate = edge_tts.Communicate(texto, VOZ)
            await communicate.save(arquivo_temp)

        asyncio.run(gerar())

        # 3. Reprodução
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Para qualquer som anterior e libera o arquivo
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except:
            pass # Versões antigas do pygame podem não ter unload, ignorar

        pygame.mixer.music.load(arquivo_temp)
        pygame.mixer.music.play()

        # Opcional: Se quiser esperar terminar de falar para não encavalar
        # while pygame.mixer.music.get_busy():
        #     pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"❌ [ERRO DE VOZ]: {e}")

def _limpar_audios_antigos():
    """Remove arquivos tts_*.mp3 antigos da pasta"""
    try:
        diretorio = os.getcwd()
        for arquivo in os.listdir(diretorio):
            if arquivo.startswith("tts_") and arquivo.endswith(".mp3"):
                try:
                    # Tenta deletar. Se o Pygame estiver usando, vai dar erro e ignoramos.
                    os.remove(os.path.join(diretorio, arquivo))
                except PermissionError:
                    pass # Arquivo ainda em uso, deixa para a próxima
    except Exception:
        pass