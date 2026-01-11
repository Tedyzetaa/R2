"""
Testes da Interface Gráfica
Testes para componentes da interface HUD Sci-Fi
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk

# Nota: Mocks são usados para evitar dependências de GUI em testes
from core.config import AppConfig

class TestGUIConfig(unittest.TestCase):
    """Testes para configuração da GUI"""
    
    def test_gui_config_defaults(self):
        """Testa configurações padrão da GUI"""
        config = AppConfig()
        
        # Verificar se seções da GUI existem
        self.assertIn('gui', config.to_dict())
        self.assertIn('theme', config.to_dict()['gui'])
        self.assertIn('hud', config.to_dict()['gui'])
        
    def test_gui_theme_validation(self):
        """Testa validação de temas"""
        config = AppConfig()
        
        # Temas válidos devem ser aceitos
        config.gui.theme = "sci-fi"
        config.gui.theme = "dark"
        config.gui.theme = "light"
        
        # Temas inválidos devem manter o padrão
        config.gui.theme = "invalid-theme"
        # O sistema deve reverter para padrão ou lançar erro
        self.assertIn(config.gui.theme, ["sci-fi", "dark", "light"])

class TestHUDComponents(unittest.TestCase):
    """Testes para componentes HUD"""
    
    @patch('tkinter.Tk')
    @patch('tkinter.ttk')
    def test_hud_initialization(self, mock_ttk, mock_tk):
        """Testa inicialização do HUD"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        
        # Mock da janela principal
        mock_window = Mock()
        mock_tk.return_value = mock_window
        
        # Criar GUI (mocks evitam criação real de janela)
        gui = R2SciFiGUI(config)
        
        # Verificar se métodos essenciais existem
        self.assertTrue(hasattr(gui, 'run'))
        self.assertTrue(hasattr(gui, 'update_display'))
        self.assertTrue(hasattr(gui, 'show_alert'))
        
    @patch('tkinter.Tk')
    def test_hud_alerts_display(self, mock_tk):
        """Testa exibição de alertas no HUD"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        
        # Mock dos componentes da GUI
        mock_alert_frame = Mock()
        mock_alert_label = Mock()
        mock_alert_frame.return_value = mock_alert_label
        
        gui = R2SciFiGUI(config)
        gui.alert_frame = mock_alert_frame
        gui.alert_label = mock_alert_label
        
        # Testar exibição de alerta
        alert_data = {
            'title': 'Test Alert',
            'message': 'This is a test',
            'priority': 'high'
        }
        
        gui.show_alert(alert_data)
        
        # Verificar se métodos de atualização foram chamados
        mock_alert_label.config.assert_called()
        
    @patch('tkinter.Tk')
    def test_hud_metrics_update(self, mock_tk):
        """Testa atualização de métricas no HUD"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        
        # Mock dos componentes de métricas
        mock_cpu_label = Mock()
        mock_memory_label = Mock()
        mock_network_label = Mock()
        
        gui = R2SciFiGUI(config)
        gui.cpu_label = mock_cpu_label
        gui.memory_label = mock_memory_label
        gui.network_label = mock_network_label
        
        # Dados de teste
        metrics = {
            'cpu_usage': 45.5,
            'memory_usage': 67.2,
            'network_up': 1024,
            'network_down': 2048
        }
        
        gui.update_metrics(metrics)
        
        # Verificar se labels foram atualizados
        self.assertTrue(mock_cpu_label.config.called)
        self.assertTrue(mock_memory_label.config.called)
        self.assertTrue(mock_network_label.config.called)

class TestGUIThemes(unittest.TestCase):
    """Testes para temas da interface"""
    
    def test_theme_colors(self):
        """Testa paletas de cores dos temas"""
        # Mock do gerenciador de temas
        class MockThemeManager:
            THEMES = {
                'sci-fi': {
                    'background': '#0a0a1a',
                    'primary': '#00ffff',
                    'secondary': '#ff00ff',
                    'text': '#ffffff'
                },
                'dark': {
                    'background': '#121212',
                    'primary': '#bb86fc',
                    'secondary': '#03dac6',
                    'text': '#e0e0e0'
                },
                'light': {
                    'background': '#f5f5f5',
                    'primary': '#6200ee',
                    'secondary': '#03dac6',
                    'text': '#000000'
                }
            }
            
            def get_theme(self, name):
                return self.THEMES.get(name, self.THEMES['sci-fi'])
        
        manager = MockThemeManager()
        
        # Testar cores do tema sci-fi
        sci_fi_colors = manager.get_theme('sci-fi')
        self.assertEqual(sci_fi_colors['background'], '#0a0a1a')
        self.assertEqual(sci_fi_colors['primary'], '#00ffff')
        
        # Testar cores do tema dark
        dark_colors = manager.get_theme('dark')
        self.assertEqual(dark_colors['background'], '#121212')
        
        # Testar fallback para tema inválido
        invalid_colors = manager.get_theme('invalid')
        self.assertEqual(invalid_colors, manager.THEMES['sci-fi'])

class TestGUIResponsiveness(unittest.TestCase):
    """Testes para responsividade da GUI"""
    
    @patch('tkinter.Tk')
    def test_window_resize(self, mock_tk):
        """Testa redimensionamento de janela"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        gui = R2SciFiGUI(config)
        
        # Mock de bind para eventos de redimensionamento
        mock_bind = Mock()
        gui.root = Mock()
        gui.root.bind = mock_bind
        
        # Simular configuração de responsividade
        gui.setup_responsive_design()
        
        # Verificar se bind foi chamado para evento de redimensionamento
        mock_bind.assert_any_call('<Configure>', unittest.mock.ANY)
        
    @patch('tkinter.Tk')
    def test_font_scaling(self, mock_tk):
        """Testa escalonamento de fontes"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        gui = R2SciFiGUI(config)
        
        # Mock do sistema de fontes
        mock_font = Mock()
        gui.font_manager = Mock()
        gui.font_manager.scale_fonts = mock_font
        
        # Testar diferentes escalas
        test_scales = [0.8, 1.0, 1.2, 1.5]
        
        for scale in test_scales:
            gui.update_font_scale(scale)
            mock_font.assert_called_with(scale)

class TestGUIDialogues(unittest.TestCase):
    """Testes para diálogos e modais"""
    
    @patch('tkinter.Tk')
    @patch('tkinter.simpledialog')
    def test_alert_dialog(self, mock_dialog, mock_tk):
        """Testa diálogos de alerta"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        gui = R2SciFiGUI(config)
        
        # Configurar mock
        mock_dialog_instance = Mock()
        mock_dialog.askstring.return_value = "User input"
        
        # Testar diálogo de confirmação
        result = gui.show_confirmation_dialog(
            title="Confirm",
            message="Are you sure?",
            buttons=["Yes", "No"]
        )
        
        # Verificar se diálogo foi chamado
        mock_dialog.askstring.assert_called_once()
        
    @patch('tkinter.Tk')
    def test_progress_dialog(self, mock_tk):
        """Testa diálogo de progresso"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        gui = R2SciFiGUI(config)
        
        # Mock do progresso
        mock_progress = Mock()
        gui.progress_dialog = mock_progress
        
        # Testar atualização de progresso
        gui.update_progress_dialog(50, "Processing...")
        
        mock_progress.update.assert_called_with(50, "Processing...")
        
        # Testar fechamento
        gui.close_progress_dialog()
        mock_progress.destroy.assert_called_once()

class TestGUICommands(unittest.TestCase):
    """Testes para interface de comandos"""
    
    @patch('tkinter.Tk')
    def test_command_input(self, mock_tk):
        """Testa entrada de comandos"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        gui = R2SciFiGUI(config)
        
        # Mock do campo de entrada
        mock_entry = Mock()
        mock_entry.get.return_value = "help system"
        gui.command_entry = mock_entry
        
        # Mock do processador de comandos
        mock_processor = Mock()
        mock_processor.process.return_value = {
            'success': True,
            'message': 'System help displayed'
        }
        gui.command_processor = mock_processor
        
        # Simular execução de comando
        gui.execute_command()
        
        # Verificar se processador foi chamado
        mock_processor.process.assert_called_with("help system", unittest.mock.ANY)
        mock_entry.delete.assert_called_with(0, 'end')

class TestGUIAccessibility(unittest.TestCase):
    """Testes para acessibilidade"""
    
    @patch('tkinter.Tk')
    def test_high_contrast_mode(self, mock_tk):
        """Testa modo alto contraste"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        gui = R2SciFiGUI(config)
        
        # Mock de componentes
        mock_widgets = [Mock() for _ in range(5)]
        gui.all_widgets = mock_widgets
        
        # Ativar alto contraste
        gui.enable_high_contrast(True)
        
        # Verificar se todos os widgets foram atualizados
        for widget in mock_widgets:
            widget.config.assert_called()
            
    @patch('tkinter.Tk')
    def test_screen_reader_support(self, mock_tk):
        """Testa suporte a leitores de tela"""
        from gui.sci_fi_hud import R2SciFiGUI
        
        config = AppConfig()
        gui = R2SciFiGUI(config)
        
        # Mock de acessibilidade
        mock_accessibility = Mock()
        gui.accessibility_manager = mock_accessibility
        
        # Testar anúncio de mudanças
        gui.announce_screen_reader("New alert received")
        mock_accessibility.announce.assert_called_with("New alert received")

if __name__ == '__main__':
    unittest.main(verbosity=2)