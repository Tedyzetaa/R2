import sys
import os
sys.path.append('.')

from core.command_system import CommandSystem
from core.audio_processor import AudioProcessor
from commands.system_commands import register_system_commands
from commands.web_commands import register_web_commands
from commands.basic_commands import register_basic_commands

def test_commands():
    command_system = CommandSystem()
    audio_processor = AudioProcessor()
    
    # Registrar comandos
    def fake_listen():
        return "teste"
    
    def fake_speak(text):
        print(f"🔊 R2 diz: {text}")
    
    register_system_commands(command_system, fake_speak, fake_listen)
    register_web_commands(command_system, fake_speak, fake_listen)
    register_basic_commands(command_system, fake_speak, fake_listen)
    
    print("📋 Comandos registrados:")
    commands = command_system.get_available_commands()
    for cmd in commands:
        print(f"  - {cmd['trigger']}: {cmd['description']}")
    
    print(f"\n🎯 Total: {len(commands)} comandos")
    
    # Testar TODOS os comandos
    test_cmds = ["olá", "hora", "data", "ajuda", "sobre", "notícias", "bitcoin"]
    print("\n🧪 Testando comandos:")
    
    success_count = 0
    for cmd in test_cmds:
        print(f"  Executando '{cmd}': ", end="")
        success = command_system.execute_command(cmd, fake_speak, fake_listen)
        if success:
            success_count += 1
            print("✅")
        else:
            print("❌")
    
    print(f"\n📊 Resultado: {success_count}/{len(test_cmds)} comandos funcionando")
    
    if success_count == len(test_cmds):
        print("🎉 TODOS OS COMANDOS ESTÃO FUNCIONANDO!")
    else:
        print("⚠️  Alguns comandos precisam de ajuste.")

if __name__ == "__main__":
    test_commands()