# 🎯 Guia de Integração - Nova Análise de Velas por Pixels

## 📌 O que mudou?

A função `perceive_and_act()` no `alpha_module.py` agora:

1. ✅ **Não trava se OCR falhar** - fallback para análise de cores
2. ✅ **Analisa pixels diretamente** - detecta velas verdes (CALL) ou vermelhas (PUT)
3. ✅ **Coleta histórico sempre** - mesmo sem texto detectado
4. ✅ **Estado COLLECTING** - retorna com progresso enquanto junta dados

## 🧪 Teste Rápido

### Opção 1: Script Isolado
```bash
python test_vision.py
```

Este script:
- ✅ Verifica Tesseract
- ✅ Captura screenshot
- ✅ Extrai texto OCR
- ✅ Executa ciclo de percepção
- ✅ Mostra histórico de velas

### Opção 2: Integração no main2.py

Adicione isso no seu `main2.py` antes de chamar o loop principal:

```python
import asyncio
from alpha_module import alpha_engine

# ... código anterior ...

async def test_r2_vision():
    """Testa se o R2 consegue ver a tela"""
    print("\n👀 Testando visão do R2...")
    
    # Executar alguns ciclos de teste
    for i in range(5):
        result = await alpha_engine.perceive_and_act()
        print(f"Ciclo {i+1}: {result.get('state')} - Histórico: {len(alpha_engine.candle_history)}/10")
        
        if result.get('state') == 'COLLECTING':
            print(f"  → {result.get('msg')}")
        elif result.get('recommended_action'):
            print(f"  → Ação: {result.get('recommended_action')}")
        
        await asyncio.sleep(0.5)
    
    return {"vision_test": "completed"}

# Chamar antes do autopilot (se necessário)
# asyncio.run(test_r2_vision())
```

## 🔧 Ajustar Zona de Análise de Cores

Se o script não está detectando as cores corretamente, edite o método `_analyze_candle_colors()` em `alpha_module.py`:

```python
# Ajuste essas proporções para sua corretora (linhas ~960):
left = int(width * 0.3)    # 30% do lado esquerdo
right = int(width * 0.7)   # 70% do lado direito
top = int(height * 0.2)    # 20% do topo
bottom = int(height * 0.6) # 60% da altura
```

**Dica:** Abra seu broker em tela cheia, note onde fica o gráfico de velas, e ajuste essas proporções.

## 📊 Interpretar Logs

```
[DEBUG OCR] Texto lido: COMPRA CALL EUR/USD...
  → OCR detectou "COMPRA"
  
⚠️ OCR falhou: [erro aqui]
  → Tesseract teve problema, mas análise de cores vai tentar

✅ Sinal detectado por análise de pixels: CALL
  → Cores verdes foram detectadas na zona

🔴 Vela BAIXA detectada: vermelho: 150
  → Detectou vela vermelha (PUT)

📊 Estado: COLLECTING (3/10)
  → Coletando dados, histórico em progresso
```

## ⚙️ Configurações do AlphaConfig

Você pode ajustar no seu código:

```python
from alpha_module import AlphaConfig, AlphaEngine

config = AlphaConfig(
    analysis_window=10,              # Quantas velas coletar (padrão: 10)
    min_pattern_strength=0.7,        # Mínimo 70% de concordância
    signal_score_threshold=30,       # Score mínimo para executar trade
    candle_period_seconds=5          # Período de vela em segundos
)

engine = AlphaEngine(config=config)
```

## 🚀 Próximos Passos

1. **Execute** `test_vision.py` para validar:
   ```bash
   python test_vision.py
   ```

2. **Monitore** os logs do terminal:
   - Procure por "🔍 [DEBUG OCR]" → mostra texto lido
   - Procure por "✅ Sinal detectado" → mostra como foi detectado
   - Procure por "COLLECTING" → mostra progresso do histórico

3. **Ajuste** o método `_analyze_candle_colors()` se necessário

4. **Valide** que o histórico chega a 10 velas antes de executar trades

## 📝 Referência: Estados Possíveis

```python
# Em perceive_and_act():
{
    "state": "COLLECTING",           # Coletando dados
    "msg": "Coletando dados... (3/10)"
}

# Ou quando pronto:
{
    "state": ScreenState.GATINHO_CALL,
    "recommended_action": "CALL",
    "confidence": 85.5
}
```

## 💡 Dicas de Troubleshooting

| Sintoma | Causa | Solução |
|---------|-------|---------|
| Histórico nunca preenche | OCR não detecta, cores ambíguas | Ajuste zona em `_analyze_candle_colors` |
| Erro "Tesseract not found" | Path incorreto | Execute `TESSERACT_SETUP.md` |
| Screenshot em branco | WASM não carregou, aba fora de foco | Aguarde carregamento, coloque em foco |
| Cores erradas detectadas | Zona de análise fora do gráfico | Ajuste `left, right, top, bottom` |

## ✅ Checklist de Validação

- [ ] Tesseract instalado e configurado
- [ ] `test_vision.py` executado com sucesso
- [ ] Logs mostram texto sendo lido pelo OCR ou cores detectadas
- [ ] Histórico de velas preenchendo (progredindo de 0 a 10)
- [ ] Estado muda para `GATINHO_CALL` ou `GATINHO_PUT` quando pronto
- [ ] Nenhum erro de "trava de segurança" nos logs

---

**Última atualização:** 2026-04-29
**Versão:** alpha_module.py v14 com análise por pixels
