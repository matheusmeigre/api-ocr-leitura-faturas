# 🔧 Guia de Troubleshooting - Render Deploy

## ✅ Correções Aplicadas

### 1. Versão do PaddlePaddle
❌ **Erro anterior:** `paddlepaddle==2.6.0` (versão não disponível)  
✅ **Correção:** `paddlepaddle==3.2.2` (versão atual e compatível)

### 2. OpenCV
❌ **Erro anterior:** `opencv-python` (requer GUI)  
✅ **Correção:** `opencv-python-headless` (para servidores)

### 3. Camelot removido
❌ **Problema:** Camelot tem muitas dependências complexas  
✅ **Solução:** Removido, tabelas são extraídas via pdfplumber

## 🚀 Passos para Deploy no Render

### 1. Commit e Push das Correções

```bash
git add .
git commit -m "fix: atualiza dependências para compatibilidade com Render"
git push origin main
```

### 2. Configure o Render

No Render Dashboard:

1. **New** → **Web Service**
2. **Connect Repository**: Selecione seu repo GitHub
3. **Settings**:
   - Name: `api-ocr-leitura-faturas`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2`

### 3. Variáveis de Ambiente

Adicione no Render:

```
API_HOST=0.0.0.0
API_DEBUG=False
MAX_FILE_SIZE_MB=10
PADDLE_OCR_LANG=pt
PADDLE_OCR_USE_GPU=False
LOG_LEVEL=INFO
```

### 4. Configurações Avançadas

- **Python Version**: Deixe em branco (usa runtime.txt automaticamente)
- **Health Check Path**: `/health`
- **Auto-Deploy**: Yes (deploy automático no push)

### 5. Plano Recomendado

- **Starter** ($7/mês): 512MB RAM - Suficiente para a maioria dos PDFs
- **Standard** ($25/mês): 2GB RAM - Recomendado para PDFs grandes

## 🐛 Erros Comuns e Soluções

### Erro 1: "ModuleNotFoundError: No module named 'paddleocr'"

**Causa:** Dependências não instaladas corretamente

**Solução:**
```bash
# Verifique o Build Log no Render
# Se falhou, tente:
# 1. Clear Build Cache no Render
# 2. Manual Deploy
```

### Erro 2: "Memory exceeded"

**Causa:** PDF muito grande ou RAM insuficiente

**Solução:**
- Aumente o plano para Standard (2GB)
- Ou reduza MAX_FILE_SIZE_MB para 5

### Erro 3: "Request timeout"

**Causa:** OCR demora muito em PDFs grandes

**Solução:**
No Render Dashboard → Settings → Advanced:
- HTTP Request Timeout: 300 segundos

### Erro 4: "libGL.so.1: cannot open shared object file"

**Causa:** Dependências do sistema não instaladas

**Solução:**
Isso NÃO deve acontecer mais porque usamos `opencv-python-headless`.
Se acontecer, adicione no Build Command:
```
apt-get update && apt-get install -y libgl1-mesa-glx && pip install -r requirements.txt
```

### Erro 5: "Cannot find poppler"

**Causa:** Poppler não está instalado

**Solução:**
No Render, poppler-utils já vem instalado. Se der erro:

Build Command:
```
apt-get update && apt-get install -y poppler-utils && pip install -r requirements.txt
```

### Erro 6: Build muito lento

**Causa:** PaddleOCR baixa modelos grandes

**Solução:**
- Normal na primeira vez (~5-10 minutos)
- Próximos deploys são mais rápidos (cache)

## ✅ Checklist Pós-Deploy

Depois do deploy, teste:

```bash
# 1. Health check
curl https://seu-app.onrender.com/health

# Resposta esperada:
# {"status":"healthy","service":"api-ocr-leitura-faturas"}

# 2. Documentação
curl https://seu-app.onrender.com/docs
# Deve abrir Swagger UI

# 3. Upload de teste
curl -X POST "https://seu-app.onrender.com/extract" \
  -F "file=@test.pdf"
```

## 📊 Monitoramento

### Logs

No Render Dashboard → Logs, procure por:

✅ **Sucesso:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

❌ **Erro:**
```
ModuleNotFoundError
ImportError
ERROR
```

### Métricas

Render mostra automaticamente:
- CPU Usage
- Memory Usage
- Request Count
- Response Time

## 🔄 Redeploy

Se precisar fazer redeploy:

1. **Manual:** Render Dashboard → Manual Deploy
2. **Automático:** Faça push para `main`
3. **Clear Cache:** Settings → Clear Build Cache (se dependências mudaram)

## 🆘 Ainda com Problemas?

### Verifique os Arquivos

Certifique-se de que estes arquivos existem:

- ✅ [requirements.txt](requirements.txt) - Dependências atualizadas
- ✅ [runtime.txt](runtime.txt) - Python 3.10.12
- ✅ [Procfile](Procfile) - Comando de start
- ✅ [render.yaml](render.yaml) - Configuração automática

### Teste Local Antes

```bash
# Instale as dependências atualizadas
pip install -r requirements.txt

# Teste local
uvicorn main:app --host 0.0.0.0 --port 8000

# Se funcionar local, funcionará no Render
```

### Suporte Render

- Documentação: https://render.com/docs
- Status: https://status.render.com
- Community: https://community.render.com

## 📝 Comandos Úteis

### Build Local (simula Render)

```bash
# Cria ambiente limpo
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
test_env\Scripts\activate     # Windows

# Instala exatamente como Render
pip install -r requirements.txt

# Testa
python -c "import paddleocr; print('OK')"
python -c "import cv2; print('OK')"

# Inicia
uvicorn main:app --port 8000
```

### Verificar Versões

```bash
pip list | grep paddle
pip list | grep opencv
pip list | grep fastapi
```

## 🎯 Próximos Passos

Depois que o deploy funcionar:

1. ✅ Configure domínio customizado (opcional)
2. ✅ Configure variáveis de ambiente de produção
3. ✅ Monitore logs e métricas
4. ✅ Configure alertas (Render Pro)
5. ✅ Teste carga com vários PDFs

---

**Última atualização:** 10 de Janeiro de 2026

**Status:** ✅ Correções aplicadas, pronto para deploy!
