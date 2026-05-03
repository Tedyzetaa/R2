#!/usr/bin/env python3
"""
Script de Teste Rápido para Visão do R2
Testa se o bot consegue "enxergar" e analisar a tela
"""
import asyncio
import logging
import sys

# Configurar logging para DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(name)s | %(levelname)s | %(message)s'
)

logger = logging.getLogger("TestVision")

async def test_vision():
    """Testa a percepção visual do AlphaEngine"""
    print("\n" + "="*60)
    print("👀 TESTE DE VISÃO DO R2")
    print("="*60)
    
    try:
        from alpha_module import alpha_engine
        logger.info("✅ Módulo AlphaEngine importado com sucesso")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar alpha_module: {e}")
        return {"status": "FAILED", "error": str(e)}
    
    # Verificar se página está anexada
    if not alpha_engine._active_page:
        logger.warning("⚠️  Nenhuma página Playwright anexada. Teste será limitado.")
        logger.info("💡 Dica: Certifique-se de que a página foi anexada via alpha_engine.attach(page)")
        return {"status": "NO_PAGE", "msg": "Página não anexada"}
    
    logger.info(f"✅ Página ativa detectada: {alpha_engine._active_page}")
    
    # Executar ciclo de percepção
    print("\n📊 Executando ciclo de percepção...")
    try:
        result = await alpha_engine.perceive_and_act()
        
        print("\n" + "="*60)
        print("📋 RESULTADO DO TESTE:")
        print("="*60)
        print(f"Estado: {result.get('state')}")
        print(f"Ação Recomendada: {result.get('recommended_action', result.get('msg'))}")
        print(f"Histórico de Velas: {len(alpha_engine.candle_history)}/{alpha_engine.config.analysis_window}")
        
        if alpha_engine.candle_history:
            print("\n📈 Últimas velas detectadas:")
            for i, candle in enumerate(alpha_engine.candle_history[-5:], 1):
                print(f"  {i}. Tipo: {candle.get('type')}")
        
        print("="*60)
        return {"status": "SUCCESS", "result": result}
        
    except Exception as e:
        logger.error(f"❌ Erro durante teste de visão: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}

async def test_ocr_debug():
    """Testa especificamente o OCR"""
    print("\n" + "="*60)
    print("🔍 TESTE DE OCR (DEBUG)")
    print("="*60)
    
    try:
        from alpha_module import alpha_engine
        import pytesseract
        from PIL import Image
        import io
        
        if not alpha_engine._active_page:
            logger.warning("⚠️  Nenhuma página para capturar screenshot")
            return
        
        logger.info("📸 Capturando screenshot...")
        screenshot_bytes = await asyncio.to_thread(
            alpha_engine._active_page.screenshot, 
            full_page=False
        )
        screenshot = Image.open(io.BytesIO(screenshot_bytes))
        logger.info(f"✅ Screenshot capturado: {screenshot.size[0]}x{screenshot.size[1]}px")
        
        # Tentar OCR
        logger.info("🔍 Executando OCR...")
        raw_text = await asyncio.to_thread(
            pytesseract.image_to_string, 
            screenshot, 
            config='--psm 11',
            lang='por+eng'
        )
        
        print("\n" + "="*60)
        print("📝 TEXTO LIDO PELO OCR:")
        print("="*60)
        print(raw_text[:200] if len(raw_text) > 0 else "(vazio)")
        print("="*60)
        
        # Procurar palavras-chave
        raw_upper = raw_text.upper()
        keywords = ['CALL', 'PUT', 'COMPRA', 'VENDA', 'ALTA', 'BAIXA']
        found_keywords = [kw for kw in keywords if kw in raw_upper]
        
        if found_keywords:
            print(f"\n✅ Palavras-chave encontradas: {', '.join(found_keywords)}")
        else:
            print("\n⚠️  Nenhuma palavra-chave típica encontrada")
            print("    Possível problema com Tesseract ou tela em branco")
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de OCR: {e}")
        import traceback
        traceback.print_exc()

async def test_tesseract_config():
    """Verifica configuração do Tesseract"""
    print("\n" + "="*60)
    print("⚙️  VERIFICAÇÃO DO TESSERACT")
    print("="*60)
    
    import os
    import shutil
    import pytesseract
    
    tesseract_path = os.environ.get("TESSERACT_PATH", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    
    print(f"Caminho configurado: {tesseract_path}")
    print(f"Arquivo existe: {'✅ SIM' if os.path.exists(tesseract_path) else '❌ NÃO'}")
    
    # Verificar no PATH
    which_result = shutil.which(tesseract_path)
    print(f"Encontrado no PATH: {'✅ SIM' if which_result else '❌ NÃO'}")
    
    # Tentar obter versão
    try:
        import subprocess
        result = subprocess.run([tesseract_path, '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"\n✅ Versão do Tesseract:")
            print(result.stdout.split('\n')[0])
        else:
            print(f"\n❌ Erro ao obter versão: {result.stderr}")
    except Exception as e:
        print(f"\n⚠️  Não foi possível obter versão: {e}")

async def main():
    """Executa todos os testes"""
    
    # Teste 1: Verificar Tesseract
    await test_tesseract_config()
    
    # Teste 2: Teste de visão principal
    vision_result = await test_vision()
    
    # Teste 3: Debug do OCR (se houver página)
    from alpha_module import alpha_engine
    if alpha_engine._active_page:
        await test_ocr_debug()
    
    print("\n" + "="*60)
    print("✨ TESTES CONCLUÍDOS")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Teste interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
