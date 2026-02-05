# fix_gui_widgets.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def patch_gui_widgets():
    """Patch para corrigir widgets None na GUI"""
    
    print("🔧 Aplicando patches nos widgets da GUI...")
    
    try:
        import gui.sci_fi_hud as hud_module
        
        # Verificar se a classe existe
        if hasattr(hud_module, 'R2SciFiGUI'):
            original_build = hud_module.R2SciFiGUI._build_interface
            
            def patched_build(self):
                """Versão corrigida com verificação de widgets"""
                try:
                    # Chamar o método original
                    original_build(self)
                    
                    # Verificar widgets críticos
                    critical_widgets = [
                        'input_field', 'input_entry', 'text_input',
                        'output_text', 'response_text', 'console_text',
                        'send_button', 'submit_button', 'execute_button'
                    ]
                    
                    for widget_name in critical_widgets:
                        if hasattr(self, widget_name):
                            widget = getattr(self, widget_name)
                            if widget is None:
                                print(f"⚠️  Widget {widget_name} é None, criando fallback")
                                self._create_fallback_widget(widget_name)
                    
                except AttributeError as e:
                    if "'NoneType' object has no attribute 'get'" in str(e):
                        print("🔧 Detectado erro 'NoneType.get()', aplicando correção...")
                        # Criar widgets básicos
                        self._create_basic_widgets()
                    else:
                        raise
                except Exception as e:
                    print(f"⚠️  Erro na construção da interface: {e}")
                    self._create_basic_widgets()
            
            # Método auxiliar para criar widgets básicos
            def create_fallback_widgets(self):
                """Cria widgets básicos de fallback sem conflito com grid"""
                import customtkinter as ctk
                
                try:
                    # Primeiro, limpar completamente a janela se já houver widgets
                    for widget in self.winfo_children():
                        try:
                            widget.destroy()
                        except:
                            pass
                    
                    # Usar grid de forma limpa
                    self.grid_rowconfigure(0, weight=1)
                    self.grid_columnconfigure(0, weight=1)
                    
                    # Frame principal usando grid
                    self.main_frame = ctk.CTkFrame(self)
                    self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
                    self.main_frame.grid_rowconfigure(1, weight=1)
                    self.main_frame.grid_columnconfigure(0, weight=1)
                    
                    # Título
                    title_label = ctk.CTkLabel(
                        self.main_frame,
                        text="🤖 R2 ASSISTANT - FALLBACK MODE",
                        font=("Segoe UI", 20, "bold")
                    )
                    title_label.grid(row=0, column=0, pady=(10, 20), sticky="ew")
                    
                    # Console de saída
                    self.output_text = ctk.CTkTextbox(
                        self.main_frame,
                        height=300,
                        font=("Consolas", 11)
                    )
                    self.output_text.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
                    self.output_text.insert("1.0", "R2 Assistant - Interface de Fallback\n")
                    self.output_text.insert("end", "Sistema inicializado com segurança.\n")
                    self.output_text.insert("end", "Digite 'ajuda' para ver comandos.\n\n")
                    
                    # Frame de entrada
                    input_frame = ctk.CTkFrame(self.main_frame)
                    input_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
                    input_frame.grid_columnconfigure(0, weight=1)
                    
                    self.input_field = ctk.CTkEntry(
                        input_frame,
                        placeholder_text="Digite um comando...",
                        font=("Segoe UI", 12)
                    )
                    self.input_field.grid(row=0, column=0, sticky="ew", padx=(0, 10))
                    
                    self.send_button = ctk.CTkButton(
                        input_frame,
                        text="Enviar",
                        width=80,
                        command=lambda: self._process_fallback_command()
                    )
                    self.send_button.grid(row=0, column=1)
                    
                    # Vincular Enter ao campo de entrada
                    self.input_field.bind("<Return>", 
                                        lambda e: self._process_fallback_command())
                    
                    # Adicionar handler para o botão de enviar
                    self.send_button.configure(command=self._process_fallback_command)
                    
                    print("✅ Fallback widgets criados com grid")
                    
                except Exception as e:
                    print(f"❌ Erro crítico no fallback: {e}")
                    # Último recurso: mensagem simples
                    error_label = ctk.CTkLabel(
                        self,
                        text="Erro crítico na interface.\nReinicie o aplicativo.",
                        font=("Segoe UI", 14),
                        text_color="red"
                    )
                    error_label.pack(pady=50)

            def _process_fallback_command(self):
                """Processa comandos no modo fallback"""
                try:
                    if hasattr(self, 'input_field'):
                        command = self.input_field.get().strip()
                        if command:
                            # Mostrar comando
                            self.output_text.insert("end", f"\n> {command}\n")
                            
                            # Processar comando (simulado)
                            if command.lower() == "ajuda":
                                response = "Comandos disponíveis: ajuda, hora, data, status"
                            elif command.lower() in ["hora", "que horas são"]:
                                from datetime import datetime
                                response = f"Hora: {datetime.now().strftime('%H:%M:%S')}"
                            elif command.lower() in ["data", "que dia é hoje"]:
                                from datetime import datetime
                                response = f"Data: {datetime.now().strftime('%d/%m/%Y')}"
                            elif command.lower() == "status":
                                response = "Sistema operacional em modo fallback"
                            else:
                                response = f"Comando '{command}' não reconhecido"
                            
                            # Mostrar resposta
                            self.output_text.insert("end", f"📢 {response}\n")
                            self.input_field.delete(0, "end")
                            self.output_text.see("end")
                except Exception as e:
                    print(f"❌ Erro ao processar comando: {e}")
            
            # Adicionar métodos à classe
            hud_module.R2SciFiGUI._build_interface = patched_build
            hud_module.R2SciFiGUI._create_basic_widgets = create_fallback_widgets
            hud_module.R2SciFiGUI._process_fallback_command = _process_fallback_command
            
            print("✅ Patch aplicado: Widgets da GUI protegidos")
    
    except Exception as e:
        print(f"⚠️  Não foi possível aplicar patch GUI: {e}")
    
    print("\n🎉 Patches de widgets aplicados!")

if __name__ == "__main__":
    patch_gui_widgets()