import streamlit as st
import json
import time
import datetime
import requests 
import pandas as pd
from core.api_market import obter_rentabilidade_atual
from core.gpu_telemetry import obter_status_gpu
from core.process_manager import GerenciadorMinerador

st.set_page_config(page_title="Nexus Auto-Miner", layout="wide")

if 'gerenciador' not in st.session_state: st.session_state.gerenciador = GerenciadorMinerador()
if 'minerando' not in st.session_state: st.session_state.minerando = False
if 'resfriando' not in st.session_state: st.session_state.resfriando = False 
if 'logs' not in st.session_state: st.session_state.logs = [] 
if 'grafico_velocidade' not in st.session_state: st.session_state.grafico_velocidade = [] 

@st.cache_data(ttl=600)
def buscar_mercado_cache():
    return obter_rentabilidade_atual()

@st.cache_data(ttl=60)
def consultar_saldo_pool(algoritmo, carteira):
    try:
        # Se for Unmineable Modo Anônimo (Antigo)
        if algoritmo == "beam-iii" and ":" in carteira:
            moeda = carteira.split(":")[0]
            endereco = carteira.split(":")[1].split(".")[0]
            res = requests.get(f"https://api.unminable.com/v4/address/{endereco}?coin={moeda}", timeout=3)
            if res.status_code == 200:
                return float(res.json().get('data', {}).get('balance', 0.0)), moeda
                
        # Se for HeroMiners
        elif algoritmo == "karlsenv2":
            res = requests.get(f"https://karlsen.herominers.com/api/stats_address?address={carteira}", timeout=3)
            if res.status_code == 200:
                saldo_bruto = int(res.json().get('stats', {}).get('balance', 0))
                return float(saldo_bruto / 100000000), "KLS"
                
        # NOVO: Se for Unmineable Modo Conta Privada (Novo Dashboard)
        elif algoritmo == "beam-iii" and ":" not in carteira:
            return 0.0, "NO SITE"
    except:
        pass
    
    sigla = "NANO"
    if algoritmo == "karlsenv2": sigla = "KLS"
    elif ":" not in carteira: sigla = "CONTA"
    return 0.0, sigla

@st.cache_data(ttl=120)
def consultar_extrato(algoritmo, carteira):
    try:
        if algoritmo == "beam-iii" and ":" in carteira:
            moeda = carteira.split(":")[0]
            endereco = carteira.split(":")[1].split(".")[0]
            res = requests.get(f"https://api.unminable.com/v4/address/{endereco}/payments?coin={moeda}", timeout=3)
            if res.status_code == 200:
                return res.json().get('data', {}).get('list', [])
        elif algoritmo == "karlsenv2":
            res = requests.get(f"https://karlsen.herominers.com/api/stats_address?address={carteira}", timeout=3)
            if res.status_code == 200:
                pagamentos = res.json().get('payments', [])
                extrato_formatado = []
                for p in pagamentos:
                    extrato_formatado.append({
                        "Data": datetime.datetime.fromtimestamp(p['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                        "Valor": f"{p['amount'] / 100000000:.4f} KLS",
                        "Transação (TX)": p['tx'][:20] + "..."
                    })
                return extrato_formatado
    except:
        pass
    return []

def obter_link_pool(algoritmo, carteira):
    # Se for Conta Privada, leva pro Dashboard Geral de login
    if algoritmo == "beam-iii" and ":" not in carteira:
        return "https://unmineable.com/dashboard"
    elif algoritmo == "beam-iii" and ":" in carteira:
        moeda = carteira.split(":")[0]
        endereco = carteira.split(":")[1].split(".")[0]
        return f"https://unmineable.com/coins/{moeda}/address/{endereco}"
    elif algoritmo == "karlsenv2":
        return f"https://karlsen.herominers.com/?context=address&mac={carteira}"
    return "#"

def adicionar_log(mensagem):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{agora}] {mensagem}") 
    if len(st.session_state.logs) > 50: st.session_state.logs.pop()

def carregar_configs():
    with open('config/wallets.json', 'r') as f: wallets = json.load(f)
    with open('config/pools.json', 'r') as f: pools = json.load(f)
    return wallets, pools

def ler_api_minerador():
    if not st.session_state.minerando or st.session_state.resfriando: return 0.0
    try:
        res = requests.get("http://127.0.0.1:4444/summary", timeout=1)
        dados = res.json()
        velocidade = round(float(dados['Algorithms'][0]['Total_Performance']), 2)
        return velocidade
    except:
        return 0.0

st.title("⛏️ Nexus Auto-Miner - Edição Mobile (RTX 3050)")

wallets, pools = carregar_configs()
gpu_stats = obter_status_gpu()
mercado, melhor_algo = buscar_mercado_cache()

velocidade_atual = ler_api_minerador()

saldo_atual, sigla_moeda = consultar_saldo_pool(melhor_algo, wallets[melhor_algo])

if st.session_state.minerando:
    st.session_state.grafico_velocidade.append(velocidade_atual)
    if len(st.session_state.grafico_velocidade) > 30:
        st.session_state.grafico_velocidade.pop(0)

col1, col2, col3, col4, col5 = st.columns(5)

temp_atual = float(gpu_stats['temperatura'])
str_temp = f"{temp_atual} °C"
if temp_atual >= 90:
    str_temp = f"🔥 {temp_atual} °C (CRÍTICO)"

with col1: st.metric("🌡️ Temp. GPU", str_temp)
with col2: st.metric("⚡ Consumo", f"{gpu_stats['energia_w']} W")
with col3: st.metric("📈 Algoritmo", melhor_algo.upper())
unidade_hash = "Sol/s" if melhor_algo == "beam-iii" else "MH/s"
with col4: st.metric("🚀 Hashrate Real", f"{velocidade_atual} {unidade_hash}") 

# Exibição inteligente para conta privada
if sigla_moeda in ["NO SITE", "CONTA"]:
    with col5: st.metric("🔒 Conta Privada", "Ver Dashboard")
else:
    with col5: st.metric("💰 Saldo na Pool", f"{saldo_atual:.6f} {sigla_moeda}") 

st.divider()

col_grafico, col_controle = st.columns([3, 1])

with col_grafico:
    st.subheader(f"Estabilidade da Mineração ({unidade_hash})")
    if st.session_state.resfriando:
        st.warning("⚠️ Mineração pausada automaticamente. Aguardando a placa resfriar até 65 °C...")
    elif len(st.session_state.grafico_velocidade) > 0:
        st.line_chart(st.session_state.grafico_velocidade, height=150)
    else:
        st.info("Aguardando o minerador iniciar para gerar o gráfico...")

with col_controle:
    st.subheader("Controle")
    
    if st.button("▶️ Iniciar" if not st.session_state.minerando else "⏹️ Parar", use_container_width=True):
        st.session_state.minerando = not st.session_state.minerando
        if not st.session_state.minerando:
            st.session_state.gerenciador.parar()
            st.session_state.resfriando = False 
            st.session_state.grafico_velocidade.clear() 
            adicionar_log("🛑 Minerador parado manualmente.")
        else:
            adicionar_log("▶️ Minerador ativado! Iniciando motores...")
            
    st.markdown("<br>", unsafe_allow_html=True)
    link_banco = obter_link_pool(melhor_algo, wallets[melhor_algo])
    st.link_button(f"🏦 Abrir Dashboard", link_banco, use_container_width=True)

st.divider()

st.subheader(f"🧾 Histórico de Depósitos")
extrato = consultar_extrato(melhor_algo, wallets[melhor_algo])

if sigla_moeda in ["NO SITE", "CONTA"]:
    st.info("🔒 Seu minerador está conectado a uma Conta Privada. Clique no botão 'Abrir Dashboard' acima para acompanhar seus ganhos em tempo real.")
elif extrato:
    df = pd.DataFrame(extrato)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum depósito recente encontrado ou a API está temporariamente indisponível.")

st.divider()

if st.session_state.minerando:
    if temp_atual >= 90 and not st.session_state.resfriando:
        st.session_state.resfriando = True
        st.session_state.gerenciador.parar()
        adicionar_log(f"🔥 ALERTA TÉRMICO: Placa atingiu os {temp_atual} °C! Mineração pausada.")
        
    elif temp_atual <= 65 and st.session_state.resfriando:
        st.session_state.resfriando = False
        adicionar_log("❄️ Placa resfriada para 65 °C! Retomando a mineração...")
        
    if not st.session_state.resfriando:
        algo_atual = st.session_state.gerenciador.algo_atual
        if algo_atual != melhor_algo:
            if algo_atual is None: adicionar_log(f"Iniciando mineração de {melhor_algo.upper()} (Conta Logada)...")
            
            sucesso = st.session_state.gerenciador.iniciar(melhor_algo, wallets[melhor_algo], pools[melhor_algo])
            if sucesso: adicionar_log(f"✅ {melhor_algo.upper()} rodando. Aguardando conexão com a pool...")
            else: 
                adicionar_log(f"❌ ERRO ao iniciar.")
                st.session_state.minerando = False

st.subheader("Terminal de Eventos")
if st.session_state.logs: st.code("\n".join(st.session_state.logs), language="text")
else: st.caption("Nenhum evento.")

if st.session_state.minerando:
    time.sleep(5)
    st.rerun()