import os

class ImageGenerator:
    def __init__(self, bot_instance):
        self.bot = bot_instance

    def gerar_personagem_consistente(self, descricao):
        """
        Gera um personagem realista focado em consistência.
        Dica: Use sempre os mesmos traços físicos no prompt.
        """
        prompt_final = f"Fotografia ultra-realista, 8k, iluminação cinematográfica, detalhes de pele, focado em: {descricao}"
        # O sistema utilizará a ferramenta Nano Banana 2 internamente
        return prompt_final

    def transformar_com_referencia(self, prompt, imagem_referencia):
        """
        Usa uma imagem como base para manter fisionomia e aplicar novos estilos/cenários.
        """
        return prompt, imagem_referencia
