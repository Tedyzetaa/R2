#!/usr/bin/env python3
"""
Teste de conexão com a Binance
"""

import os
from dotenv import load_dotenv
from binance.client import Client

# Carrega variáveis de ambiente
load_dotenv()

def test_binance_connection():
    print("🧪 Testando conexão com Binance...")
    
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    
    print(f"API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'N/A'}")
    print(f"Secret Key: {secret_key[:10]}...{secret_key[-10:] if secret_key else 'N/A'}")
    
    if not api_key or not secret_key:
        print("❌ Chaves API não encontradas no arquivo .env")
        return False
    
    try:
        # Testa com testnet primeiro
        client = Client(api_key, secret_key, testnet=True)
        
        # Tenta obter informações da conta
        account_info = client.get_account()
        print("✅ Conexão com Binance TESTNET bem-sucedida!")
        print(f"💰 Saldo disponível:")
        
        for balance in account_info['balances']:
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                print(f"   {balance['asset']}: Livre={balance['free']}, Em ordens={balance['locked']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na TESTNET: {e}")
        
        try:
            # Tenta com mainnet
            print("🔄 Tentando conexão com MAINNET...")
            client = Client(api_key, secret_key, testnet=False)
            account_info = client.get_account()
            print("✅ Conexão com Binance MAINNET bem-sucedida!")
            return True
            
        except Exception as e2:
            print(f"❌ Erro na MAINNET: {e2}")
            print("\n🔧 SOLUÇÃO:")
            print("1. Verifique se as chaves API estão corretas")
            print("2. Certifique-se de que a API tem permissões de leitura e trading")
            print("3. Use chaves da TESTNET para desenvolvimento")
            print("4. Verifique se o IP está whitelisted (se aplicável)")
            return False

if __name__ == "__main__":
    test_binance_connection()