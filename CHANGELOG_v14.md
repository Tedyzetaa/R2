# filename: CHANGELOG_v14.md
# CHANGELOG — SISTEMA JUSTICEIRO ALPHA v14

## 🔥 CORREÇÕES CRÍTICAS (indicadores Lua)

1. **JUSTWIN**: Unificado bloco `instrument {}` único; corrigido `pos` inicial com `nz()`; ATR Trailing Stop agora usa `close` como valor inicial.
2. **GENERAL_INDICADOR**: Adicionadas variáveis ausentes `neutro`, `upline_color`, `lowline_color` via inputs padrão.
3. **J25**: Nenhuma correção estrutural, mas adicionado filtro de tendência ATR (integração com JUSTWIN).
4. **SUPORTE_E_RESISTENCIA**: Substituída variável inexistente `high_width` por `width`.
5. **Comunicação entre scripts**: Unificados em um único arquivo `JUSTICEIRO_ALPHA_v14.lua`, com compartilhamento da variável `trend_pos` (ATR) e níveis S/R.
6. **Remoção de ofuscação**: Eliminadas strings aleatórias e comentários sem sentido; mantidos apenas comentários técnicos em português.

## 🧠 CORREÇÕES NO MÓDULO PYTHON (alpha_module_v14.py)

7. **Candle period configurável**: Substituído divisor fixo `5` por `AlphaConfig.candle_period_seconds`.
8. **Filtro de preço ajustável**: Agora usando `asset_price_min` e `asset_price_max` (valores padrão 0 e 99999, desligado).
9. **Circuit breaker aumentado**: `CIRCUIT_BREAKER_LIMIT = 3` por padrão, configurável via `AlphaConfig`.
10. **Detecção de posição aberta**: Adicionado fallback OCR na região inferior da tela.
11. **Segurança em índices**: `evaluate_scripts` agora verifica `len(history_c) < 9` antes de acessar `C8`.
12. **Cache de sinal OCR**: Implementado `_signal_cache` com TTL configurável (`ocr_signal_cache_ttl`), evitando disparos múltiplos.
13. **Renomeação**: `run_until_success` → `run_autopilot` (nome mais semântico).
14. **Stale news**: Adicionado `is_stale()` no `NewsSentimentAnalyzer`.

## 🚀 MELHORIAS ESTRATÉGICAS

15. **Filtro de tendência ATR**: Integrado no script Lua (`buyCondition = buyCondition and (pos == 1)` etc).
16. **Filtro S/R no Python**: Classe `SRZoneTracker` com tolerância configurável; bloqueia sinais contra zonas.
17. **Engulfing como alta confiança**: Detectado no `evaluate_scripts` e eleva sinal para `TRIPLE_CONFIRMACAO` (score 80).
18. **Score de qualidade**: Substituído sistema de ticks por `SignalScore` (0-100). Executa apenas se `score >= threshold` (padrão 50).
19. **Log CSV de trades**: Gravado automaticamente ao final de cada trade (WIN/LOSS), com timestamp, ativo, direção, preços, resultado, sinal e sentimento.
20. **Timeout adaptativo**: `signal_timeout = candle_period_seconds * 2.5`.
21. **Filtro de horário**: `SessionFilter` bloqueia operações em janelas pré-definidas (09:25‑09:35, 13:55‑14:05, 15:25‑15:35 BRT).

## 📦 Configuração unificada

Todos os parâmetros foram agrupados em `AlphaConfig` (dataclass), facilitando ajustes sem alterar lógica interna.

## ✅ Compatibilidade mantida

- `alpha_engine` continua com a mesma interface pública (`attach`, `process_network_packet`, `perceive_and_act`, `get_status`, `run_autopilot`, `request_stop`).
- `main2.py` só precisa passar um `AlphaConfig` customizado se desejar, caso contrário usa valores padrão.

---
*Versão estável para implementação em ambiente real (Broker10 / IQ Option).*