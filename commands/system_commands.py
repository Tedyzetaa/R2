import os
import platform
import subprocess
import pyautogui
import datetime
import pyperclip
import time
import logging

def register_system_commands(command_system, falar, ouvir_comando):
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
            'calculadora': 'calc' if platform.system() == "Windows" else 'gnome-calculator'
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

    # Comandos específicos para abrir programas
    def abrir_chrome(falar_func=None, ouvir_func=None):
        abrir_programa("chrome", falar_func, ouvir_func)

    def abrir_vscode(falar_func=None, ouvir_func=None):
        abrir_programa("vscode", falar_func, ouvir_func)

    # Registra os comandos
    command_system.register_command("olá", dizer_ola, "Cumprimenta o usuário")
    command_system.register_command("hora", dizer_hora, "Diz a hora atual")
    command_system.register_command("data", dizer_data, "Diz a data atual")
    command_system.register_command("tirar print", tirar_print, "Tira um print da tela")
    command_system.register_command("preencher documento", preencher_documento, "Preenche um documento com texto por voz")
    command_system.register_command("mutar áudio", mutar_audio, "Muta o áudio do sistema")
    command_system.register_command("desmutar áudio", desmutar_audio, "Desmuta o áudio do sistema")
    
    # Comandos para abrir programas
    command_system.register_command("abrir chrome", abrir_chrome, "Abre o Google Chrome")
    command_system.register_command("abrir vscode", abrir_vscode, "Abre o Visual Studio Code")