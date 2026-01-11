"""
Testes do Core do Sistema
Testes unitários para os componentes centrais do R2 Assistant
"""

import unittest
import tempfile
import os
import sys
import json
import time
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Importações do projeto
from core.config import AppConfig
from features.alerts import AlertManager, AlertPriority, AlertType
from features.alerts.notification_system import NotificationSystem, NotificationChannel
from utils.file_utils import FileManager
from utils.validation import Validator
from utils.cache import LRUCache, TTLCache
from utils.security import SecurityManager
from utils.helpers import retry, timeout, ProgressBar

class TestAppConfig(unittest.TestCase):
    """Testes para a configuração do aplicativo"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.config = AppConfig()
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if os.path.exists(self.temp_config_file.name):
            os.unlink(self.temp_config_file.name)
    
    def test_config_creation(self):
        """Testa criação da configuração padrão"""
        self.assertIsNotNone(self.config)
        self.assertIsInstance(self.config.to_dict(), dict)
        
    def test_config_loading(self):
        """Testa carregamento de configuração de arquivo"""
        config_data = {
            "app": {
                "name": "R2 Test",
                "version": "1.0.0"
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        with open(self.temp_config_file.name, 'w') as f:
            json.dump(config_data, f)
        
        config = AppConfig(config_file=self.temp_config_file.name)
        self.assertEqual(config.app.name, "R2 Test")
        
    def test_config_saving(self):
        """Testa salvamento de configuração"""
        temp_save_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False).name
        
        try:
            config = AppConfig()
            config.app.name = "R2 Test Save"
            config.save(temp_save_file)
            
            with open(temp_save_file, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data['app']['name'], "R2 Test Save")
        finally:
            if os.path.exists(temp_save_file):
                os.unlink(temp_save_file)

class TestAlertSystem(unittest.TestCase):
    """Testes para o sistema de alertas"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.alert_manager = AlertManager(max_alerts=10)
        
    def test_alert_creation(self):
        """Testa criação de alertas"""
        alert = self.alert_manager.create_alert(
            title="Test Alert",
            message="This is a test alert",
            priority=AlertPriority.HIGH,
            alert_type=AlertType.SYSTEM,
            source="test_suite"
        )
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.title, "Test Alert")
        self.assertEqual(alert.priority, AlertPriority.HIGH)
        self.assertEqual(alert.source, "test_suite")
        
    def test_alert_retrieval(self):
        """Testa recuperação de alertas"""
        # Criar múltiplos alertas
        for i in range(5):
            self.alert_manager.create_alert(
                title=f"Alert {i}",
                message=f"Message {i}",
                priority=AlertPriority.MEDIUM,
                alert_type=AlertType.INFO,
                source="test"
            )
        
        active_alerts = self.alert_manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 5)
        
    def test_alert_acknowledgment(self):
        """Testa reconhecimento de alertas"""
        alert = self.alert_manager.create_alert(
            title="Test Alert",
            message="Test",
            priority=AlertPriority.MEDIUM,
            alert_type=AlertType.INFO,
            source="test"
        )
        
        self.assertTrue(self.alert_manager.acknowledge_alert(alert.id, user="tester"))
        retrieved_alert = self.alert_manager.get_alert(alert.id)
        self.assertTrue(retrieved_alert.acknowledged)
        
    def test_alert_expiration(self):
        """Testa expiração de alertas"""
        alert = self.alert_manager.create_alert(
            title="Expiring Alert",
            message="This will expire",
            priority=AlertPriority.LOW,
            alert_type=AlertType.INFO,
            source="test",
            ttl_seconds=1  # 1 segundo
        )
        
        time.sleep(1.5)  # Aguardar expiração
        self.assertTrue(alert.is_expired)
        
    def test_alert_statistics(self):
        """Testa estatísticas do sistema de alertas"""
        for i in range(3):
            self.alert_manager.create_alert(
                title=f"Alert {i}",
                message=f"Message {i}",
                priority=AlertPriority.HIGH if i % 2 == 0 else AlertPriority.LOW,
                alert_type=AlertType.SYSTEM,
                source="test"
            )
        
        stats = self.alert_manager.get_stats()
        self.assertEqual(stats['total_created'], 3)
        self.assertEqual(stats['by_priority']['high'], 2)
        self.assertEqual(stats['by_priority']['low'], 1)

class TestNotificationSystem(unittest.TestCase):
    """Testes para o sistema de notificações"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.notification_system = NotificationSystem(max_queue_size=100)
        
    def test_notification_creation(self):
        """Testa criação de notificação"""
        notification_id = self.notification_system.send_notification(
            title="Test Notification",
            message="This is a test notification",
            channel=NotificationChannel.IN_APP,
            priority=NotificationPriority.NORMAL
        )
        
        self.assertIsNotNone(notification_id)
        self.assertGreater(len(notification_id), 0)
        
    @patch('features.alerts.notification_system.asyncio')
    def test_notification_handler(self, mock_asyncio):
        """Testa handlers de notificação"""
        mock_handler = Mock()
        mock_handler.can_send.return_value = True
        mock_handler.send.return_value = True
        mock_handler.get_name.return_value = "Test Handler"
        
        self.notification_system.register_handler(mock_handler)
        self.notification_system.start_workers(num_workers=1)
        
        # Dar tempo para processar
        time.sleep(0.5)
        
        self.notification_system.stop()
        mock_handler.send.assert_called()

class TestFileUtils(unittest.TestCase):
    """Testes para utilitários de arquivo"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_path=self.temp_dir)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_file_creation(self):
        """Testa criação de arquivo"""
        test_content = "Hello, R2 Assistant!"
        filepath = "test.txt"
        
        result = self.file_manager.write_text(filepath, test_content)
        self.assertTrue(result)
        
        read_content = self.file_manager.read_text(filepath)
        self.assertEqual(read_content, test_content)
        
    def test_json_operations(self):
        """Testa operações com JSON"""
        test_data = {
            "name": "R2",
            "version": "1.0.0",
            "features": ["alerts", "notifications"]
        }
        
        filepath = "config.json"
        self.file_manager.write_json(filepath, test_data)
        
        loaded_data = self.file_manager.read_json(filepath)
        self.assertEqual(loaded_data, test_data)
        
    def test_file_find(self):
        """Testa busca de arquivos"""
        # Criar alguns arquivos
        self.file_manager.write_text("file1.txt", "content1")
        self.file_manager.write_text("file2.txt", "content2")
        self.file_manager.write_text("other.md", "content3")
        
        txt_files = self.file_manager.find_files("*.txt")
        self.assertEqual(len(txt_files), 2)
        
        all_files = self.file_manager.find_files("*")
        self.assertEqual(len(all_files), 3)
        
    def test_file_hash(self):
        """Testa cálculo de hash de arquivo"""
        content = "Test content for hash"
        filepath = "hash_test.txt"
        
        self.file_manager.write_text(filepath, content)
        file_hash = self.file_manager.calculate_hash(filepath)
        
        self.assertIsNotNone(file_hash)
        self.assertEqual(len(file_hash), 64)  # SHA256 tem 64 chars hex

class TestValidation(unittest.TestCase):
    """Testes para validação de dados"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.validator = Validator()
        
    def test_email_validation(self):
        """Testa validação de email"""
        valid_emails = [
            "user@example.com",
            "first.last@domain.co.uk",
            "name+tag@domain.org"
        ]
        
        invalid_emails = [
            "invalid",
            "@domain.com",
            "user@.com",
            "user@domain."
        ]
        
        for email in valid_emails:
            self.assertTrue(self.validator._validate_email(email, None, "email"))
        
        for email in invalid_emails:
            self.assertFalse(self.validator._validate_email(email, None, "email"))
            
    def test_url_validation(self):
        """Testa validação de URL"""
        valid_urls = [
            "https://example.com",
            "http://sub.domain.co.uk/path",
            "https://www.example.com:8080/page"
        ]
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "://example.com"
        ]
        
        for url in valid_urls:
            self.assertTrue(self.validator._validate_url(url, None, "url"))
            
        for url in invalid_urls:
            self.assertFalse(self.validator._validate_url(url, None, "url"))
    
    def test_schema_validation(self):
        """Testa validação com schema"""
        schema = {
            "name": {"required": True, "string": True, "min_length": 2},
            "email": {"required": True, "email": True},
            "age": {"integer": True, "min": 18, "max": 120}
        }
        
        valid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        
        invalid_data = {
            "name": "J",  # Muito curto
            "email": "invalid-email",
            "age": 15  # Menor que 18
        }
        
        valid_errors = self.validator.validate(valid_data, schema)
        invalid_errors = self.validator.validate(invalid_data, schema)
        
        self.assertEqual(len(valid_errors), 0)
        self.assertGreater(len(invalid_errors), 0)

class TestCache(unittest.TestCase):
    """Testes para sistema de cache"""
    
    def test_lru_cache(self):
        """Testa cache LRU"""
        cache = LRUCache(max_size=3)
        
        # Adicionar itens
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Acessar key1 para torná-lo recente
        self.assertEqual(cache.get("key1"), "value1")
        
        # Adicionar novo item (key2 deve ser removido por ser o menos recente)
        cache.set("key4", "value4")
        
        self.assertIsNone(cache.get("key2"))  # key2 foi removido
        self.assertIsNotNone(cache.get("key1"))  # key1 ainda está
        self.assertIsNotNone(cache.get("key3"))  # key3 ainda está
        self.assertIsNotNone(cache.get("key4"))  # key4 está
        
    def test_ttl_cache(self):
        """Testa cache com TTL"""
        cache = TTLCache(default_ttl=1)  # 1 segundo
        
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        time.sleep(1.5)  # Aguardar expiração
        self.assertIsNone(cache.get("key1"))  # Deve ter expirado
        
        cache.stop()  # Parar thread de limpeza

class TestSecurity(unittest.TestCase):
    """Testes para segurança"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.security = SecurityManager(secret_key="test-key-12345")
        
    def test_encryption_decryption(self):
        """Testa criptografia e descriptografia"""
        original_data = {
            "username": "r2_user",
            "password": "secret123",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        encrypted = self.security.encrypt_data(original_data)
        decrypted = self.security.decrypt_data(encrypted)
        
        self.assertNotEqual(encrypted, str(original_data))
        self.assertEqual(decrypted, original_data)
        
    def test_password_hashing(self):
        """Testa hashing de senha"""
        password = "MySecurePassword123"
        
        hashed = self.security.hash_password(password)
        self.assertNotEqual(hashed, password)
        self.assertTrue(self.security.verify_password(password, hashed))
        self.assertFalse(self.security.verify_password("wrongpassword", hashed))
        
    def test_token_generation(self):
        """Testa geração e verificação de token"""
        payload = {
            "user_id": 123,
            "username": "test_user",
            "role": "admin"
        }
        
        token = self.security.generate_token(payload, expires_in=3600)
        self.assertIsNotNone(token)
        
        decoded = self.security.verify_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["user_id"], 123)
        self.assertEqual(decoded["username"], "test_user")

class TestHelpers(unittest.TestCase):
    """Testes para helpers utilitários"""
    
    def test_retry_decorator(self):
        """Testa decorator de retry"""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Simulated failure")
        
        with self.assertRaises(ValueError):
            failing_function()
        
        self.assertEqual(call_count, 3)  # Deve ter tentado 3 vezes
        
    def test_progress_bar(self):
        """Testa barra de progresso"""
        import io
        import sys
        
        # Capturar output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            progress = ProgressBar(total=100, width=20)
            
            for i in range(100):
                progress.update()
                if i == 99:
                    progress.finish()
            
            output = captured_output.getvalue()
            self.assertIn("100%", output)
            self.assertIn("100/100", output)
        finally:
            sys.stdout = sys.__stdout__
    
    def test_format_functions(self):
        """Testa funções de formatação"""
        from utils.helpers import format_bytes, format_time, format_number
        
        # Teste format_bytes
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1048576), "1.00 MB")
        
        # Teste format_time
        self.assertEqual(format_time(30), "30.0s")
        self.assertEqual(format_time(90), "1m 30.0s")
        
        # Teste format_number
        self.assertEqual(format_number(1234567), "1.23M")
        self.assertEqual(format_number(1234), "1.23K")

class TestAsyncComponents(unittest.TestCase):
    """Testes para componentes assíncronos"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        self.loop.close()
        
    def test_async_retry(self):
        """Testa decorator de retry assíncrono"""
        call_count = 0
        
        @async_retry(max_attempts=3, delay=0.1)
        async def async_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Simulated async failure")
        
        async def run_test():
            with self.assertRaises(ValueError):
                await async_failing_function()
        
        self.loop.run_until_complete(run_test())
        self.assertEqual(call_count, 3)

if __name__ == '__main__':
    # Executar todos os testes
    unittest.main(verbosity=2)