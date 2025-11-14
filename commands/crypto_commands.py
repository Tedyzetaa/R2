import os
import json
import logging
from typing import Dict, Any

def register_crypto_commands(command_system, falar, ouvir_comando, trading_engine=None):
    """Registra comandos de trading de criptomoedas."""
    logger = logging.getLogger(__name__)

    # Configurações de trading para cada moeda - AGORA COM MÚLTIPLOS PARES
    TRADING_CONFIG = {
        # Pares USDT
        'nano': {'symbol': 'XNOUSDT', 'quantity': 0.01, 'name': 'Nano', 'base_asset': 'XNO', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        'xno': {'symbol': 'XNOUSDT', 'quantity': 0.01, 'name': 'Nano', 'base_asset': 'XNO', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        'dogecoin': {'symbol': 'DOGEUSDT', 'quantity': 0.3, 'name': 'Dogecoin', 'base_asset': 'DOGE', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        'doge': {'symbol': 'DOGEUSDT', 'quantity': 0.3, 'name': 'Dogecoin', 'base_asset': 'DOGE', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        'shiba': {'symbol': 'SHIBUSDT', 'quantity': 50000.0, 'name': 'Shiba Inu', 'base_asset': 'SHIB', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        'shib': {'symbol': 'SHIBUSDT', 'quantity': 50000.0, 'name': 'Shiba Inu', 'base_asset': 'SHIB', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        'cardano': {'symbol': 'ADAUSDT', 'quantity': 5.0, 'name': 'Cardano', 'base_asset': 'ADA', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        'ada': {'symbol': 'ADAUSDT', 'quantity': 5.0, 'name': 'Cardano', 'base_asset': 'ADA', 'quote_asset': 'USDT', 'tipo': 'USDT'},
        
        # Pares BTC (trading entre criptomoedas)
        'nano btc': {'symbol': 'XNOBTC', 'quantity': 1.0, 'name': 'Nano/BTC', 'base_asset': 'XNO', 'quote_asset': 'BTC', 'tipo': 'BTC'},
        'doge btc': {'symbol': 'DOGEBTC', 'quantity': 50.0, 'name': 'Dogecoin/BTC', 'base_asset': 'DOGE', 'quote_asset': 'BTC', 'tipo': 'BTC'},
        'ada btc': {'symbol': 'ADABTC', 'quantity': 10.0, 'name': 'Cardano/BTC', 'base_asset': 'ADA', 'quote_asset': 'BTC', 'tipo': 'BTC'},
        
        # Pares ETH (trading entre criptomoedas)
        'nano eth': {'symbol': 'XNOETH', 'quantity': 1.0, 'name': 'Nano/ETH', 'base_asset': 'XNO', 'quote_asset': 'ETH', 'tipo': 'ETH'},
        'doge eth': {'symbol': 'DOGEETH', 'quantity': 50.0, 'name': 'Dogecoin/ETH', 'base_asset': 'DOGE', 'quote_asset': 'ETH', 'tipo': 'ETH'},
        
        # Pares BNB (trading entre criptomoedas)
        'doge bnb': {'symbol': 'DOGEBNB', 'quantity': 50.0, 'name': 'Dogecoin/BNB', 'base_asset': 'DOGE', 'quote_asset': 'BNB', 'tipo': 'BNB'},
        'ada bnb': {'symbol': 'ADABNB', 'quantity': 10.0, 'name': 'Cardano/BNB', 'base_asset': 'ADA', 'quote_asset': 'BNB', 'tipo': 'BNB'},
    }

    # Mapeamento de tipos de pares para nomes amigáveis
    TIPO_PARA_NOME = {
        'USDT': 'USDT',
        'BTC': 'Bitcoin', 
        'ETH': 'Ethereum',
        'BNB': 'BNB'
    }

    def obter_cotacao_cripto(cripto="", falar_func=None, ouvir_func=None):
        try:
            if not cripto:
                falar_func("Qual criptomoeda você quer consultar?")
                cripto = ouvir_func()
                
            if not cripto:
                falar_func("Não entendi o nome da criptomoeda.")
                return

            cripto = cripto.lower().strip()
            
            # Verifica se a moeda está no nosso config
            if cripto in TRADING_CONFIG:
                config = TRADING_CONFIG[cripto]
                symbol = config['symbol']
                nome = config['name']
                
                if trading_engine:
                    preco = trading_engine.binance_client.get_ticker_price(symbol)
                    if preco:
                        if config['tipo'] == 'USDT':
                            falar_func(f"O preço da {nome} é ${preco:,.4f}")
                        else:
                            falar_func(f"O preço da {nome} é {preco:,.8f} {config['quote_asset']}")
                        return
            
            # Fallback para CoinGecko
            import requests
            moedas_gecko = {
                'bitcoin': 'bitcoin',
                'ethereum': 'ethereum',
                'doge': 'dogecoin',
                'dogecoin': 'dogecoin',
                'cardano': 'cardano',
                'ada': 'cardano',
                'nano': 'nano',
                'xno': 'nano',
                'shiba': 'shiba-inu',
                'shib': 'shiba-inu'
            }
            
            moeda_id = moedas_gecko.get(cripto, cripto)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={moeda_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if moeda_id in data:
                preco = data[moeda_id]["usd"]
                nome_display = TRADING_CONFIG.get(cripto, {}).get('name', cripto)
                falar_func(f"O preço da {nome_display} é ${preco:,.4f}")
            else:
                falar_func(f"Criptomoeda {cripto} não encontrada.")
                
        except Exception as e:
            logger.error(f"Erro ao obter cotação: {e}")
            falar_func("Erro ao buscar cotação de criptomoeda.")

    def verificar_saldo_para_trade_avancado(symbol, operacao, quantity, falar_func):
        """Verificação de saldo avançada para múltiplos tipos de pares"""
        if not trading_engine:
            return False
            
        try:
            # Encontra a configuração do par
            config = None
            for key, cfg in TRADING_CONFIG.items():
                if cfg['symbol'] == symbol:
                    config = cfg
                    break
            
            if not config:
                falar_func(f"Par {symbol} não configurado.")
                return False
            
            base_asset = config['base_asset']
            quote_asset = config['quote_asset']
            
            account_info = trading_engine.binance_client.get_account_info()
            if not account_info:
                falar_func("Erro ao verificar saldo da conta.")
                return False
            
            # Para COMPRAS: precisa da moeda de cotação
            if operacao.upper() == "BUY":
                saldo_quote = 0
                for balance in account_info['balances']:
                    if balance['asset'] == quote_asset:
                        saldo_quote = float(balance['free'])
                        break
                
                # Calcula custo aproximado
                current_price = trading_engine.binance_client.get_ticker_price(symbol)
                if current_price:
                    custo_aproximado = current_price * quantity
                    
                    if saldo_quote < custo_aproximado:
                        falar_func(f"Saldo de {quote_asset} insuficiente para comprar {symbol}.")
                        falar_func(f"Necessário: ~{custo_aproximado:.6f} {quote_asset}, Disponível: {saldo_quote:.6f}")
                        return False
                
                return True
            
            # Para VENDAS: precisa da moeda base
            elif operacao.upper() == "SELL":
                saldo_base = 0
                for balance in account_info['balances']:
                    if balance['asset'] == base_asset:
                        saldo_base = float(balance['free'])
                        break
                
                if saldo_base < quantity:
                    falar_func(f"Saldo de {base_asset} insuficiente para vender {symbol}.")
                    falar_func(f"Necessário: {quantity} {base_asset}, Disponível: {saldo_base:.4f}")
                    return False
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar saldo para trade: {e}")
            falar_func("Erro ao verificar saldo disponível.")
            return False

    def iniciar_trading_automatico(comando_completo="", falar_func=None, ouvir_func=None):
        """Inicia trading automático em um comando único"""
        if not trading_engine:
            falar_func("Sistema de trading não disponível.")
            return
            
        # Extrai estratégia e moeda do comando completo
        partes = comando_completo.lower().strip().split()
        
        # Mapeamento de estratégias
        estrategias = {
            'sma': 'sma',
            'rsi': 'rsi',
            'um': 'sma',
            '1': 'sma',
            'dois': 'rsi',
            '2': 'rsi'
        }
        
        # Tenta extrair estratégia e moeda do comando
        estrategia = None
        moeda = None
        
        for parte in partes:
            if parte in estrategias:
                estrategia = estrategias[parte]
            elif parte in TRADING_CONFIG:
                moeda = parte
        
        # Se não encontrou no comando, pede informações
        if not estrategia:
            falar_func("Qual estratégia deseja usar? SMA ou RSI?")
            resposta = ouvir_func()
            if resposta:
                estrategia = estrategias.get(resposta.lower().strip())
        
        if not estrategia:
            falar_func("Estratégia não reconhecida. Use SMA ou RSI.")
            return
            
        if not moeda:
            falar_func("Para qual par de trading? Diga o nome como 'doge', 'nano btc' ou 'ada eth'")
            resposta = ouvir_func()
            if resposta and resposta.lower().strip() in TRADING_CONFIG:
                moeda = resposta.lower().strip()
        
        if not moeda:
            falar_func("Par de trading não reconhecido ou não suportado.")
            return
        
        # Obtém configurações da moeda
        config = TRADING_CONFIG[moeda]
        symbol = config['symbol']
        quantity = config['quantity']
        nome = config['name']
        tipo = config['tipo']
        
        # Verifica saldo antes de iniciar (apenas aviso)
        if not verificar_saldo_para_trade_avancado(symbol, "BUY", quantity, falar_func):
            falar_func("Atenção: Saldo insuficiente para compras iniciais, mas o trading será iniciado para vendas.")
        
        resultado = trading_engine.start_auto_trading(estrategia, symbol, quantity)
        if resultado:
            tipo_nome = TIPO_PARA_NOME.get(tipo, tipo)
            falar_func(f"Trading {estrategia.upper()} iniciado para {nome} com quantidade {quantity} - Par: {tipo_nome}")
        else:
            falar_func("Erro ao iniciar trading automático.")

    def listar_pares_trading(falar_func=None, ouvir_func=None):
        """Lista todos os pares de trading disponíveis"""
        if not trading_engine:
            falar_func("Sistema de trading não disponível.")
            return
            
        falar_func("Pares de trading disponíveis:")
        
        # Agrupa por tipo
        pares_por_tipo = {}
        for config in TRADING_CONFIG.values():
            tipo = config['tipo']
            if tipo not in pares_por_tipo:
                pares_por_tipo[tipo] = []
            pares_por_tipo[tipo].append(f"{config['name']} - Qtd: {config['quantity']}")
        
        for tipo, pares in pares_por_tipo.items():
            tipo_nome = TIPO_PARA_NOME.get(tipo, tipo)
            falar_func(f"{tipo_nome}:")
            for par in pares:
                falar_func(f"  {par}")

    def status_trading_avancado(falar_func=None, ouvir_func=None):
        """Status detalhado do trading"""
        if not trading_engine:
            falar_func("Sistema de trading não disponível.")
            return
            
        status = trading_engine.get_status()
        
        if status['trading_ativo']:
            falar_func(f"Trading ativo com {status['trades_ativos']} pares:")
            
            for symbol, detalhes in status['pares_detalhes'].items():
                mensagem = f"{symbol}: {detalhes['estrategia']}, "
                mensagem += f"Posição: {'aberta' if detalhes['posicao_aberta'] else 'fechada'}, "
                if detalhes['preco_atual']:
                    mensagem += f"Preço: {detalhes['preco_atual']:.6f}"
                falar_func(mensagem)
                
            falar_func(f"Total de trades no histórico: {status['total_historico_trades']}")
        else:
            falar_func("Trading não está ativo no momento.")

    # ... (mantenha as outras funções como comprar_cripto, vender_cripto, etc.)

    # Registra comandos de trading
    if trading_engine:
        # Comando principal flexível
        command_system.register_command(
            "iniciar trading", iniciar_trading_automatico, 
            "Inicia trading automático. Ex: 'iniciar trading sma doge' ou 'iniciar trading rsi nano btc'"
        )
        
        # Comando parar e status
        command_system.register_command(
            "parar trading", lambda f, o: trading_engine.stop_auto_trading() if trading_engine else f("Sistema não disponível"),
            "Para todo o trading automático"
        )
        
        command_system.register_command(
            "status trading", status_trading_avancado,
            "Mostra status detalhado do trading automático"
        )
        
        command_system.register_command(
            "listar pares", listar_pares_trading,
            "Lista todos os pares de trading disponíveis"
        )

        # Comandos específicos para cada moeda e estratégia
        estrategias = ['sma', 'rsi']
        for moeda in TRADING_CONFIG.keys():
            for estrategia in estrategias:
                comando = f"trading {estrategia} {moeda}"
                # Função lambda para capturar os valores corretos
                command_system.register_command(
                    comando, 
                    lambda f, o, m=moeda, e=estrategia: iniciar_trading_automatico(f"{e} {m}", f, o),
                    f"Inicia trading {estrategia.upper()} para {TRADING_CONFIG[moeda]['name']}"
                )

    # Comandos de cotação para todas as moedas
    command_system.register_command("cotação", obter_cotacao_cripto, "Mostra cotação de criptomoeda")
    
    # Comandos específicos de cotação para cada moeda
    for moeda, config in TRADING_CONFIG.items():
        nome = config['name']
        command_system.register_command(
            moeda, 
            lambda f, o, m=moeda: obter_cotacao_cripto(m, f, o), 
            f"Cotação da {nome}"
        )