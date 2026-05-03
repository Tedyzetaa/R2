-- filename: JUSTICEIRO_ALPHA_v14.lua
-- ====================================================================
-- MÓDULO: JUSTICEIRO ALPHA v14 (indicador unificado)
-- PLATAFORMA: TradingView / Broker10 (sintaxe Lua-like)
-- AUTOR: R2 Ghost Protocol
-- DESCRIÇÃO: Combina ATR Trailing Stop (tendência), crossover diferencial 
--            (sinais), níveis S/R multi-período e coloração de velas.
--            Inclui filtros de tendência (pos) e bloqueio contra entradas 
--            em zonas de suporte/resistência.
-- ====================================================================

-- ====================================================================
-- SEÇÃO 1: CONFIGURAÇÕES E INPUTS DO USUÁRIO
-- ====================================================================
-- Parâmetros ATR
atr_period    = input(14, "Período ATR")
atr_mult      = input(3.0, "Multiplicador ATR")

-- Parâmetros MACD diferencial (estilo J25)
fast_length   = input(9, "Média Rápida")
slow_length   = input(21, "Média Lenta")
signal_length = input(7, "Média do Sinal")

-- Parâmetros de suporte/resistência
sr_lookback   = input(100, "Lookback S/R")
sr_tolerance  = input(0.002, "Tolerância S/R (%)") / 100

-- Parâmetros de visualização
show_sr_lines = input(true, "Mostrar linhas S/R")
show_atr_line = input(true, "Mostrar linha ATR")
color_bullish = input(color.green, "Cor Bullish")
color_bearish = input(color.red, "Cor Bearish")

-- ====================================================================
-- SEÇÃO 2: CÁLCULO DO ATR TRAILING STOP (tendência macro)
-- Extraído e unificado do JUSTWIN original
-- ====================================================================
function atr_trailing_stop()
    -- ATR usual
    atr_val = ta.atr(atr_period)
    
    -- Trailing stop baseado em ATR
    ts_up   = high - atr_mult * atr_val
    ts_down = low  + atr_mult * atr_val
    
    var float trail_stop_long  = na
    var float trail_stop_short = na
    var int   pos              = 0   -- 1=bullish, -1=bearish
    
    if barstate.isfirst then
        trail_stop_long  = close
        trail_stop_short = close
        pos = 0
    else
        -- Previne NaN
        if na(trail_stop_long) then trail_stop_long := close end
        if na(trail_stop_short) then trail_stop_short := close end
        
        -- Lógica de trailing para longo
        long_stop = na(trail_stop_short) ? close : trail_stop_short
        if close > long_stop then
            trail_stop_long  := math.max(ts_up, nz(trail_stop_long))
            trail_stop_short := na
            pos := 1
        else
            trail_stop_long := na
        end
        
        -- Lógica de trailing para curto
        short_stop = na(trail_stop_long) ? close : trail_stop_long
        if close < short_stop then
            trail_stop_short := math.min(ts_down, nz(trail_stop_short))
            trail_stop_long  := na
            pos := -1
        else
            trail_stop_short := na
        end
    end
    
    return atr_val, pos, trail_stop_long, trail_stop_short
end

atr_val, trend_pos, stop_long, stop_short = atr_trailing_stop()

-- ====================================================================
-- SEÇÃO 3: CÁLCULO DO CROSSOVER DIFERENCIAL (tendência micro)
-- Estilo J25: SMA fast, SMA slow, WMA do sinal
-- ====================================================================
fast_ma   = ta.sma(close, fast_length)
slow_ma   = ta.sma(close, slow_length)
macd_line = fast_ma - slow_ma
signal    = ta.wma(macd_line, signal_length)
histogram = macd_line - signal

-- Geração de sinal bruto (antes do filtro de tendência)
raw_buy_signal  = ta.crossover(macd_line, signal)  -- cruza acima
raw_sell_signal = ta.crossunder(macd_line, signal) -- cruza abaixo

-- ====================================================================
-- SEÇÃO 4: NÍVEIS DE SUPORTE / RESISTÊNCIA (multi‑período)
-- Adaptado do SUPORTE_E_RESISTENCIA, corrigindo variáveis indefinidas
-- ====================================================================
levels = array.new<float>()

-- Calcula suportes e resistências baseados em máximos/mínimos
periods = {10, 30, 60, sr_lookback}
for i = 1, #periods do
    p = periods[i]
    high_level = ta.highest(high, p)
    low_level  = ta.lowest(low, p)
    array.push(levels, high_level)
    array.push(levels, low_level)
end

-- Função para verificar proximidade de nível
function is_near_level(price, level, tolerance)
    return math.abs(price - level) / price <= tolerance
end

-- Flag para sinal bloqueado por S/R
blocked_by_sr = false
for i = 1, array.size(levels) do
    level = array.get(levels, i)
    if is_near_level(high, level, sr_tolerance) and trend_pos == 1 then
        blocked_by_sr = true   -- resistência próxima → não comprar
    end
    if is_near_level(low, level, sr_tolerance) and trend_pos == -1 then
        blocked_by_sr = true   -- suporte próximo → não vender
    end
end

-- ====================================================================
-- SEÇÃO 5: LÓGICA DE SINAIS COM FILTROS DE TENDÊNCIA E ZONA
-- ====================================================================
buy_condition  = raw_buy_signal and (trend_pos == 1) and not blocked_by_sr
sell_condition = raw_sell_signal and (trend_pos == -1) and not blocked_by_sr

-- Gera setas de entrada
plotshape(buy_condition,  title="Sinal COMPRA", location=location.belowbar,
          style=shape.triangleup, size=size.small, color=color_bullish,
          text="ALPHA-C")
plotshape(sell_condition, title="Sinal VENDA",  location=location.abovebar,
          style=shape.triangledown, size=size.small, color=color_bearish,
          text="ALPHA-P")

-- ====================================================================
-- SEÇÃO 6: COLORAÇÃO DE CANDLES (Engulfing e tendência)
-- Inspirado no GENERAL_INDICADOR, sem strings obfuscadas
-- ====================================================================
-- Engulfing bullish: vela anterior baixista, atual alta e fecha acima do high anterior
engulfing_bull = close[1] < open[1] and close > open and close > high[1]
-- Engulfing bearish: vela anterior altista, atual baixa e fecha abaixo do low anterior
engulfing_bear = close[1] > open[1] and close < open and close < low[1]

-- Coloração baseada na direção do ATR (tendência)
candle_color = close >= open ? color_bullish : color_bearish
if trend_pos == 1 and close >= open then
    candle_color := color.new(color_bullish, 0)
elseif trend_pos == -1 and close < open then
    candle_color := color.new(color_bearish, 0)
elseif engulfing_bull then
    candle_color := color.new(color.yellow, 80)
elseif engulfing_bear then
    candle_color := color.new(color.orange, 80)
end
barcolor(candle_color)

-- ====================================================================
-- SEÇÃO 7: PLOTAGEM DE LINHAS AUXILIARES
-- ====================================================================
if show_sr_lines then
    for i = 1, #periods do
        p = periods[i]
        hi_line = ta.highest(high, p)
        lo_line = ta.lowest(low, p)
        plot(hi_line, title="Resistência "..tostring(p), color=color.new(color.gray, 80), linewidth=1)
        plot(lo_line, title="Suporte "..tostring(p),      color=color.new(color.gray, 80), linewidth=1)
    end
end

if show_atr_line then
    plot(stop_long,  title="ATR Stop Long",  color=color.new(color.green, 60), linewidth=2)
    plot(stop_short, title="ATR Stop Short", color=color.new(color.red, 60),   linewidth=2)
end

-- Exibe o valor do ATR no canto (opcional)
plot(atr_val, title="ATR", color=color.silver, linewidth=1, style=plot.style_line)

-- ====================================================================
-- FIM DO SCRIPT — JUSTICEIRO ALPHA v14
-- ====================================================================s