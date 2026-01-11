# ⚡ R2 ASSISTANT - TACTICAL OS (v2.1)

![Status](https://img.shields.io/badge/STATUS-OPERACIONAL-00ff00?style=for-the-badge&logo=probot)
![Platform](https://img.shields.io/badge/ARCH-HYBRID_CLOUD-00ffff?style=for-the-badge)
![Security](https://img.shields.io/badge/SECURITY-NEURAL_VAULT-ffff00?style=for-the-badge)

> **"A inteligência não é apenas processamento, é prontidão."** > R2 é um assistente tático de alto nível, operando em arquitetura híbrida entre Estação de Trabalho Local (PC) e Redundância em Nuvem (Render).

---

## 🛠️ ARQUITETURA HÍBRIDA (FAILOVER)
O R2 opera em dois nós simultâneos para garantir 100% de Uptime:
1. **NÓ LOCAL (PC):** Interface Sci-Fi completa, controle de hardware, webcam (Sentinela) e processamento de baixa latência.
2. **NÓ CLOUD (RENDER):** Cérebro de reserva que assume automaticamente via Telegram quando o PC é desligado.



---

## 🛰️ CAPACIDADES TÁTICAS

### 📡 Monitoramento e Intel
* **Radar ADS-B:** Varredura de tráfego aéreo em tempo real no setor de Ivinhema e arredores.
* **Frontline Intel:** Relatórios atualizados de zonas de conflito (Ucrânia, Israel, Global) via LiveUAMap.
* **Space Weather:** Telemetria solar via NOAA (Kp Index, Vento Solar e Alertas Geomagnéticos).
* **Pizza Meter:** Monitoramento indireto de atividade governamental (DEFCON).

### ☁️ Utilidades e Clima
* **Previsão de Precisão:** Dados meteorológicos detalhados com fluxo de diálogo inteligente.
* **Market Intel:** Cotações em tempo real de moedas e criptoativos (BTC, USD, etc).
* **Orbital Track:** Rastreamento da Estação Espacial Internacional (ISS) com geração de mapa.

### 🛡️ Segurança e Sistema
* **Neural Vault:** Cofre criptografado para armazenamento de dados sensíveis com chave mestra.
* **Sentinela:** Captura de imagens de segurança via webcam com alerta remoto.
* **System Monitor (/sm):** Diagnóstico completo de integridade de todos os módulos do sistema.

---

## ⌨️ COMANDOS PRINCIPAIS (TELEGRAM)

| Comando | Função | Ambiente |
| :--- | :--- | :--- |
| `/start` | Inicia o Link Neural e abre o Menu | Ambos |
| `/sm` | Diagnóstico de integridade dos módulos | Ambos |
| `nuvem` | Verifica qual nó está processando a ordem | Ambos |
| `radar` | Inicia varredura de tráfego aéreo | Ambos |
| `clima` | Consulta meteorológica (Sistema pergunta a cidade) | Ambos |
| `solar` | Telemetria de clima espacial NOAA | Ambos |
| `sentinela` | Captura foto do ambiente (Webcam) | Local Only |

---

## 🚀 PARA TESTADORES (BETA PROGRAM)
O R2 está em fase de expansão. Estamos selecionando operadores para testar a estabilidade do link neural.

**Requisitos para o Nó Local:**
- Python 3.11+
- Conexão estável com a internet
- Chaves de API configuradas no `.env`

---

## 🧬 DESENVOLVEDOR
**Operador:** [Tedyzetaa](https://github.com/Tedyzetaa)  
**Sistemas:** Python | FastAPI | CustomTkinter | Telegram API