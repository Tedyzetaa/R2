# 🤖 R2 Assistant - Assistente Pessoal em Python

Um assistente virtual estilo Jarvis desenvolvido em Python com interface gráfica, reconhecimento de voz e sintetização de fala.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 Funcionalidades

### 🎤 Comandos por Voz
- Reconhecimento de voz em tempo real
- Escuta contínua sem travamentos
- Sistema anti-eco (não reconhece a própria voz)

### 💬 Comandos por Texto
- Interface gráfica intuitiva
- Histórico de conversa
- Botões de ação rápida

### 🔧 Comandos Implementados
- **Sistema**: `olá`, `hora`, `data`, `tirar print`, `abrir chrome`, `abrir vscode`
- **Web**: `pesquisar`, `notícias`, `previsão do tempo`, `bitcoin`, `ethereum`
- **Utilidades**: `mutar áudio`, `desmutar áudio`, `preencher documento`
- **Ajuda**: `ajuda`, `sobre`, `limpar`

### 🎵 Sistema de Áudio
- Síntese de voz com gTTS
- Suporte a ffplay (recomendado) e pygame
- Controle de volume automático

## 🚀 Instalação Rápida

### Pré-requisitos
- Python 3.10+
- Miniconda/Anaconda (recomendado)
- Microfone
- Alto-falantes

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/r2-assistant.git
cd r2-assistant
2. Configure o ambiente Conda
bash
# Crie o ambiente
conda env create -f environment.yml

# Ative o ambiente
conda activate r2_assistant
3. Instalação alternativa com pip
bash
pip install -r requirements.txt
4. Configure as APIs (opcional)
bash
# Copie o arquivo de configuração
copy .env.example .env

# Edite o .env com suas chaves API
# NEWS_API_KEY=sua_chave_aqui
# WEATHER_API_KEY=sua_chave_aqui
5. Execute o R2
bash
python main.py
📁 Estrutura do Projeto
text
r2-assistant/
├── core/                 # Núcleo do sistema
│   ├── voice_engine.py   # Motor de reconhecimento de voz
│   ├── audio_processor.py # Sistema de síntese de fala
│   └── command_system.py  # Gerenciador de comandos
├── commands/             # Comandos do assistente
│   ├── system_commands.py # Comandos do sistema
│   ├── web_commands.py   # Comandos web
│   ├── crypto_commands.py # Comandos de criptomoedas
│   └── basic_commands.py  # Comandos básicos
├── gui/                  # Interface gráfica
│   └── assistant_gui.py  # Interface Tkinter
├── config/               # Configurações
│   └── settings.py       # Configurações do sistema
├── utils/                # Utilitários
│   └── helpers.py        # Funções auxiliares
├── tests/                # Testes
├── main.py               # Arquivo principal
├── requirements.txt      # Dependências Python
└── environment.yml       # Ambiente Conda
🛠️ Desenvolvimento
Testando componentes individuais
bash
# Teste o reconhecimento de voz
python test_voice.py

# Teste os comandos
python test_commands.py

# Teste a escuta contínua
python test_continuous_listening.py

# Teste o sistema de áudio
python test_audio.py
Adicionando novos comandos
Crie uma função em um dos arquivos em commands/

Registre o comando no sistema:

python
def meu_comando(falar_func=None, ouvir_func=None):
    falar_func("Executando meu comando!")

command_system.register_command("meu comando", meu_comando, "Descrição do comando")
Configuração de APIs
Edite o arquivo .env:

ini
NEWS_API_KEY=sua_chave_newsapi
WEATHER_API_KEY=sua_chave_openweather
BINANCE_API_KEY=sua_chave_binance
BINANCE_SECRET_KEY=seu_secret_binance
🎨 Personalização
Modificando a interface
Edite gui/assistant_gui.py para alterar cores, layout ou adicionar novos elementos.

Adicionando novos comandos
Crie novos arquivos em commands/ seguindo o padrão existente.

Alterando a voz
Modifique o idioma em config/settings.py:

python
LANGUAGE = "en"  # Para inglês
🔧 Solução de Problemas
Problema: Travamento ao clicar em "Ouvir"
Solução: Verifique se o microfone está funcionando e se as permissões estão concedidas.

Problema: Áudio não funciona
Solução:

bash
# Instale o ffmpeg
conda install ffmpeg -c conda-forge

# Ou use pygame como fallback
pip install pygame
Problema: Comandos não são reconhecidos
Solução: Execute python test_commands.py para verificar se os comandos estão registrados.

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

🤝 Contribuindo
Fork o projeto

Crie uma branch para sua feature (git checkout -b feature/AmazingFeature)

Commit suas mudanças (git commit -m 'Add some AmazingFeature')

Push para a branch (git push origin feature/AmazingFeature)

Abra um Pull Request

📞 Suporte
Se encontrar problemas, abra uma issue no GitHub ou entre em contato.