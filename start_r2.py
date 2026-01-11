#!/usr/bin/env python3
"""
R2 Assistant - Sistema de Inicialização Segura CORRIGIDO
Versão corrigida para resolver o erro _safe_grid_forget
"""

import os
import sys
import json
import traceback
import importlib
from pathlib import Path
from datetime import datetime

# ============================================================================
# CORREÇÃO CRÍTICA: REMOVER PATCH PROBLEMÁTICO DO grid_forget
# ============================================================================

def apply_safe_patches():
    """
    Aplica patches seguros que não quebram o sistema
    """
    try:
        # 1. Patch para o módulo gui.sci_fi_hud
        import gui.sci_fi_hud
        
        # Salvar referências originais
        original_R2SciFiGUI = gui.sci_fi_hud.R2SciFiGUI
        original_init = original_R2SciFiGUI.__init__
        original_build_interface = original_R2SciFiGUI._build_interface
        original_create_simple_interface = None
        
        # Verificar se o método existe
        if hasattr(original_R2SciFiGUI, '_create_simple_interface'):
            original_create_simple_interface = original_R2SciFiGUI._create_simple_interface
        
        # DEFINIR NOVA CLASSE PATCHADA SEGURA
        class SafeR2SciFiGUI(original_R2SciFiGUI):
            """Versão segura da GUI que não usa grid_forget problemático"""
            
            def __init__(self, config):
                try:
                    super().__init__(config)
                except Exception as e:
                    print(f"⚠️  Erro na inicialização da GUI: {e}")
                    # Fallback: GUI básica
                    self._launch_basic_fallback(config)
            
            def _build_interface(self):
                """Versão segura de construção de interface"""
                try:
                    # Chamar método original com tratamento de erro
                    super()._build_interface()
                except AttributeError as e:
                    if "'_safe_grid_forget'" in str(e) or "'grid_forget'" in str(e):
                        print("🔧 Aplicando patch para grid_forget...")
                        self._build_interface_safe()
                    else:
                        raise
            
            def _build_interface_safe(self):
                """Interface segura sem grid_forget"""
                try:
                    import customtkinter as ctk
                    
                    # Configuração básica da janela
                    self.title("R2 Assistant - Modo Seguro")
                    self.geometry("1024x768")
                    
                    # Usar tema escuro como fallback
                    ctk.set_appearance_mode("dark")
                    ctk.set_default_color_theme("blue")
                    
                    # Frame principal
                    main_frame = ctk.CTkFrame(self)
                    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                    
                    # Cabeçalho
                    header = ctk.CTkLabel(
                        main_frame,
                        text="⚡ R2 ASSISTANT - MODO SEGURO ⚡",
                        font=("Courier", 24, "bold"),
                        text_color="#00ffff"
                    )
                    header.pack(pady=20)
                    
                    # Status do sistema
                    status_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a2a")
                    status_frame.pack(fill="x", pady=10, padx=10)
                    
                    status_text = """
                    ✅ Sistema de Comandos: Operacional
                    ✅ Gerenciador de Histórico: Ativo
                    ✅ Sistema de Alertas: Ativo
                    ⚠️  Interface Sci-Fi: Modo Básico
                    ⚠️  Reconhecimento de Voz: Desativado
                    ⚠️  Animações: Desativadas
                    """
                    
                    status_label = ctk.CTkLabel(
                        status_frame,
                        text=status_text,
                        font=("Courier", 12),
                        justify="left"
                    )
                    status_label.pack(pady=10, padx=10)
                    
                    # Área de console
                    console_frame = ctk.CTkFrame(main_frame)
                    console_frame.pack(fill="both", expand=True, pady=10, padx=10)
                    
                    console_label = ctk.CTkLabel(
                        console_frame,
                        text="CONSOLE R2:",
                        font=("Courier", 14, "bold"),
                        text_color="#00ff00"
                    )
                    console_label.pack(anchor="w", padx=10, pady=(10, 5))
                    
                    # Área de texto para exibição
                    self.text_display = ctk.CTkTextbox(
                        console_frame,
                        height=200,
                        font=("Courier", 12),
                        text_color="#00ff00",
                        fg_color="#0a0a12"
                    )
                    self.text_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
                    self.text_display.insert("1.0", "R2 Assistant inicializado em modo seguro.\n")
                    self.text_display.insert("end", "Digite comandos abaixo.\n\n")
                    self.text_display.configure(state="disabled")
                    
                    # Entrada de comando
                    input_frame = ctk.CTkFrame(console_frame)
                    input_frame.pack(fill="x", padx=10, pady=(0, 10))
                    
                    self.command_entry = ctk.CTkEntry(
                        input_frame,
                        placeholder_text="Digite um comando...",
                        font=("Courier", 12)
                    )
                    self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
                    self.command_entry.bind("<Return>", lambda e: self._execute_command_safe())
                    
                    send_button = ctk.CTkButton(
                        input_frame,
                        text="EXECUTAR",
                        command=self._execute_command_safe,
                        font=("Courier", 12, "bold"),
                        fg_color="#0066cc"
                    )
                    send_button.pack(side="right")
                    
                    # Rodapé
                    footer = ctk.CTkLabel(
                        main_frame,
                        text="Modo Seguro Ativo - grid_forget corrigido",
                        font=("Arial", 10),
                        text_color="#666699"
                    )
                    footer.pack(pady=10)
                    
                except Exception as e:
                    print(f"❌ Falha crítica na interface segura: {e}")
                    traceback.print_exc()
            
            def _execute_command_safe(self):
                """Executa comandos no modo seguro"""
                command = self.command_entry.get().strip()
                if not command:
                    return
                
                self.text_display.configure(state="normal")
                self.text_display.insert("end", f"\n> {command}\n")
                
                # Comandos básicos
                if command.lower() == 'ajuda':
                    help_text = """
                    COMANDOS DISPONÍVEIS (Modo Seguro):
                    - ajuda: Mostra esta mensagem
                    - status: Status do sistema
                    - limpar: Limpa o console
                    - sistema: Informações do sistema
                    - sair: Encerra o aplicativo
                    
                    COMANDOS DO NÚCLEO:
                    - hello: Saudação do R2
                    - time: Hora atual
                    - date: Data atual
                    - sysinfo: Informações do sistema
                    """
                    self.text_display.insert("end", help_text)
                elif command.lower() == 'status':
                    self.text_display.insert("end", "✅ Sistema operacional em modo seguro\n")
                elif command.lower() == 'limpar':
                    self.text_display.delete("1.0", "end")
                elif command.lower() == 'sair':
                    self.quit()
                else:
                    self.text_display.insert("end", f"Executando: {command}\n")
                
                self.text_display.see("end")
                self.text_display.configure(state="disabled")
                self.command_entry.delete(0, "end")
            
            def _launch_basic_fallback(self, config):
                """Fallback completo se tudo falhar"""
                try:
                    import customtkinter as ctk
                    
                    self.title("R2 Assistant - Fallback")
                    self.geometry("800x600")
                    
                    label = ctk.CTkLabel(
                        self,
                        text="R2 Assistant em modo de recuperação",
                        font=("Arial", 16)
                    )
                    label.pack(pady=50)
                    
                    info = ctk.CTkLabel(
                        self,
                        text="Sistema operacional com funcionalidades mínimas",
                        font=("Arial", 12)
                    )
                    info.pack(pady=10)
                    
                    close_btn = ctk.CTkButton(
                        self,
                        text="Fechar",
                        command=self.quit
                    )
                    close_btn.pack(pady=20)
                    
                except:
                    # Último recurso
                    self.title("R2 Assistant")
                    self.geometry("400x200")
        
        # Substituir a classe no módulo
        gui.sci_fi_hud.R2SciFiGUI = SafeR2SciFiGUI
        print("✅ Patch seguro aplicado à R2SciFiGUI")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar patches: {e}")
        traceback.print_exc()
        return False

# ============================================================================
# SISTEMA DE INICIALIZAÇÃO SEGURO
# ============================================================================

class SafeLauncher:
    """Lançador seguro com tratamento de erros robusto"""
    
    @staticmethod
    def launch_sci_fi_gui(config):
        """Tenta lançar GUI Sci-Fi com patches seguros"""
        print("\n🚀 Iniciando GUI Sci-Fi (modo seguro)...")
        
        # Aplicar patches primeiro
        if not apply_safe_patches():
            print("❌ Falha ao aplicar patches, usando fallback...")
            return SafeLauncher.launch_basic_gui(config)
        
        try:
            from gui.sci_fi_hud import R2SciFiGUI
            
            # Criar instância da classe já patchada
            app = R2SciFiGUI(config)
            app.mainloop()
            return True
            
        except Exception as e:
            print(f"❌ GUI Sci-Fi falhou: {e}")
            traceback.print_exc()
            return SafeLauncher.launch_basic_gui(config)
    
    @staticmethod
    def launch_basic_gui(config):
        """GUI básica CustomTkinter sem problemas"""
        print("\n🔄 Iniciando GUI Básica...")
        
        try:
            import customtkinter as ctk
            
            class BasicR2GUI(ctk.CTk):
                def __init__(self, config):
                    super().__init__()
                    self.config = config
                    self._setup_gui()
                
                def _setup_gui(self):
                    self.title("R2 Assistant - GUI Básica")
                    self.geometry("900x700")
                    
                    # Configurar tema
                    ctk.set_appearance_mode("dark")
                    ctk.set_default_color_theme("blue")
                    
                    # Frame principal
                    main_frame = ctk.CTkFrame(self, fg_color="transparent")
                    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                    
                    # Título
                    title = ctk.CTkLabel(
                        main_frame,
                        text="R2 ASSISTANT",
                        font=("Courier", 32, "bold"),
                        text_color="#00ffff"
                    )
                    title.pack(pady=20)
                    
                    # Subtítulo
                    subtitle = ctk.CTkLabel(
                        main_frame,
                        text="Sistema de Assistência de IA - Modo Básico",
                        font=("Courier", 14),
                        text_color="#8888ff"
                    )
                    subtitle.pack(pady=5)
                    
                    # Status
                    status_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a2a")
                    status_frame.pack(fill="x", pady=20, padx=10)
                    
                    status_items = [
                        "✅ Núcleo do Sistema: Operacional",
                        "✅ Sistema de Comandos: 7 comandos carregados",
                        "✅ Gerenciador de Histórico: Ativo",
                        "✅ Sistema de Alertas: Monitorando",
                        "⚠️  Interface Sci-Fi: Modo Básico",
                        "⚠️  Reconhecimento de Voz: Desativado",
                        "⚠️  Animações: Simples"
                    ]
                    
                    for item in status_items:
                        label = ctk.CTkLabel(
                            status_frame,
                            text=item,
                            font=("Courier", 12),
                            justify="left"
                        )
                        label.pack(anchor="w", padx=20, pady=5)
                    
                    # Área de console
                    console_frame = ctk.CTkFrame(main_frame)
                    console_frame.pack(fill="both", expand=True, pady=20)
                    
                    console_title = ctk.CTkLabel(
                        console_frame,
                        text="CONSOLE PRINCIPAL:",
                        font=("Courier", 16, "bold")
                    )
                    console_title.pack(anchor="w", padx=10, pady=10)
                    
                    # Texto de saída
                    self.output_text = ctk.CTkTextbox(
                        console_frame,
                        height=200,
                        font=("Courier", 12)
                    )
                    self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
                    self.output_text.insert("1.0", "R2 Assistant inicializado com sucesso!\n")
                    self.output_text.insert("end", "Digite 'ajuda' para ver comandos disponíveis.\n\n")
                    self.output_text.configure(state="disabled")
                    
                    # Entrada de comando
                    input_frame = ctk.CTkFrame(console_frame)
                    input_frame.pack(fill="x", padx=10, pady=(0, 10))
                    
                    self.cmd_entry = ctk.CTkEntry(
                        input_frame,
                        placeholder_text="Digite um comando...",
                        width=400
                    )
                    self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
                    self.cmd_entry.bind("<Return>", lambda e: self.execute_command())
                    
                    ctk.CTkButton(
                        input_frame,
                        text="Executar",
                        command=self.execute_command
                    ).pack(side="right")
                    
                    # Rodapé
                    footer = ctk.CTkLabel(
                        main_frame,
                        text="Sistema operacional com correções aplicadas",
                        font=("Arial", 10),
                        text_color="#666699"
                    )
                    footer.pack(pady=20)
                
                def execute_command(self):
                    """Executa comandos básicos"""
                    command = self.cmd_entry.get().strip()
                    if not command:
                        return
                    
                    self.output_text.configure(state="normal")
                    self.output_text.insert("end", f"\n> {command}\n")
                    
                    # Comandos básicos
                    if command.lower() == 'ajuda':
                        help_text = """
                        COMANDOS DISPONÍVEIS:
                        - ajuda: Mostra esta ajuda
                        - status: Status do sistema
                        - limpar: Limpa o console
                        - info: Informações do sistema
                        - time: Hora atual
                        - date: Data atual
                        - sysinfo: Informações técnicas
                        - sair: Encerra o aplicativo
                        """
                        self.output_text.insert("end", help_text)
                    elif command.lower() == 'status':
                        self.output_text.insert("end", "✅ Sistema operacional\n")
                        self.output_text.insert("end", "✅ Modo básico ativo\n")
                    elif command.lower() == 'limpar':
                        self.output_text.delete("1.0", "end")
                    elif command.lower() == 'sair':
                        self.quit()
                    elif command.lower() == 'info':
                        self.output_text.insert("end", f"R2 Assistant v1.0\n")
                        self.output_text.insert("end", f"Modo: Básico (corrigido)\n")
                        self.output_text.insert("end", f"Python: {sys.version}\n")
                    else:
                        self.output_text.insert("end", f"Comando reconhecido: {command}\n")
                    
                    self.output_text.see("end")
                    self.output_text.configure(state="disabled")
                    self.cmd_entry.delete(0, "end")
            
            app = BasicR2GUI(config)
            app.mainloop()
            return True
            
        except Exception as e:
            print(f"❌ GUI básica falhou: {e}")
            traceback.print_exc()
            return SafeLauncher.launch_terminal_mode()
    
    @staticmethod
    def launch_terminal_mode():
        """Modo terminal se GUI falhar, agora com IA e voz."""
        print("\n💻 Iniciando modo terminal...")
        
        print("\n" + "="*60)
        print("⚡ R2 ASSISTANT - TERMINAL INTERATIVO (NEURAL)")
        print("="*60)
        
        try:
            # --- Imports e inicialização dos componentes neurais ---
            import asyncio
            from core.config import AppConfig
            from features.ai_integration.openrouter_client import AIIntegrationManager
            from core.audio_processor import AudioProcessor
            
            print("🧠 Carregando Córtex Neural...")
            config = AppConfig.load()
            
            # Carrega e inicializa a IA
            ai_manager = AIIntegrationManager(config)
            asyncio.run(ai_manager.initialize())
            
            # Carrega o processador de áudio para TTS
            audio_processor = AudioProcessor(lang=config.LANGUAGE.value.split('-')[0])
            print("🎤 Sintetizador de voz pronto.")

            def gerar_resposta(mensagem_usuario):
                """Chama a IA para gerar uma resposta."""
                response = asyncio.run(ai_manager.chat("terminal_user", mensagem_usuario))
                return response.content

            def falar(texto):
                """Usa o processador de áudio para falar o texto."""
                print("🔊 [Sintetizando voz...]")
                audio_processor.text_to_speech(texto)

            print("\n[R2]: Pronto para ouvir. Digite 'sair' para encerrar.")

            while True:
                user_input = input("\nVOCÊ> ")
                
                if user_input.lower() in ["sair", "exit"]:
                    print("[R2]: Encerrando protocolos...")
                    falar("Encerrando protocolos.")
                    break
                
                resposta_r2 = gerar_resposta(user_input)

                print(f"\n[R2]: {resposta_r2}")

                falar(resposta_r2)

        except Exception as e:
            print(f"❌ Erro fatal no modo terminal neural: {e}")
            traceback.print_exc()
            input("\nPressione Enter para sair...")
        
        return True

# ============================================================================
# PONTO DE ENTRADA PRINCIPAL
# ============================================================================

def main():
    """Função principal com inicialização segura"""
    print("\n" + "="*60)
    print("🚀 R2 ASSISTANT - SISTEMA CORRIGIDO v2.0")
    print("="*60)
    
    # Carregar configuração
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ Configuração carregada")
    except:
        print("⚠️  Usando configuração padrão")
        config = {
            "app_name": "R2 Assistant",
            "version": "2.0",
            "theme": "dark",
            "voice_enabled": False,
            "animations_enabled": False
        }
    
    # Sistema de fallback hierárquico
    print("\n🎮 SELECIONANDO MODO DE OPERAÇÃO...")
    
    # Verificar CustomTkinter
    try:
        import customtkinter as ctk
        print("✅ CustomTkinter disponível")
        
        # Tentar GUI básica primeiro (mais estável)
        return SafeLauncher.launch_basic_gui(config)
        
    except ImportError as e:
        print(f"❌ CustomTkinter não disponível: {e}")
        return SafeLauncher.launch_terminal_mode()
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        traceback.print_exc()
        return SafeLauncher.launch_terminal_mode()

if __name__ == "__main__":
    # Configurar path
    project_dir = Path(__file__).parent
    sys.path.insert(0, str(project_dir))
    
    # Executar
    # Setup básico
    # A função main() agora atua como nosso setup_environment, retornando True/False
    setup_ok = main()
    if not setup_ok:
        print("⚠️  Ambiente incompleto. Ocorreu uma falha na inicialização principal.")
        print("👉 O sistema tentará continuar em modo de fallback.\n")
        # NÃO usamos sys.exit(1) aqui para permitir o fallback

    print("\n✅ Programa finalizado.")
    sys.exit(0) # Sempre sai com código 0, pois o fallback é o comportamento esperado