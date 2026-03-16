import torch
import os
from diffusers import StableDiffusionPipeline

class ImageGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Caminhos sincronizados com o r2_web_core.py
        self.model_path = "models/checkpoints/v1-5-pruned.safetensors"
        self.lora_dir = "models/loras"
        self.pipe = None

    def load_engine(self):
        print("🎨 [IMAGE]: Carregando motor SD 1.5...")
        self.pipe = StableDiffusionPipeline.from_single_file(
            self.model_path, 
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)

        # Injeta as 3 LoRAs baixadas
        loras = ["detailed_perfection.safetensors", "realistic_skin.safetensors", "amateur_photography.safetensors"]
        for lora in loras:
            path = os.path.join(self.lora_dir, lora)
            if os.path.exists(path):
                self.pipe.load_lora_weights(path, adapter_name=lora.split('.')[0])
                print(f"✨ [IMAGE]: LoRA {lora} acoplada.")

    def generate(self, prompt):
        if not self.pipe: self.load_engine()
        # Adiciona gatilhos automáticos para as LoRAs no prompt
        full_prompt = f"{prompt}, highly detailed, realistic skin, amateur photography style, masterpiece"
        image = self.pipe(full_prompt, num_inference_steps=30).images[0]
        return image