# 🔍 Checklist de Configuração do Tesseract

## 1. Verificar Instalação

### Windows
```powershell
# Verificar se o arquivo existe
Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe"

# Se sim, obter versão
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

**Resultado esperado:**
```
tesseract 5.x.x
...
```

### Se não encontrar:
```powershell
# Procurar alternativas
Get-ChildItem -Path "C:\Program Files*" -Filter "tesseract.exe" -Recurse
Get-ChildItem -Path "C:\Users\$env:USERNAME" -Filter "tesseract.exe" -Recurse
```

## 2. Configurar Variável de Ambiente

Se encontrou o Tesseract em um local diferente, configure:

```powershell
# PowerShell (temporário)
$env:TESSERACT_PATH = "C:\Seu\Caminho\tesseract.exe"

# PowerShell (permanente)
[Environment]::SetEnvironmentVariable("TESSERACT_PATH", "C:\Seu\Caminho\tesseract.exe", "User")
```

## 3. Verificar em Python

```python
import os
import pytesseract

tesseract_path = os.environ.get("TESSERACT_PATH", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
print(f"Caminho: {tesseract_path}")
print(f"Existe: {os.path.exists(tesseract_path)}")

# Se existir, configurar pytesseract
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print("✅ Tesseract configurado com sucesso")
else:
    print("❌ Tesseract não encontrado")
```

## 4. Testar OCR

```python
from PIL import Image
import pytesseract

# Tentar com uma imagem simples
img = Image.new('RGB', (100, 100), color='white')
text = pytesseract.image_to_string(img)
print(f"Teste OCR: {text}")
```

## 5. Logs de Debug no alpha_module.py

O módulo já está configurado com logs DEBUG. Para ver erros do Tesseract:

```python
# No seu código
import logging
logging.basicConfig(level=logging.DEBUG)

# Depois execute test_vision.py
```

## 📋 Possíveis Problemas

| Problema | Solução |
|----------|---------|
| "tesseract.exe not found" | Instale do https://github.com/UB-Mannheim/tesseract/wiki ou configure TESSERACT_PATH |
| OCR retorna vazio | Screenshot pode estar em branco ou WASM não carregou |
| Caracteres estranhos | Tente `lang='por'` ou `lang='eng'` só em alpha_module.py |
| Muito lento | Reduza `--psm` ou use `--oem 1` (mais rápido, menos preciso) |

## ✅ Verificação Final

```bash
# Para testar tudo:
python test_vision.py
```

Se passar, você terá:
- ✅ Tesseract funcionando
- ✅ Screenshot capturando corretamente  
- ✅ OCR lendo texto da tela
- ✅ Análise de pixels como fallback
- ✅ Histórico de velas sendo preenchido
