import torch
from diffusers import StableDiffusionPipeline

class ImageGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = "models/checkpoints/v1-5-pruned.safetensors"
        self.lora_path = "models/loras/detailed_perfection.safetensors"
        self.pipe = None

    def load_engine(self):
        """Carrega o modelo base e injeta o LoRA de perfeição"""
        print("🎨 [IMAGE]: Carregando motor de renderização...")
        
        # Carrega o Pipeline
        self.pipe = StableDiffusionPipeline.from_single_file(
            self.model_path, 
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)

        # Injeta o LoRA (Detailed Perfection)
        # Nota: Requer a biblioteca 'peft' instalada
        try:
            self.pipe.load_lora_weights(self.lora_path, adapter_name="perfection")
            print("✨ [IMAGE]: LoRA 'Detailed Perfection' acoplado com sucesso.")
        except Exception as e:
            print(f"⚠️ [IMAGE]: Erro ao carregar LoRA: {e}")

    def generate(self, prompt):
        if not self.pipe: self.load_engine()
        
        # O modelo que você escolheu funciona melhor com certos gatilhos no prompt
        enhanced_prompt = f"{prompt}, highly detailed, masterpiece, perfection style"
        
        image = self.pipe(enhanced_prompt, num_inference_steps=30).images[0]
        path = "output_gen.png"
        image.save(path)
        return path
