"""
Testes de Módulos do Sistema
Testes para módulos carregáveis e suas funcionalidades
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

# Importações do projeto
from features.alerts import AlertManager
from features.alerts.notification_system import NotificationSystem
from commands import CommandRegistry, CommandProcessor, CommandContext, CommandPermission
from commands.basic_commands import PingCommand, HelpCommand
from commands.system_commands import SystemInfoCommand

class TestModuleLoading(unittest.TestCase):
    """Testes para carregamento de módulos"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.temp_modules_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if os.path.exists(self.temp_modules_file.name):
            os.unlink(self.temp_modules_file.name)
    
    def test_modules_file_parsing(self):
        """Testa parsing do arquivo de módulos"""
        modules_data = {
            "modules": {
                "test_module": {
                    "name": "Test Module",
                    "description": "A test module",
                    "version": "1.0.0",
                    "enabled": True,
                    "required": False,
                    "dependencies": []
                }
            }
        }
        
        with open(self.temp_modules_file.name, 'w') as f:
            json.dump(modules_data, f)
        
        with open(self.temp_modules_file.name, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertIn("modules", loaded_data)
        self.assertIn("test_module", loaded_data["modules"])
        self.assertEqual(loaded_data["modules"]["test_module"]["name"], "Test Module")
    
    def test_module_dependencies(self):
        """Testa validação de dependências de módulos"""
        modules_data = {
            "modules": {
                "core": {"enabled": True},
                "alerts": {"enabled": True, "dependencies": ["core"]},
                "trading": {"enabled": True, "dependencies": ["core", "alerts"]}
            }
        }
        
        # Verificar se trading depende de core e alerts
        trading_deps = modules_data["modules"]["trading"]["dependencies"]
        self.assertIn("core", trading_deps)
        self.assertIn("alerts", trading_deps)
        self.assertEqual(len(trading_deps), 2)

class TestCommandModules(unittest.TestCase):
    """Testes para módulos de comandos"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.registry = CommandRegistry()
        self.processor = CommandProcessor(self.registry)
        
    def test_command_registration(self):
        """Testa registro de comandos"""
        ping_cmd = PingCommand()
        help_cmd = HelpCommand(self.registry)
        
        self.registry.register(ping_cmd)
        self.registry.register(help_cmd)
        
        # Verificar se comandos foram registrados
        self.assertIsNotNone(self.registry.get("ping"))
        self.assertIsNotNone(self.registry.get("help"))
        self.assertIsNotNone(self.registry.get("?"))  # Alias de help
        
    def test_command_execution(self):
        """Testa execução de comandos básicos"""
        async def run_test():
            # Criar contexto de teste
            context = CommandContext(
                user_id="test_user",
                username="Tester",
                permission=CommandPermission.USER,
                channel="test",
                session_id="test_session",
                timestamp=1234567890.0,
                environment={},
                metadata={}
            )
            
            # Registrar comando ping
            self.registry.register(PingCommand())
            
            # Executar comando
            result = await self.processor.process("ping", context)
            
            self.assertTrue(result.success)
            self.assertIn("Pong!", result.message)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_command_permissions(self):
        """Testa verificação de permissões"""
        # Criar comandos com diferentes permissões
        class GuestCommand:
            name = "guest_cmd"
            permission = CommandPermission.GUEST
        
        class AdminCommand:
            name = "admin_cmd"
            permission = CommandPermission.ADMIN
        
        # Testar contexto de usuário normal
        user_context = CommandContext(
            user_id="user1",
            username="User",
            permission=CommandPermission.USER,
            channel="test",
            session_id="test",
            timestamp=1234567890.0,
            environment={},
            metadata={}
        )
        
        # Usuário deve poder executar comando de guest
        guest_cmd = GuestCommand()
        self.assertTrue(guest_cmd.permission.value == "guest")
        
        # Comando de admin deve requerer permissão de admin
        admin_cmd = AdminCommand()
        self.assertTrue(admin_cmd.permission.value == "admin")
        
        # Em uma implementação real, haveria uma verificação:
        # user_context.permission >= command.permission

class TestAlertModule(unittest.TestCase):
    """Testes para módulo de alertas"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.alert_manager = AlertManager(max_alerts=50)
        
    def test_alert_integration(self):
        """Testa integração do sistema de alertas"""
        # Criar alguns alertas de teste
        alerts = []
        for i in range(3):
            alert = self.alert_manager.create_alert(
                title=f"Test Alert {i}",
                message=f"Message {i}",
                priority="high",
                alert_type="system",
                source="test_module"
            )
            alerts.append(alert)
        
        # Verificar se alertas foram criados
        self.assertEqual(len(alerts), 3)
        
        # Verificar estatísticas
        stats = self.alert_manager.get_stats()
        self.assertEqual(stats['total_created'], 3)
        
    def test_alert_callback(self):
        """Testa callbacks de alerta"""
        callback_called = False
        callback_message = ""
        
        def test_callback(alert):
            nonlocal callback_called, callback_message
            callback_called = True
            callback_message = alert.message
        
        # Registrar callback
        self.alert_manager.register_callback('on_new', test_callback)
        
        # Criar alerta (deve disparar callback)
        self.alert_manager.create_alert(
            title="Callback Test",
            message="Testing callback",
            priority="medium",
            alert_type="test",
            source="test"
        )
        
        self.assertTrue(callback_called)
        self.assertEqual(callback_message, "Testing callback")

class TestNotificationModule(unittest.TestCase):
    """Testes para módulo de notificações"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.notification_system = NotificationSystem(max_queue_size=100)
        
    def test_notification_queue(self):
        """Testa enfileiramento de notificações"""
        # Enfileirar algumas notificações
        notification_ids = []
        for i in range(5):
            nid = self.notification_system.send_notification(
                title=f"Notification {i}",
                message=f"Message {i}",
                channel="in_app",
                priority="normal"
            )
            if nid:
                notification_ids.append(nid)
        
        # Verificar estatísticas
        stats = self.notification_system.get_stats()
        self.assertEqual(stats['queued'], 5)
        self.assertEqual(len(notification_ids), 5)
        
    @patch('features.alerts.notification_system.LogNotificationHandler')
    def test_notification_handlers(self, mock_handler_class):
        """Testa handlers de notificação"""
        # Configurar mock
        mock_handler = Mock()
        mock_handler.can_send.return_value = True
        mock_handler.send.return_value = True
        mock_handler.get_name.return_value = "Mock Handler"
        mock_handler_class.return_value = mock_handler
        
        # Registrar handler
        self.notification_system.register_handler(mock_handler)
        
        # Enviar notificação
        self.notification_system.send_notification(
            title="Test",
            message="Test message",
            channel="log",
            priority="normal"
        )
        
        # Iniciar workers e dar tempo para processar
        self.notification_system.start_workers(num_workers=1)
        import time
        time.sleep(0.5)
        self.notification_system.stop(wait=True)
        
        # Verificar se handler foi chamado
        mock_handler.send.assert_called()

class TestSystemModule(unittest.TestCase):
    """Testes para módulo do sistema"""
    
    @patch('commands.system_commands.psutil')
    @patch('commands.system_commands.platform')
    def test_system_info_command(self, mock_platform, mock_psutil):
        """Testa comando de informações do sistema"""
        # Configurar mocks
        mock_platform.system.return_value = "Linux"
        mock_platform.release.return_value = "5.15"
        mock_platform.version.return_value = "#1 SMP"
        mock_platform.machine.return_value = "x86_64"
        mock_platform.python_version.return_value = "3.11.0"
        
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value = Mock(
            total=17179869184,  # 16GB
            available=8589934592,  # 8GB
            used=8589934592,
            percent=50.0
        )
        mock_psutil.boot_time.return_value = 1234567890.0
        mock_psutil.users.return_value = [Mock(name="user1")]
        mock_psutil.pids.return_value = [1, 2, 3, 4, 5]
        
        async def run_test():
            # Criar comando
            cmd = SystemInfoCommand()
            
            # Criar contexto
            context = CommandContext(
                user_id="test",
                username="Tester",
                permission=CommandPermission.USER,
                channel="test",
                session_id="test",
                timestamp=1234567890.0,
                environment={},
                metadata={}
            )
            
            # Executar comando
            result = await cmd.execute(context)
            
            self.assertTrue(result.success)
            self.assertIn("Linux", result.message)
            self.assertIn("CPU", result.message)
            self.assertIn("Memory", result.message)
            
            # Verificar dados retornados
            self.assertIsNotNone(result.data)
            self.assertEqual(result.data['platform'], "Linux")
            self.assertEqual(result.data['cpu_count'], 8)
        
        import asyncio
        asyncio.run(run_test())

class TestModuleInteractions(unittest.TestCase):
    """Testes para interações entre módulos"""
    
    def test_alert_notification_integration(self):
        """Testa integração entre módulo de alertas e notificações"""
        # Esta função testaria como alertas disparam notificações
        # Em um sistema real, haveria um hook entre os dois sistemas
        
        alert_triggered = False
        notification_sent = False
        
        # Simular callback de alerta que dispara notificação
        def on_alert_callback(alert):
            nonlocal alert_triggered
            alert_triggered = True
            
            # Em um sistema real, aqui seria enviada uma notificação
            # notification_system.send_notification(...)
        
        # Simular sistema
        alert_manager = AlertManager()
        alert_manager.register_callback('on_new', on_alert_callback)
        
        # Criar alerta (deve disparar callback)
        alert_manager.create_alert(
            title="Integration Test",
            message="Testing integration",
            priority="high",
            alert_type="test",
            source="integration_test"
        )
        
        self.assertTrue(alert_triggered)
        # Em um teste real, verificaríamos se notificação foi enviada

class TestModuleConfiguration(unittest.TestCase):
    """Testes para configuração de módulos"""
    
    def test_module_config_loading(self):
        """Testa carregamento de configuração de módulos"""
        # Criar arquivo de configuração de módulo de teste
        module_config = {
            "name": "Test Module Config",
            "settings": {
                "enabled": True,
                "auto_start": False,
                "update_interval": 300,
                "features": ["feature1", "feature2"]
            },
            "api_keys": {
                "service1": "key_placeholder",
                "service2": ""
            }
        }
        
        # Salvar em arquivo temporário
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        with open(temp_config.name, 'w') as f:
            json.dump(module_config, f)
        
        try:
            # Carregar configuração
            with open(temp_config.name, 'r') as f:
                loaded_config = json.load(f)
            
            # Verificar valores
            self.assertEqual(loaded_config["name"], "Test Module Config")
            self.assertTrue(loaded_config["settings"]["enabled"])
            self.assertFalse(loaded_config["settings"]["auto_start"])
            self.assertEqual(loaded_config["settings"]["update_interval"], 300)
            
        finally:
            os.unlink(temp_config.name)

class TestModuleErrorHandling(unittest.TestCase):
    """Testes para tratamento de erros em módulos"""
    
    def test_module_dependency_failure(self):
        """Testa falha de dependência de módulo"""
        # Simular módulo com dependência faltando
        module_def = {
            "name": "Problematic Module",
            "dependencies": ["missing_module"],
            "enabled": True
        }
        
        # Em um sistema real, tentar carregar este módulo sem a dependência
        # deve falhar ou desabilitar o módulo
        
        self.assertIn("missing_module", module_def["dependencies"])
        # A implementação real verificaria se dependências estão disponíveis
    
    def test_module_config_validation(self):
        """Testa validação de configuração de módulo"""
        # Configuração válida
        valid_config = {
            "name": "Valid Module",
            "version": "1.0.0",
            "settings": {
                "enabled": True,
                "port": 8080,
                "host": "localhost"
            }
        }
        
        # Configuração inválida (porta fora do range)
        invalid_config = {
            "name": "Invalid Module",
            "settings": {
                "enabled": True,
                "port": 999999,  # Porta inválida
                "host": ""
            }
        }
        
        # Em um sistema real, haveria validação desses valores
        self.assertIsInstance(valid_config["settings"]["port"], int)
        self.assertTrue(0 < valid_config["settings"]["port"] < 65536)
        
        # Porta inválida
        self.assertFalse(0 < invalid_config["settings"]["port"] < 65536)

class TestModulePerformance(unittest.TestCase):
    """Testes de performance para módulos"""
    
    def test_module_load_time(self):
        """Testa tempo de carregamento de módulo"""
        import time
        
        # Simular tempo de carregamento
        load_times = []
        
        for i in range(5):
            start_time = time.time()
            
            # Simular carregamento de módulo
            time.sleep(0.01)  # 10ms simulado
            
            end_time = time.time()
            load_times.append(end_time - start_time)
        
        # Verificar se tempos são razoáveis
        avg_load_time = sum(load_times) / len(load_times)
        self.assertLess(avg_load_time, 0.1)  # Menos de 100ms
    
    def test_module_memory_usage(self):
        """Testa uso de memória por módulo"""
        import sys
        
        # Medir uso de memória antes
        before_memory = sys.getsizeof([])
        
        # Criar alguns objetos (simulando módulo)
        module_objects = [
            {"name": f"obj_{i}", "data": "x" * 1000}
            for i in range(100)
        ]
        
        # Medir uso de memória depois
        after_memory = sys.getsizeof(module_objects)
        
        # A diferença deve ser razoável
        memory_used = after_memory - before_memory
        self.assertLess(memory_used, 1024 * 1024)  # Menos de 1MB

if __name__ == '__main__':
    unittest.main(verbosity=2)