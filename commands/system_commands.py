import os
import platform
import subprocess
import pyautogui
import datetime
import pyperclip
import time
import logging

def register_system_commands(command_system, falar, ouvir_comando, audio_processor=None):
    """Registra comandos do sistema."""
    logger = logging.getLogger(__name__)

    def dizer_ola(falar_func=None, ouvir_func=None):
        falar_func("Olá! Eu sou o R2, seu assistente pessoal. Como posso ajudar?")

    def dizer_hora(falar_func=None, ouvir_func=None):
        hora_atual = datetime.datetime.now().strftime("%H:%M")
        falar_func(f"Agora são {hora_atual}.")

    def dizer_data(falar_func=None, ouvir_func=None):
        data_atual = datetime.datetime.now().strftime("%d de %B de %Y")
        falar_func(f"Hoje é {data_atual}.")

    def abrir_programa(nome_programa, falar_func=None, ouvir_func=None):
        programas = {
            'chrome': 'chrome' if platform.system() == "Windows" else 'google-chrome',
            'vscode': 'code',
            'notepad': 'notepad' if platform.system() == "Windows" else 'gedit',
            'calculadora': 'calc' if platform.system() == "Windows" else 'gnome-calculator',
            'explorer': 'explorer' if platform.system() == "Windows" else 'nautilus',
            'terminal': 'cmd' if platform.system() == "Windows" else 'gnome-terminal',
            'spotify': 'spotify',
            'discord': 'discord'
        }
        
        programa = programas.get(nome_programa.lower(), nome_programa)
        
        try:
            if platform.system() == "Windows":
                os.startfile(programa)
            else:
                subprocess.Popen([programa])
            falar_func(f"Abrindo {nome_programa}.")
        except Exception as e:
            logger.error(f"Erro ao abrir programa: {e}")
            falar_func(f"Não foi possível abrir o programa {nome_programa}.")

    def tirar_print(falar_func=None, ouvir_func=None):
        try:
            screenshot = pyautogui.screenshot()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            screenshot.save(filename)
            falar_func(f"Print da tela salvo como {filename}.")
        except Exception as e:
            logger.error(f"Erro ao tirar print: {e}")
            falar_func("Não foi possível tirar o print da tela.")

    def preencher_documento(falar_func=None, ouvir_func=None):
        falar_func("O que você gostaria que eu escrevesse?")
        texto_a_escrever = ouvir_func()

        if texto_a_escrever:
            falar_func(f"Preparando para escrever: {texto_a_escrever}.")
            pyperclip.copy(texto_a_escrever)
            falar_func("Por favor, clique onde você deseja que o texto seja inserido. Aguardando 5 segundos...")
            time.sleep(5)

            try:
                pyautogui.hotkey('ctrl', 'v')
                falar_func("Texto inserido com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao colar texto: {e}")
                falar_func("Não foi possível colar o texto. Verifique se a janela do documento está ativa.")
        else:
            falar_func("Não entendi o que você disse. Por favor, tente novamente.")

    def mutar_audio(falar_func=None, ouvir_func=None):
        try:
            # Comando para mutar áudio no Windows
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)  # VK_VOLUME_MUTE
            falar_func("Áudio mutado.")
        except Exception as e:
            logger.error(f"Erro ao mutar áudio: {e}")
            falar_func("Não foi possível mutar o áudio.")

    def desmutar_audio(falar_func=None, ouvir_func=None):
        try:
            # Comando para desmutar áudio no Windows
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)  # VK_VOLUME_MUTE
            falar_func("Áudio desmutado.")
        except Exception as e:
            logger.error(f"Erro ao desmutar áudio: {e}")
            falar_func("Não foi possível desmutar o áudio.")

    def aumentar_volume(falar_func=None, ouvir_func=None):
        try:
            if platform.system() == "Windows":
                import ctypes
                for _ in range(5):  # Aumenta volume 5 vezes
                    ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)  # VK_VOLUME_UP
            falar_func("Volume aumentado.")
        except Exception as e:
            logger.error(f"Erro ao aumentar volume: {e}")
            falar_func("Não foi possível aumentar o volume.")

    def diminuir_volume(falar_func=None, ouvir_func=None):
        try:
            if platform.system() == "Windows":
                import ctypes
                for _ in range(5):  # Diminui volume 5 vezes
                    ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)  # VK_VOLUME_DOWN
            falar_func("Volume diminuído.")
        except Exception as e:
            logger.error(f"Erro ao diminuir volume: {e}")
            falar_func("Não foi possível diminuir o volume.")

    def configurar_voz(falar_func=None, ouvir_func=None):
        """Configura as preferências de voz."""
        if not audio_processor:
            falar_func("Sistema de configuração de voz não disponível.")
            return

        falar_func("Deseja alterar velocidade, volume ou tom da voz?")
        resposta = ouvir_func()
        
        if not resposta:
            return
            
        resposta = resposta.lower()
        
        if 'velocidade' in resposta or 'rápido' in resposta or 'devagar' in resposta:
            falar_func("Diga 'mais rápido', 'mais devagar' ou 'velocidade normal'")
            comando_vel = ouvir_func()
            
            if comando_vel:
                if 'mais rápido' in comando_vel or 'acelerar' in comando_vel:
                    audio_processor.set_voice_rate(200)  # Aumenta a velocidade
                    falar_func("Velocidade da voz aumentada.")
                elif 'mais devagar' in comando_vel or 'reduzir' in comando_vel or 'devagar' in comando_vel:
                    audio_processor.set_voice_rate(100)  # Diminui a velocidade
                    falar_func("Velocidade da voz reduzida.")
                else:
                    audio_processor.set_voice_rate(150)  # Velocidade normal
                    falar_func("Velocidade da voz definida como normal.")
                
        elif 'volume' in resposta:
            falar_func("Diga 'aumentar volume', 'diminuir volume' ou 'volume normal'")
            comando_vol = ouvir_func()
            
            if comando_vol:
                if 'aumentar' in comando_vol:
                    audio_processor.set_voice_volume(1.0)  # Volume máximo
                    falar_func("Volume da voz aumentado.")
                elif 'diminuir' in comando_vol:
                    audio_processor.set_voice_volume(0.5)  # Volume médio
                    falar_func("Volume da voz diminuído.")
                else:
                    audio_processor.set_voice_volume(0.8)  # Volume normal
                    falar_func("Volume da voz definido como normal.")
            
        elif 'tom' in resposta or 'voz' in resposta:
            falar_func("Diga 'tom mais alto', 'tom mais baixo' ou 'tom normal'")
            comando_tom = ouvir_func()
            
            if comando_tom:
                if 'mais alto' in comando_tom or 'alto' in comando_tom:
                    audio_processor.set_voice_pitch(150)  # Tom mais alto
                    falar_func("Tom da voz aumentado.")
                elif 'mais baixo' in comando_tom or 'baixo' in comando_tom:
                    audio_processor.set_voice_pitch(80)   # Tom mais baixo
                    falar_func("Tom da voz diminuído.")
                else:
                    audio_processor.set_voice_pitch(110)  # Tom normal
                    falar_func("Tom da voz definido como normal.")
            
        else:
            falar_func("Opção não reconhecida. Use velocidade, volume ou tom.")

    def listar_voze(falar_func=None, ouvir_func=None):
        """Lista vozes disponíveis (apenas para TTS offline)."""
        if not audio_processor:
            falar_func("Sistema de listagem de vozes não disponível.")
            return

        voices = audio_processor.list_available_voices()
        if not voices:
            falar_func("Nenhuma voz disponível para listar.")
            return

        falar_func(f"Encontradas {len(voices)} vozes disponíveis:")
        for i, voice in enumerate(voices[:5]):  # Mostra apenas as primeiras 5
            falar_func(f"{i+1}. {voice['name']}")

    def alterar_voz(falar_func=None, ouvir_func=None):
        """Altera para uma voz específica."""
        if not audio_processor:
            falar_func("Sistema de alteração de voz não disponível.")
            return

        voices = audio_processor.list_available_voices()
        if not voices:
            falar_func("Nenhuma voz disponível para alterar.")
            return

        falar_func(f"Voze disponíveis. Diga o número da voz desejada (1 a {len(voices)})")
        
        try:
            resposta = ouvir_func()
            if resposta:
                numero = int(''.join(filter(str.isdigit, resposta)))
                if 1 <= numero <= len(voices):
                    if audio_processor.change_voice(numero - 1):
                        falar_func(f"Voz alterada para: {voices[numero-1]['name']}")
                    else:
                        falar_func("Erro ao alterar a voz.")
                else:
                    falar_func(f"Número inválido. Use um número entre 1 e {len(voices)}")
        except ValueError:
            falar_func("Não entendi o número. Por favor, tente novamente.")

    def modo_voz_offline(falar_func=None, ouvir_func=None):
        """Ativa o modo de voz offline."""
        if not audio_processor:
            falar_func("Sistema de voz offline não disponível.")
            return

        # Esta funcionalidade precisaria ser expandida para realmente alterar o modo
        falar_func("Modo de voz offline ativado. Usando síntese de voz local.")
        # Aqui você implementaria a lógica para mudar para pyttsx3

    def modo_voz_online(falar_func=None, ouvir_func=None):
        """Ativa o modo de voz online."""
        if not audio_processor:
            falar_func("Sistema de voz online não disponível.")
            return

        falar_func("Modo de voz online ativado. Usando serviço de síntese de voz em nuvem.")
        # Aqui você implementaria a lógica para mudar para gTTS

    def testar_voz(falar_func=None, ouvir_func=None):
        """Testa a voz atual com uma frase de exemplo."""
        frase_teste = "Olá! Esta é uma demonstração da minha voz. Como estou soando?"
        falar_func(frase_teste)

    # Comandos específicos para abrir programas
    def abrir_chrome(falar_func=None, ouvir_func=None):
        abrir_programa("chrome", falar_func, ouvir_func)

    def abrir_vscode(falar_func=None, ouvir_func=None):
        abrir_programa("vscode", falar_func, ouvir_func)

    def abrir_explorer(falar_func=None, ouvir_func=None):
        abrir_programa("explorer", falar_func, ouvir_func)

    def abrir_terminal(falar_func=None, ouvir_func=None):
        abrir_programa("terminal", falar_func, ouvir_func)

    def abrir_spotify(falar_func=None, ouvir_func=None):
        abrir_programa("spotify", falar_func, ouvir_func)

    def abrir_discord(falar_func=None, ouvir_func=None):
        abrir_programa("discord", falar_func, ouvir_func)

    # Registra os comandos
    command_system.register_command("olá", dizer_ola, "Cumprimenta o usuário")
    command_system.register_command("hora", dizer_hora, "Diz a hora atual")
    command_system.register_command("data", dizer_data, "Diz a data atual")
    command_system.register_command("tirar print", tirar_print, "Tira um print da tela")
    command_system.register_command("preencher documento", preencher_documento, "Preenche um documento com texto por voz")
    command_system.register_command("mutar áudio", mutar_audio, "Muta o áudio do sistema")
    command_system.register_command("desmutar áudio", desmutar_audio, "Desmuta o áudio do sistema")
    command_system.register_command("aumentar volume", aumentar_volume, "Aumenta o volume do sistema")
    command_system.register_command("diminuir volume", diminuir_volume, "Diminui o volume do sistema")
    
    # Novos comandos de voz
    command_system.register_command("configurar voz", configurar_voz, "Configura preferências de voz")
    command_system.register_command("alterar voz", alterar_voz, "Altera a voz do assistente")
    command_system.register_command("voze disponíveis", listar_voze, "Lista vozes disponíveis")
    command_system.register_command("modo voz offline", modo_voz_offline, "Ativa modo de voz offline")
    command_system.register_command("modo voz online", modo_voz_online, "Ativa modo de voz online")
    command_system.register_command("testar voz", testar_voz, "Testa a voz atual")
    
    # Comandos para abrir programas
    command_system.register_command("abrir chrome", abrir_chrome, "Abre o Google Chrome")
    command_system.register_command("abrir vscode", abrir_vscode, "Abre o Visual Studio Code")
    command_system.register_command("abrir explorer", abrir_explorer, "Abre o Explorador de Arquivos")
    command_system.register_command("abrir terminal", abrir_terminal, "Abre o Terminal/CMD")
    command_system.register_command("abrir spotify", abrir_spotify, "Abre o Spotify")
    command_system.register_command("abrir discord", abrir_discord, "Abre o Discord")