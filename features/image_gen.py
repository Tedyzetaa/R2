import torch
import os
from diffusers import StableDiffusionPipeline

class ImageGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_id = "SG161222/Realistic_Vision_V5.1_noVAE"
        self.pipe = None

    def load_engine(self):
        print("🎨 [IMAGE]: Carregando motor SD 1.5 (Realistic Vision V5.1 Oficial)...")
        self.pipe = StableDiffusionPipeline.from_pretrained(
            self.model_id, 
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        )
        self.pipe.safety_checker = None
        
        if self.device == "cuda":
            self.pipe.enable_model_cpu_offload()

        print("✨ [IMAGE]: Motor carregado com sucesso.")

    def generate(self, prompt):
        if not self.pipe: 
            self.load_engine()
            
        # 1. ORDEM CORRIGIDA: Tags de hiper-realismo vêm PRIMEIRO para nunca serem cortadas
        full_prompt = f"RAW photo, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT4, {prompt}"
        
        # 2. O SEGREDO DO REALISMO: Prompt Negativo
        neg_prompt = (
            "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), "
            "text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, "
            "morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, "
            "blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions"
        )
        
        print(f"🎨 [IMAGE]: Renderizando em Alta Definição (30 passos)... Aguarde.")
        
        # Aumentamos para 30 passos para dar tempo da IA refinar a pele e texturas
        image = self.pipe(
            prompt=full_prompt, 
            negative_prompt=neg_prompt,
            num_inference_steps=30,
            guidance_scale=7.5
        ).images[0]
        
        return image