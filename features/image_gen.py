import torch
from diffusers import StableDiffusionPipeline
import sys
import os

# Define a localização para salvar as imagens
IMAGE_OUTPUT_DIR = "assets/images"
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

def gerar_imagem(prompt):
    print(f"--- Gerando imagem para o prompt: '{prompt}' ---")
    
    # Carrega o modelo. Usaremos o SD v1.5 para maior velocidade/compatibilidade.
    # Você pode mudar para modelos mais pesados/modernos (como SDXL) se tiver hardware.
    model_id = "runwayml/stable-diffusion-v1-5"
    
    # Configura para rodar na GPU (CUDA) se disponível, senão na CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id, 
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    pipe = pipe.to(device)

    # Gera a imagem
    image = pipe(prompt).images[0]

    # Salva a imagem
    filename = f"{IMAGE_OUTPUT_DIR}/{prompt.replace(' ', '_')}.png"
    image.save(filename)
    
    return filename

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Pega o prompt via argumento de linha de comando
        prompt = " ".join(sys.argv[1:])
        generated_image_path = gerar_imagem(prompt)
        print(f"IMAGEM_GERADA: {generated_image_path}")
    else:
        print("Uso: python features/image_gen.py SEU PROMPT AQUI")