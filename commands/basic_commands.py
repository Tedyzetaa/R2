import logging

def register_basic_commands(command_system, falar, ouvir_comando):
    """Registra comandos básicos do sistema."""
    logger = logging.getLogger(__name__)

    def mostrar_ajuda(falar_func=None, ouvir_func=None):
        """Mostra todos os comandos disponíveis."""
        command_system.list_commands(falar_func)

    def sobre_assistente(falar_func=None, ouvir_func=None):
        """Informações sobre o assistente."""
        falar_func("Eu sou o R2, seu assistente pessoal. Desenvolvido para ajudar com tarefas do dia a dia, pesquisas e muito mais!")

    def limpar_conversa(falar_func=None, ouvir_func=None):
        """Limpa a conversa (será implementado na GUI)."""
        falar_func("Função de limpar conversa será implementada na interface.")

    # Registra os comandos básicos
    command_system.register_command("ajuda", mostrar_ajuda, "Mostra todos os comandos disponíveis")
    command_system.register_command("help", mostrar_ajuda, "Mostra todos os comandos disponíveis")
    command_system.register_command("sobre", sobre_assistente, "Informações sobre o assistente")
    command_system.register_command("limpar", limpar_conversa, "Limpa a conversa")