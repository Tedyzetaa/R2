# Modelos do R2 Assistant

Este diretório armazena modelos de machine learning, IA e processamento de dados utilizados pelo R2 Assistant.

## Estrutura Recomendada
models/
├── audio/ # Modelos de áudio (STT, TTS)
│ ├── whisper/ # Modelos Whisper para transcrição
│ ├── tts/ # Modelos de síntese de voz
│ └── vad/ # Voice Activity Detection
├── vision/ # Modelos de visão computacional
│ ├── object_detection/
│ ├── face_recognition/
│ └── image_generation/
├── nlp/ # Modelos de Processamento de Linguagem Natural
│ ├── embeddings/ # Modelos de embeddings
│ ├── classifiers/ # Classificadores de texto
│ └── generators/ # Modelos generativos (GPT-like)
├── trading/ # Modelos de trading quantitativo
│ ├── predictors/ # Modelos preditivos
│ ├── rl/ # Reinforcement Learning
│ └── anomaly/ # Detecção de anomalias
├── cache/ # Cache de modelos baixados
│ └── huggingface/ # Modelos do Hugging Face
└── configs/ # Configurações de modelos
├── model_configs.json
└── download_list.json

text

## Modelos Suportados

### 1. **Audio Processing**
- **Whisper** (OpenAI): Transcrição de áudio multilíngue
- **Coqui TTS**: Síntese de voz natural
- **Silero VAD**: Detecção de atividade vocal

### 2. **Computer Vision**
- **YOLOv8**: Detecção de objetos em tempo real
- **CLIP**: Classificação de imagens zero-shot
- **Stable Diffusion**: Geração de imagens

### 3. **Natural Language Processing**
- **Sentence Transformers**: Embeddings de texto
- **BERT/BART**: Classificação e geração
- **LLaMA/GPT**: Modelos de linguagem grandes

### 4. **Trading & Finance**
- **Prophet**: Previsão de séries temporais
- **LSTM/GRU**: Redes neurais recorrentes
- **Random Forest**: Modelos ensemble

## Download Automático

O R2 Assistant inclui um sistema de download automático de modelos. Para configurar:

1. **Lista de downloads**: Edite `configs/download_list.json`
2. **Cache**: Os modelos são armazenados em `cache/`
3. **Verificação**: Checksums são verificados automaticamente

### Exemplo de download_list.json:
```json
{
  "models": [
    {
      "name": "whisper-tiny",
      "type": "audio/stt",
      "source": "huggingface",
      "repo": "openai/whisper-tiny",
      "files": ["model.safetensors", "config.json"],
      "size_mb": 151,
      "checksum": "sha256:abc123..."
    },
    {
      "name": "yolov8n",
      "type": "vision/detection",
      "source": "ultralytics",
      "url": "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt",
      "size_mb": 6.2
    }
  ]
}
Gerenciamento de Modelos
Comandos Disponíveis:
bash
# Listar modelos instalados
r2> models list

# Baixar modelo específico
r2> models download whisper-base

# Verificar integridade
r2> models verify

# Limpar cache de modelos
r2> models cleanup

# Informações de uso
r2> models info
API Python:
python
from r2.models.manager import ModelManager

# Inicializar gerenciador
manager = ModelManager()

# Baixar modelo
manager.download_model("whisper-base")

# Carregar modelo
model = manager.load_model("whisper-base", device="cuda")

# Liberar memória
manager.unload_model("whisper-base")
Otimização de Performance
1. Quantização
python
# Quantização INT8 para inferência mais rápida
from utils.model_optimizer import quantize_model
quantized_model = quantize_model(model, dtype="int8")
2. GPU Acceleration
python
# Usar GPU se disponível
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
3. Batch Processing
python
# Processamento em batch para eficiência
batch_size = 32
results = model.process_batch(batch_data, batch_size=batch_size)
Armazenamento
Formatos Suportados:
PyTorch: .pt, .pth

TensorFlow: .h5, .pb

ONNX: .onnx

SafeTensors: .safetensors

GGML: .gguf, .ggml

Compressão:
bash
# Compactar modelo para economizar espaço
gzip model.pt

# O R2 Assistant descompacta automaticamente
Backup e Versionamento
Sistema de Versionamento:
bash
# Criar checkpoint do modelo
r2> models checkpoint whisper-v1

# Listar versões
r2> models versions

# Restaurar versão
r2> models restore whisper-v1
Backup Automático:
Os modelos são automaticamente copiados para:

backups/models/ - Backup local

Configuração opcional para nuvem

Segurança
Verificação de Integridade:
python
# Verificar checksum
from utils.security import verify_model_integrity
is_valid = verify_model_integrity("model.pt", expected_checksum)
Sandbox para Modelos:
python
# Executar modelo em sandbox
from utils.security import ModelSandbox

with ModelSandbox() as sandbox:
    result = sandbox.run_model(model, input_data)
Monitoramento
Métricas Coletadas:
Uso de memória

Tempo de inferência

Taxa de acerto

Utilização de GPU

Logs:
bash
logs/models/
├── download.log      # Logs de download
├── inference.log     # Logs de inferência
└── performance.log   # Métricas de performance
Troubleshooting
Problemas Comuns:
Falta de memória

bash
# Reduzir batch size
export BATCH_SIZE=8

# Usar CPU
export USE_GPU=false
Download lento

bash
# Usar mirror
export HF_MIRROR=https://mirror.example.com
Modelo corrompido

bash
# Forçar redownload
r2> models redownload <model_name>
Suporte:
Consulte r2> help models

Reporte issues no GitHub

Verifique logs em logs/models/

Nota: Sempre verifique os requisitos de licença antes de usar modelos de terceiros. Alguns modelos podem ter restrições de uso comercial.

text

## 5. **data/models/.gitkeep**
*(Arquivo vazio para manter o diretório no git)*

## Resumo da estrutura criada:

### **data/modules.json**:
✅ Sistema completo de módulos carregáveis
✅ 10 módulos com diferentes categorias
✅ Configurações detalhadas por módulo
✅ Atalhos de teclado configuráveis
✅ Estatísticas do sistema
✅ Configurações de API e performance

### **data/cache/**:
✅ Sistema de cache organizado por categorias
✅ `CacheManager` para operações de cache
✅ `CacheInitializer` para setup automático
✅ Índice e estatísticas de cache
✅ Suporte a JSON e pickle
✅ Limpeza automática e manual

### **data/models/README.md**:
✅ Documentação completa para modelos de ML/IA
✅ Estrutura recomendada de diretórios
✅ Instruções de download e gerenciamento
✅ Otimização de performance
✅ Segurança e verificação
✅ Troubleshooting e suporte

Esta estrutura fornece uma base sólida para:

1. **Gerenciamento de módulos**: Sistema extensível e configurável
2. **Cache eficiente**: Performance melhorada com cache inteligente
3. **Modelos de IA**: Documentação completa para integração de ML/IA

A estrutura segue as melhores práticas de organização de dados e está pronta para escalar conforme o sistema cresce.