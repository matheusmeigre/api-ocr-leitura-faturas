# 🔧 Correção de Timeout no Cliente TypeScript/Next.js

## 🎯 Problema Identificado

A primeira requisição de upload sempre falha com timeout porque:

1. **PaddleOCR Cold Start**: Na primeira vez, a API precisa:
   - Inicializar os modelos de ML do PaddleOCR (~200MB)
   - Carregar modelos na memória
   - Processar o PDF

2. **Timeout muito curto no cliente**: O cliente TypeScript está usando um timeout padrão muito baixo (geralmente 5-10 segundos)

3. **Segunda tentativa funciona**: Os modelos já estão carregados, processamento é rápido

---

## ✅ SOLUÇÕES IMPLEMENTADAS NA API

### 1. Pre-Warmup do PaddleOCR (✅ Implementado)

A API agora faz **warm-up automático** do PaddleOCR durante o startup:

```python
@app.on_event("startup")
async def startup_event():
    """Aquece PaddleOCR antes de receber requisições"""
    # Processa imagem dummy para forçar inicialização
    dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    _ = text_extractor.ocr.ocr(dummy_image, cls=False)
```

**Benefício**: Elimina cold start na primeira requisição de produção.

### 2. Endpoint de Health Check Detalhado (✅ Implementado)

Novo endpoint `/health/ready` indica quando a API está pronta para OCR:

```bash
GET /health/ready

# Resposta quando pronto:
{
  "status": "ready",
  "message": "API pronta para processar requisições OCR",
  "ocr_initialized": true
}

# Resposta quando ainda inicializando (status 503):
{
  "status": "not_ready",
  "message": "PaddleOCR ainda está inicializando..."
}
```