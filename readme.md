🤖 R2 Assistant - Assistente Pessoal em Python
Um assistente virtual estilo Jarvis desenvolvido em Python com interface gráfica, reconhecimento de voz offline, sintetização de fala personalizável e sistema completo de trading automático.

https://img.shields.io/badge/Python-3.10+-blue.svg
https://img.shields.io/badge/License-MIT-green.svg
https://img.shields.io/badge/Version-1.2-red.svg
https://img.shields.io/badge/Trading-Autom%25C3%25A1tico-green.svg
https://img.shields.io/badge/Voz-Offline%252FOnline-blue.svg

🆕 VERSÃO 1.2 - SISTEMA DE VOZ OFFLINE E PERSONALIZÁVEL
🎯 Novas Funcionalidades Principais
🎤 Reconhecimento de Voz Offline com Vosk

🗣️ Síntese de Voz Personalizável com pyttsx3

🔊 Controle Avançado de Voz - velocidade, volume, tom

🎭 Múltiplas Vozes do sistema suportadas

🔄 Sistema Híbrido - offline com fallback para online

⚡ Processamento em Tempo Real com filas otimizadas

📋 HISTÓRICO DE ATUALIZAÇÕES - v1.1 → v1.2
v1.20 - Sistema de Reconhecimento de Voz Offline
✅ Integração Vosk - Reconhecimento offline em português

✅ Modelo PT-BR - Modelo pequeno (vosk-model-small-pt-0.3)

✅ Captura de Áudio - PyAudio com buffer otimizado

✅ Processamento Contínuo - Loop de escuta em tempo real

✅ Tratamento de Exceções - Robustez na captura de áudio

v1.21 - Síntese de Voz Personalizável
✅ Motor Duplo TTS - pyttsx3 (offline) + gTTS (online)

✅ Configurações de Voz - Velocidade, volume, tom ajustáveis

✅ Múltiplas Vozes - Suporte a todas as vozes do sistema

✅ Sistema de Filas - Processamento sequencial sem sobreposição

✅ Controle de Eco - Pausa escuta durante fala automaticamente

v1.22 - Comandos de Voz para Personalização
✅ "configurar voz" - Ajusta velocidade, volume e tom

✅ "alterar voz" - Muda para voz específica do sistema

✅ "voze disponíveis" - Lista todas as vozes

✅ "modo voz offline/online" - Alterna entre motores TTS

✅ "testar voz" - Demonstração da voz atual

v1.23 - Otimizações de Performance
✅ Thread Seguras - Processamento não-bloqueante

✅ Gerenciamento de Recursos - Cleanup automático

✅ Fallback Inteligente - Online se offline falhar

✅ Tratamento Windows - Correções para SAPI5

✅ Logs Detalhados - Diagnóstico completo do sistema

v1.24 - Interface de Controle de Voz
✅ Status de Voz - Indicadores visuais na GUI

✅ Controles de Voz - Botões para gerenciar escuta/fala

✅ Configurações Integradas - Painel de ajustes de voz

✅ Feedback Visual - Confirmação de comandos reconhecidos

🎤 Sistema de Voz da Versão 1.2
🎯 Recursos de Reconhecimento (Vosk)
python
# Configuração Vosk
MODEL_PATH = "./model/vosk-model-small-pt-0.3"
SAMPLE_RATE = 16000      # Taxa de amostragem
CHUNK_SIZE = 4096        # Buffer de áudio
CHANNELS = 1             # Mono
🗣️ Recursos de Síntese (TTS)
python
# Configurações de Voz Personalizáveis
VOICE_TYPE = "offline"   # 'online' (gTTS) ou 'offline' (pyttsx3)
VOICE_RATE = 150         # Velocidade (50-300)
VOICE_VOLUME = 0.8       # Volume (0.0-1.0) 
VOICE_PITCH = 110        # Tom (50-200) - exceto Windows
🎙️ Comandos de Voz - CONTROLE DE VOZ
bash
# Personalização de Voz
"R2, configurar voz"              # Menu de configurações
"R2, alterar voz"                 # Lista e seleciona vozes
"R2, voze disponíveis"            # Mostra vozes do sistema
"R2, modo voz offline"            # Ativa TTS local
"R2, modo voz online"             # Ativa TTS em nuvem
"R2, testar voz"                  # Testa configuração atual

# Ajustes em Tempo Real
"mais rápido" / "mais devagar"    # Velocidade da voz
"aumentar volume" / "diminuir volume"  # Volume
"tom mais alto" / "tom mais baixo"     # Tom (exceto Windows)
🎯 Funcionalidades da Versão 1.2
🎤 Comandos por Voz - SISTEMA E VOZ
bash
# Sistema Básico
"R2, olá"                         # Cumprimenta o usuário
"R2, hora"                        # Diz a hora atual  
"R2, data"                        # Diz a data atual
"R2, tirar print"                 # Captura tela
"R2, preencher documento"         # Digita texto por voz

# Controle de Sistema
"R2, mutar áudio"                 # Muta sistema
"R2, desmutar áudio"              # Desmuta sistema
"R2, aumentar volume"             # Aumenta volume do sistema
"R2, diminuir volume"             # Diminui volume do sistema

# Abertura de Programas
"R2, abrir chrome"                # Navegador
"R2, abrir vscode"                # Editor de código
"R2, abrir explorer"              # Explorador de arquivos
"R2, abrir terminal"              # Terminal/CMD
"R2, abrir spotify"               # Música
"R2, abrir discord"               # Comunicação
🌐 Comandos por Voz - WEB E CRIPTO
bash
# Pesquisas e Web
"R2, pesquisar [termo]"           # Google search
"R2, notícias"                    # Notícias principais
"R2, previsão do tempo"           # Clima para cidade

# Criptomoedas
"R2, cotação bitcoin"             # Preço do Bitcoin
"R2, cotação ethereum"            # Preço do Ethereum
"R2, cotação nano"                # Preço da Nano
"R2, cotação doge"                # Preço do Dogecoin
📈 Comandos por Voz - TRADING (mantidos da v1.1)
bash
# Trading Automático
"R2, trading sma nano"            # Inicia SMA para Nano
"R2, trading rsi doge"            # Inicia RSI para Dogecoin
"R2, status trading"              # Status de todos os pares
"R2, parar trading"               # Para todo o trading

# Informações
"R2, saldo"                       # Mostra saldos principais
"R2, listar pares"                # Pares disponíveis
🚀 Instalação Rápida
1. Clone e Configure
bash
git clone https://github.com/seu-usuario/r2-assistant.git
cd r2-assistant
conda env create -f environment.yml
conda activate r2_assistant
2. Instale Dependências de Voz
bash
# Instalação automática
python install_requirements.py

# Ou manualmente
pip install vosk pyaudio pyttsx3 speechrecognition gtts pygame
3. Baixe Modelo de Voz Offline
bash
# O script install_requirements.py baixa automaticamente
# Ou manualmente: baixe e extraia em:
# ./model/vosk-model-small-pt-0.3/
# Disponível em: https://alphacephei.com/vosk/models
4. Configure as APIs
bash
# Edite o arquivo .env
BINANCE_API_KEY=sua_chave_da_mainnet
BINANCE_SECRET_KEY=seu_secret_da_mainnet
TESTNET=False  # Para dinheiro real

# Configurações de Voz (opcional)
VOICE_TYPE=offline  # offline ou online
5. Execute o R2 Assistant
bash
python main.py
🏗️ Arquitetura do Sistema de Voz
text
core/
├── voice_engine.py           # Motor Vosk - reconhecimento offline
├── audio_processor.py        # Processador TTS - síntese de voz  
└── command_system.py         # Sistema de comandos

config/
├── settings.py              # Configurações de voz
└── vosk_config.py           # Configurações Vosk

model/
└── vosk-model-small-pt-0.3/ # Modelo de reconhecimento PT-BR
🎮 Controles de Voz na Interface
🎯 GUI Principal
🎤 Iniciar/Parar Escuta - Botão para controle de voz

🟢/🔴 Indicador - Status visual da escuta

🗣️ Falar Agora - Síntese de texto digitado

💬 Conversa - Histórico de comandos e respostas

⚙️ Painel de Configuração de Voz
python
# Acessível via comandos de voz ou GUI
Configurações de Voz:
├── Tipo: Offline (pyttsx3) / Online (gTTS)
├── Velocidade: 150 (50-300)
├── Volume: 0.8 (0.0-1.0)
├── Tom: 110 (50-200) - exceto Windows
└── Voz Atual: Microsoft Maria - Portuguese
🔧 Configuração de Voz
🎯 Parâmetros Ajustáveis
python
# Em config/settings.py
VOICE_TYPE = "offline"    # 'online' ou 'offline'
VOICE_RATE = 150          # Velocidade da fala
VOICE_VOLUME = 0.8        # Volume da voz
VOICE_PITCH = 110         # Tom (não suportado no Windows)

# Detecção automática do Windows
if os.name == 'nt':
    VOICE_TYPE = "online"  # Recomendado para Windows
🗣️ Vozes por Sistema Operacional
Windows:
Microsoft Maria - Português Brasil

Microsoft Zira - Inglês EUA

Microsoft David - Inglês EUA (masculina)

Linux:
eSpeak - Voz robótica

Festival - Mais natural

Instale: sudo apt-get install espeak festival

macOS:
Alex - Padrão

Victoria - Feminina

Joana - Português

🐛 Solução de Problemas - Voz
❌ Erro: "Modelo Vosk não encontrado"
Solução:

bash
# Execute o script de instalação
python install_requirements.py

# Ou baixe manualmente:
# 1. Acesse: https://alphacephei.com/vosk/models
# 2. Baixe: vosk-model-small-pt-0.3.zip
# 3. Extraia em: ./model/vosk-model-small-pt-0.3/
❌ Erro: "Pitch adjustment not supported" (Windows)
Solução:

python
# No config/settings.py
VOICE_TYPE = "online"  # Use gTTS no Windows

# Ou desative o pitch:
VOICE_PITCH = 100      # Será ignorado no Windows
❌ Erro: "No module named 'vosk'"
Solução:

bash
pip install vosk

# No Windows, pode precisar de:
pip install pipwin
pipwin install pyaudio
❌ Problema: Comandos não são detectados
Solução:

Verifique se o microfone está funcionando

Fale claramente e próximo ao microfone

Ajuste o ganho do microfone no sistema

Teste em ambiente silencioso

❌ Problema: Voz não funciona
Solução:

Verifique se as caixas de som estão ligadas

Teste o volume do sistema

No Windows, use VOICE_TYPE = "online"

Verifique permissões de áudio

🔮 Próximas Atualizações Planejadas
🚀 v1.3 - Backtesting e Otimização
Sistema de backtesting com dados históricos

Otimização de parâmetros de estratégias

Relatórios de performance detalhados

🎯 v1.4 - Estratégias Avançadas
Machine Learning para previsão de preços

Grid Trading e DCA (Dollar Cost Averaging)

Arbitragem entre exchanges

🔒 v1.5 - Segurança Avançada
Stop-loss e take-profit automáticos

Gestão de risco integrada

Alertas de mercado em tempo real

🗣️ v1.6 - Voz Avançada
Comandos contextuais e conversacionais

Aprendizado de preferências de voz

Suporte a múltiplos idiomas simultâneos

Sintetização de voz neural (Azure, Google Wavenet)

📊 Estrutura do Projeto Completa
text
r2-assistant/
├── core/
│   ├── voice_engine.py          # Motor Vosk - reconhecimento
│   ├── audio_processor.py       # TTS - síntese de voz
│   ├── command_system.py        # Sistema de comandos
│   └── vosk_engine.py           # Motor Vosk alternativo
├── commands/
│   ├── system_commands.py       # Comandos de sistema e voz
│   ├── web_commands.py          # Comandos web
│   ├── basic_commands.py        # Comandos básicos
│   └── crypto_commands.py       # Comandos trading
├── trading/                     # Sistema de trading (v1.1)
├── gui/                         # Interface gráfica
├── config/
│   ├── settings.py              # Configurações principais
│   └── vosk_config.py           # Configurações Vosk
├── model/
│   └── vosk-model-small-pt-0.3/ # Modelo de voz PT-BR
├── utils/
└── main.py                      # Arquivo principal
📞 Suporte e Comunidade
📧 Email: suporte@r2assistant.com

💬 Discord: [Link do servidor]

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

⚠️ AVISO LEGAL: Trading de criptomoedas envolve riscos significativos. O R2 Assistant é uma ferramenta educacional e não constitui aconselhamento financeiro.

🔊 AVISO DE PRIVACIDADE: O modo de voz offline processa áudio localmente. No modo online, áudio é processado pelos serviços de nuvem respectivos.