🤖 R2 Assistant - Assistente Pessoal em Python
Um assistente virtual estilo Jarvis desenvolvido em Python com interface gráfica, reconhecimento de voz, sintetização de fala e sistema completo de trading automático.

https://img.shields.io/badge/Python-3.10+-blue.svg
https://img.shields.io/badge/License-MIT-green.svg
https://img.shields.io/badge/Version-1.1-red.svg
https://img.shields.io/badge/Trading-Autom%C3%A1tico-green.svg

🆕 VERSÃO 1.1 - SISTEMA DE TRADING COMPLETO
📈 Novas Funcionalidades Principais
🤖 Trading Automático com múltiplas estratégias

💰 Suporte a Dinheiro Real (Binance Mainnet)

📊 Histórico Completo de negociações

🎯 Interface Profissional para trading

🔄 Múltiplos Pares de criptomoedas

📋 HISTÓRICO DE ATUALIZAÇÕES - v1.0 → v1.1
v1.01 - Base do Sistema de Trading
✅ Implementação do BinanceClient para conexão segura com API

✅ Criação do TradingEngine com loop de execução automática

✅ Estratégia SMA Crossover convertida do JavaScript para Python

✅ Sistema modular de estratégias (BaseStrategy, SMACrossoverStrategy, RSIStrategy)

v1.02 - Indicadores Técnicos
✅ Implementação de SMA (Simple Moving Average)

✅ Implementação de RSI (Relative Strength Index)

✅ Implementação de MACD (Moving Average Convergence Divergence)

✅ Sistema expansível para novos indicadores

v1.03 - Interface Gráfica de Trading
✅ Painel de trading integrado à interface principal

✅ Gráficos em tempo real com matplotlib

✅ Controles de início/parada de trading

✅ Visualização de status e histórico

v1.04 - Comandos de Voz para Trading
✅ "R2, trading sma nano" - Inicia trading automático em um comando

✅ "R2, status trading" - Mostra status das operações

✅ "R2, parar trading" - Para todas as operações

✅ "R2, comprar/vender [moeda]" - Ordens manuais por voz

v1.05 - Múltiplas Criptomoedas Voláteis
✅ Nano (XNO) - Transações instantâneas, zero fees

✅ Dogecoin (DOGE) - Alta volatilidade, comunidade forte

✅ Shiba Inu (SHIB) - Meme coin extremamente volátil

✅ Cardano (ADA) - Smart contracts, pesquisa acadêmica

✅ Algorand (ALGO) - Proof-of-stake puro

✅ VeChain (VET) - Supply chain, enterprise focus

✅ E mais 5 moedas de baixo preço

v1.06 - Sistema de Pares Múltiplos
✅ Pares USDT: DOGEUSDT, XNOUSDT, ADAUSDT, SHIBUSDT

✅ Pares BTC: XNOBTC, DOGEBTC, ADABTC (trading entre criptos)

✅ Pares ETH: XNOETH, DOGEETH

✅ Pares BNB: DOGEBNB, ADABNB

v1.07 - Verificação de Saldo Inteligente
✅ Verificação automática de saldo antes de trades

✅ Suporte tanto para COMPRAS (precisa de USDT) quanto VENDAS (precisa da moeda)

✅ Painel de saldos em tempo real na interface

✅ Atualização automática a cada 15 segundos

v1.08 - Interface Avançada de Trading
✅ Painel de pares ativos com controle individual

✅ Gráficos interativos com seleção de par

✅ Histórico de trades com cores (🟢 compra / 🔴 venda)

✅ Botões de ação rápida e controles granulares

v1.09 - Histórico Completo de Negociação
✅ Dois painéis: Histórico recente + histórico completo

✅ Cálculo automático de P&L para cada trade

✅ Exportação para CSV para análise externa

✅ Estatísticas detalhadas (Win Rate, P&L total, etc.)

✅ Sistema de salvamento em JSON e CSV

v1.10 - Modo Dinheiro Real
✅ Confirmações de segurança para todas as ordens

✅ Avisos claros sobre trading com dinheiro real

✅ Interface com destaque vermelho para alertas

✅ Configuração para Binance Mainnet

v1.11 - Otimizações Finais
✅ Correção de bugs e melhorias de performance

✅ Melhor tratamento de erros da API Binance

✅ Interface mais responsiva e informativa

✅ Documentação completa atualizada

🎯 Funcionalidades da Versão 1.1
🎤 Comandos por Voz - TRADING
bash
# Trading Automático
"R2, trading sma nano"              # Inicia SMA para Nano
"R2, trading rsi doge"              # Inicia RSI para Dogecoin  
"R2, trading sma doge btc"          # Trading entre Dogecoin e Bitcoin
"R2, status trading"                # Status de todos os pares
"R2, parar trading"                 # Para todo o trading

# Ordens Manuais
"R2, comprar nano"                  # Compra 0.01 Nano
"R2, vender doge"                   # Vende 0.3 Dogecoin
"R2, comprar ada"                   # Compra 5.0 Cardano

# Informações
"R2, saldo"                         # Mostra saldos principais
"R2, cotação nano"                  # Preço da Nano
"R2, listar pares"                  # Pares disponíveis
💰 Sistema de Trading
🤖 Estratégias: SMA Crossover, RSI

📈 Pares: 10+ criptomoedas voláteis

⚡ Execução: Ordens market em tempo real

📊 Análise: Gráficos com indicadores em tempo real

💰 Modos: Testnet (desenvolvimento) e Mainnet (real)

📊 Histórico e Análise
📋 Histórico Completo: Todos os trades com timestamps

💰 Cálculo de P&L: Lucro/prejuízo automático

📈 Estatísticas: Win Rate, trades lucrativos, P&L total

💾 Exportação: CSV para Excel/Google Sheets

🎯 Métricas: Performance por estratégia e par

🚀 Instalação Rápida
1. Clone e Configure
bash
git clone https://github.com/seu-usuario/r2-assistant.git
cd r2-assistant
conda env create -f environment.yml
conda activate r2_assistant
2. Configure as APIs de Trading
bash
# Edite o arquivo .env
BINANCE_API_KEY=sua_chave_da_mainnet
BINANCE_SECRET_KEY=seu_secret_da_mainnet
TESTNET=False  # Para dinheiro real
3. Execute o R2 Assistant
bash
python main.py
📈 Estrutura do Módulo de Trading
text
trading/
├── binance_client.py          # Cliente seguro Binance API
├── trading_engine.py          # Motor principal de trading
├── strategies/
│   ├── base_strategy.py       # Classe base para estratégias
│   ├── sma_crossover.py       # Estratégia SMA Crossover
│   └── rsi_strategy.py        # Estratégia RSI
├── indicators/
│   ├── sma.py                 # Simple Moving Average
│   ├── rsi.py                 # Relative Strength Index
│   └── macd.py                # MACD
└── ui/
    └── trading_gui.py         # Interface gráfica completa
⚠️ AVISO IMPORTANTE - TRADING REAL
🔴 Riscos do Trading com Dinheiro Real
⚠️ Você pode perder dinheiro

⚠️ Criptomoedas são extremamente voláteis

⚠️ Nunca invista mais do que pode perder

⚠️ Monitore as operações constantemente

🛡️ Medidas de Segurança Implementadas
✅ Confirmação para todas as ordens

✅ Verificação de saldo antes de trades

✅ Limites de quantidade configuráveis

✅ Interface com alertas visuais

✅ Histórico completo para auditoria

🔧 Configuração de Trading
🎯 Parâmetros Ajustáveis
python
# Em config/settings.py
TRADING_ENABLED = True
TESTNET = False  # True para testes, False para dinheiro real
QUANTITY_CONFIG = {
    'nano': 0.01,      # 0.01 XNO por trade
    'doge': 0.3,       # 0.3 DOGE por trade  
    'ada': 5.0,        # 5.0 ADA por trade
    'shib': 50000.0    # 50,000 SHIB por trade
}
📊 Estratégias Disponíveis
SMA Crossover: Compra quando SMA13 > SMA21, vende quando SMA13 < SMA21

RSI Strategy: Compra quando RSI < 30 (oversold), vende quando RSI > 70 (overbought)

📊 Recursos de Análise
📈 Painel de Histórico
Trades Recentes: Últimos 15 trades em tempo real

Histórico Completo: Todos os trades com P&L calculado

Estatísticas: Win Rate, P&L total, performance por estratégia

Exportação: CSV para análise externa

💹 Métricas Calculadas
python
# Exemplo de métricas disponíveis
{
    'total_trades': 45,
    'win_rate': 62.5,      # % de trades lucrativos
    'total_pnl': 125.50,   # P&L total em USDT
    'best_trade': 45.20,   # Melhor trade
    'worst_trade': -15.75  # Pior trade
}
🐛 Solução de Problemas - Trading
❌ Erro: "Invalid API-key"
Solução:

bash
# Use chaves da Testnet para desenvolvimento
TESTNET = True
# Ou configure chaves corretas da Mainnet
❌ Erro: "Saldo insuficiente"
Solução:

Verifique se as moedas estão na carteira SPOT

Para compras: precisa de USDT na Spot

Para vendas: precisa da criptomoeda na Spot

❌ Erro: "Symbol not found"
Solução:

Verifique se o símbolo existe na Binance

Use formato correto: DOGEUSDT, XNOBTC, etc.

🔮 Próximas Atualizações Planejadas
🚀 v1.2 - Backtesting e Otimização
Sistema de backtesting com dados históricos

Otimização de parâmetros de estratégias

Relatórios de performance detalhados

🎯 v1.3 - Estratégias Avançadas
Machine Learning para previsão de preços

Grid Trading e DCA (Dollar Cost Averaging)

arbitragem entre exchanges

🔒 v1.4 - Segurança Avançada
Stop-loss e take-profit automáticos

Gestão de risco integrada

Alertas de mercado em tempo real

📞 Suporte e Comunidade
📧 Email: suporte@r2assistant.com

💬 Discord: [Link do servidor]

🐛 Issues: [GitHub Issues]

📚 Documentação: [Wiki do projeto]

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

⚠️ AVISO LEGAL: Trading de criptomoedas envolve riscos significativos. O R2 Assistant é uma ferramenta educacional e não constitui aconselhamento financeiro.

🎉 R2 Assistant v1.1 - Seu assistente pessoal agora também é seu trader automático!