⚡ R2 ASSISTANT - TACTICAL OS (v2.5) 
https://img.shields.io/badge/STATUS-OPERACIONAL-00ff00?style=for-the-badge&logo=probot
https://img.shields.io/badge/ARCH-HYBRID_CLOUD-00ffff?style=for-the-badge&logo=googlecolab
https://img.shields.io/badge/SECURITY-NEURAL_VAULT-ffff00?style=for-the-badge
https://img.shields.io/badge/INTEGRATION-TELEGRAM_BOT-26A5E4?style=for-the-badge&logo=telegram

"A inteligência não é apenas processamento, é prontidão."
R2 é um assistente tático de alto nível, operando em arquitetura híbrida entre Estação de Trabalho Local (PC) e Redundância em Nuvem (Google Colab + Render). Totalmente controlável via Telegram, Terminal e Voz.

📡 ÍNDICE
Arquitetura Híbrida

Capacidades Táticas

Implantação no Google Colab

Configuração de Ambiente

Comandos (Telegram / Terminal)

Estrutura de Arquivos

Contribuição e Testes Beta

Licença e Desenvolvedor

🛠️ ARQUITETURA HÍBRIDA (FAILOVER)
O R2 opera em dois nós simultâneos para garantir 100% de uptime e resiliência:

Nó	Localização	Função Principal
Local	Seu PC (Windows/Linux)	Interface Sci‑Fi completa (CustomTkinter), controle direto de hardware (webcam, volume, shutdown), processamento de baixa latência.
Nuvem	Google Colab + Render	Cérebro de reserva que assume automaticamente via Telegram quando o PC está offline. Processa comandos táticos e mantém o link neural ativo 24/7.
Failover Automático:

Se o PC for desligado, o bot Telegram continua ativo via Colab.

Ao religar o PC, o nó local reassume o controle e notifica a nuvem.

🛰️ CAPACIDADES TÁTICAS
📡 Monitoramento e Intel
Módulo	Descrição
Radar ADS-B	Varredura de tráfego aéreo em tempo real (OpenSky Network) com geração de mapa tático.
Frontline Intel	Relatórios atualizados de zonas de conflito (Ucrânia, Israel, Global) via LiveUAMap.
Space Weather	Telemetria solar completa (CME, SDO, Enlil, D‑RAP) da NOAA com vídeos e imagens.
Pizza Meter	Monitoramento indireto de atividade nuclear (DEFCON) baseado em pizzaint.watch.
GeoSísmico	Últimos terremotos significativos (M2.5+) via USGS.
Vulcões	Relatórios de atividade vulcânica do Smithsonian Institution.
Defesa Planetária	Dados de asteroides próximos da Terra (NASA NeoWs) + simulação de trajetória (GIF).
🌤️ Utilidades e Clima
Módulo	Descrição
Previsão de Precisão	Dados meteorológicos detalhados (OpenWeatherMap) com fluxo de diálogo inteligente.
Market Intel	Cotações em tempo real de USD, EUR, BTC (AwesomeAPI).
Orbital Track	Rastreamento da Estação Espacial Internacional (ISS) com mapa.
Rádio Scanner	Interceptação de estações de rádio online (Radio‑Browser).
🛡️ Segurança e Sistema
Módulo	Descrição
Neural Vault	Cofre criptografado (Fernet + PBKDF2) para armazenamento de dados sensíveis com chave mestra.
Sentinela	Captura de imagens de segurança via webcam (OpenCV) com alerta remoto.
System Monitor	Diagnóstico completo de CPU, RAM, disco, rede e integridade dos módulos.
Speedtest	Teste de velocidade de internet (via speedtest‑cli).
Network Scanner	Varredura ARP de dispositivos na rede local.
Controle de Volume	Ajuste de áudio do sistema via pyautogui.
🚀 IMPLANTAÇÃO NO GOOGLE COLAB
O nó de nuvem é executado no Google Colab (gratuito com GPU opcional). Siga os passos abaixo para colocar o R2 no ar em menos de 5 minutos.

1. Abrir o Colab e montar o ambiente
python
# Conecte-se a uma GPU (Runtime → Change runtime type → T4 GPU)
import os
from google.colab import drive
drive.mount('/content/drive')
2. Clonar o repositório
python
%cd /content
!rm -rf R2
!git clone https://github.com/Tedyzetaa/R2.git
%cd R2
3. Instalar dependências de sistema e Python
python
# Instala dependências de sistema para o Playwright
!apt-get update && apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 libasound2 libatk1.0-0 libcups2 libxcomposite1 libxdamage1 libxrandr2 libpango-1.0-0 libcairo2

# Instala pacotes Python principais
!pip install -q python-telegram-bot huggingface_hub geopy matplotlib requests beautifulsoup4 feedparser cloudscraper playwright ping3 psutil speedtest-cli opencv-python pyautogui cryptography colorama
!pip install -q llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# Instala navegadores do Playwright
import os
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/content/playwright-browsers'
!playwright install chromium
4. Configurar o token do Telegram
Você pode definir o token de duas formas:

Opção A – Variável de ambiente (recomendado):

python
import os
os.environ['TELEGRAM_TOKEN'] = 'SEU_TOKEN_AQUI'
Opção B – Passar como argumento ao executar o script (menos seguro):

python
!python collab.py SEU_TOKEN_AQUI
5. Executar o bot
python
!python collab.py
O bot iniciará, baixará o modelo Llama-3 (se necessário) e ficará aguardando comandos.

6. Manter o Colab ativo
Para evitar desconexão, você pode usar uma extensão de navegador ou um script simples que clique periodicamente. O bot continuará funcionando enquanto a sessão do Colab estiver ativa.

🔧 CONFIGURAÇÃO DE AMBIENTE
Variáveis de ambiente (arquivo .env)
Crie um arquivo .env na raiz do projeto com as seguintes chaves:

env
# Obrigatórios
TELEGRAM_TOKEN=seu_token_aqui

# Opcionais (para funcionalidades extras)
OPENWEATHER_KEY=sua_chave_openweather
NASA_API_KEY=DEMO_KEY   # ou sua chave da NASA
Chaves de API (em caso de rate limit)
Serviço	Onde obter	Uso
OpenWeatherMap	https://openweathermap.org/api	Previsão do tempo
NASA NeoWs	https://api.nasa.gov/ (DEMO_KEY funciona)	Dados de asteroides
OpenSky Network	Gratuito, sem chave	Radar ADS‑B
NOAA	Público	Clima espacial
Modelo Llama‑3 (GGUF)
O script baixa automaticamente do Hugging Face:

python
model_path = hf_hub_download(
    repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF",
    filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf",
    local_dir="/content/models"
)
Caso prefira um modelo menor, altere o nome do arquivo no código.

⌨️ COMANDOS (TELEGRAM / TERMINAL)
Todos os comandos abaixo podem ser enviados diretamente ao bot no Telegram ou digitados no terminal do Colab.

Menu principal (botões interativos)
Envie /start para abrir o menu tátil com botões para todas as funcionalidades.

Comandos de texto
Comando	Descrição
/help ou ajuda	Exibe este manual
/status	Mostra CPU, RAM e status da rede
clima [cidade]	Previsão do tempo. Se omitir a cidade, o bot pergunta.
radar [cidade]	Varredura ADS‑B (aviação). Se omitir, pergunta a cidade.
voos [cidade]	Radar via API OpenSky (mais preciso, gera imagem).
intel [setor]	Mapa de guerra (setores: ucrania, israel, global).
solar	Relatório completo NOAA (CME, SDO, Enlil, D‑RAP) com vídeos.
defcon	Nível de alerta nuclear (Pizza Meter) + screenshot.
terremotos	Últimos 5 terremotos significativos.
vulcao	Relatório de atividade vulcânica (Smithsonian).
asteroides	Defesa planetária: dados e simulação de trajetória.
sentinela	Captura foto da webcam (apenas no nó local).
speedtest	Testa velocidade da internet.
scan [país]	Lista rádios online do país.
cotação	Cotações USD, EUR, BTC.
iss	Posição atual da ISS e mapa.
📁 ESTRUTURA DE ARQUIVOS
text
R2/
├── collab.py                  # Script principal para Colab
├── r2_server.py               # Versão headless para PC (sem GUI)
├── force_sci_fi_gui.py        # Versão com interface gráfica (PC)
├── features/                  # Módulos táticos
│   ├── air_traffic.py         # Radar ADS‑B
│   ├── astro_defense.py       # Defesa planetária
│   ├── astro_timelapse.py     # GIF de trajetória
│   ├── ear_system.py          # Reconhecimento de voz
│   ├── geo_seismic.py         # Terremotos
│   ├── intel_war.py           # Mapas de guerra
│   ├── local_brain.py         # Llama‑3 local
│   ├── market_system.py       # Cotações
│   ├── net_speed.py           # Speedtest
│   ├── network_scanner.py     # Scanner ARP
│   ├── news_briefing.py       # Notícias (fallback)
│   ├── noaa/                  # Clima espacial (CME, SDO, etc.)
│   ├── orbital_system.py      # ISS
│   ├── orbital_trajectory.py  # Trajetória de asteroides
│   ├── quantum_module.py      # Trade (externo)
│   ├── radar_api.py           # Radar OpenSky (API)
│   ├── radio_scanner.py       # Rádios online
│   ├── sentinel_system.py     # Webcam
│   ├── system_monitor.py      # Diagnóstico
│   ├── system_scanner.py      # Scanner de hardware
│   ├── telegram_uplink.py     # Interface com Telegram
│   ├── vault.py               # Cofre criptografado
│   ├── volcano_monitor.py     # Vulcões
│   └── weather_system.py      # Clima OpenWeather
├── voz.py                     # Síntese de voz (opcional)
├── animations_system.py       # Animações para GUI
├── models/                    # Modelos GGUF (baixados)
├── data/                       # Dados persistentes (vault, cache)
├── .env.example                # Exemplo de variáveis de ambiente
└── README.md                   # Este arquivo
🧬 CONTRIBUIÇÃO E TESTES BETA
Estamos selecionando operadores avançados para testar a estabilidade do link neural e propor novas funcionalidades.

Como participar:

Fork o repositório.

Implemente melhorias ou correções.

Envie um Pull Request com descrição detalhada.

Ou entre em contato direto com o desenvolvedor.

📄 LICENÇA E DESENVOLVEDOR
Operador Principal: Tedyzetaa
Tecnologias: Python | FastAPI | CustomTkinter | Telegram Bot API | Playwright | Llama‑Cpp

Este projeto é distribuído sob a licença MIT. Sinta-se livre para usar, modificar e compartilhar, mantendo os créditos.

⭐ Se o R2 foi útil para você, deixe uma estrela no repositório!
📡 “Prontidão é tudo.”
