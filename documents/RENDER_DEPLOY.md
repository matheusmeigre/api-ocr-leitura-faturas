# Configuração específica para Render.com

## Build Command
```
pip install --upgrade pip && pip install -r requirements.txt
```

## Start Command
```
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

## Python Version
Python **3.11.11** (especificado em `runtime.txt`)

**IMPORTANTE:** No Render Dashboard, deixe o campo "Python Version" **VAZIO** para que ele use o runtime.txt automaticamente.

## Variáveis de Ambiente (Render Dashboard)

Configure as seguintes variáveis no Render:

```
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf
PADDLE_OCR_LANG=pt
PADDLE_OCR_USE_GPU=False
LOG_LEVEL=INFO
```

## Dependências do Sistema

O Render precisa de alguns pacotes do sistema. Adicione ao `render.yaml` ou configure no Render Dashboard:

```bash
apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    libgomp1
```

## Notas Importantes

1. **Python Version**: Usando 3.11.11 (compatível com todas as dependências)
2. **PaddlePaddle**: Versão 3.2.2 (mais recente)
3. **PaddleOCR**: Versão 2.9.2 (atualizada)
4. **Pillow**: Versão 11.1.0 (com wheels pré-compilados)
5. **opencv-python-headless**: Versão headless para ambientes sem GUI
6. **Workers**: Configure 2 workers para melhor performance
7. **Timeout**: Aumente o timeout para 300s para processar PDFs grandes

## Health Check

URL: `https://seu-app.onrender.com/health`

## Troubleshooting

### Erro de memória
- Aumente o plano no Render (mínimo 512MB recomendado)
- Reduza o MAX_FILE_SIZE_MB

### Timeout
- Aumente o timeout no Render para 300s
- Use instance type com mais CPU

### OCR não funciona
- Verifique se poppler-utils está instalado
- Verifique logs: os modelos do PaddleOCR são baixados na primeira execução
