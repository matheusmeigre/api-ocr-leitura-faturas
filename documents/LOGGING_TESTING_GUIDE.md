# 🧪 Guia de Teste e Validação - Sistema de Logging

## 🚀 Instalação e Configuração

### 1. Instalar Dependências

```bash
# Instalar novas dependências de logging
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Crie ou atualize o arquivo `.env`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Logging Configuration (NOVO!)
LOG_LEVEL=INFO
LOG_FORMAT_JSON=true
LOG_INCLUDE_TIMESTAMP=true

# OCR Configuration
PADDLE_OCR_LANG=pt
PADDLE_OCR_USE_GPU=false
```

### 3. Iniciar a API

```bash
# Modo desenvolvimento (logs formatados para humanos)
LOG_FORMAT_JSON=false python main.py

# Modo produção (logs JSON)
python main.py

# Com uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Exemplos de Uso e Testes

### Teste 1: Upload de Fatura (Sucesso)

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@fatura_nubank.pdf" \
  -H "X-Trace-Id: test-001-nubank"
```

**Logs esperados:**

```json
{"timestamp": "2026-01-23T14:33:22.123Z", "level": "info", "event": "request_started", "method": "POST", "path": "/extract", "trace_id": "test-001-nubank"}
{"timestamp": "2026-01-23T14:33:22.234Z", "level": "info", "event": "request_start", "endpoint": "/extract", "file_name": "fatura_nubank.pdf", "file_size_mb": 2.45, "trace_id": "test-001-nubank"}
{"timestamp": "2026-01-23T14:33:22.567Z", "level": "info", "event": "pdf_detection", "pdf_type": "scanned", "confidence": 0.920, "trace_id": "test-001-nubank"}
{"timestamp": "2026-01-23T14:33:22.678Z", "level": "info", "event": "ocr_processing", "pdf_type": "scanned", "extraction_method": "paddleocr", "trace_id": "test-001-nubank"}
{"timestamp": "2026-01-23T14:33:24.234Z", "level": "info", "event": "ocr_result", "success": true, "text_length": 4523, "processing_time_ms": 824, "trace_id": "test-001-nubank"}
{"timestamp": "2026-01-23T14:33:24.345Z", "level": "info", "event": "bank_detection", "bank": "nubank", "confidence": 0.950, "trace_id": "test-001-nubank"}
{"timestamp": "2026-01-23T14:33:24.678Z", "level": "info", "event": "extraction_result", "document_type": "fatura_cartao", "confidence": 0.871, "bank_detected": "nubank", "trace_id": "test-001-nubank"}
{"timestamp": "2026-01-23T14:33:24.789Z", "level": "info", "event": "request_completed", "status_code": 200, "success": true, "processing_time_ms": 2567, "trace_id": "test-001-nubank"}
```

### Teste 2: Arquivo Inválido (Erro de Validação)

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@documento.txt" \
  -H "X-Trace-Id: test-002-invalid"
```

**Logs esperados:**

```json
{"timestamp": "2026-01-23T14:35:12.123Z", "level": "warning", "event": "validation_error", "validation_type": "format", "reason": "Apenas arquivos PDF são aceitos", "file_name": "documento.txt", "trace_id": "test-002-invalid"}
```

### Teste 3: Arquivo Muito Grande (Erro de Validação)

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@fatura_enorme.pdf" \
  -H "X-Trace-Id: test-003-large"
```

**Logs esperados:**

```json
{"timestamp": "2026-01-23T14:36:00.123Z", "level": "warning", "event": "validation_error", "validation_type": "size", "reason": "Arquivo excede o tamanho máximo de 10MB", "file_name": "fatura_enorme.pdf", "file_size_mb": 15.67, "trace_id": "test-003-large"}
```

### Teste 4: PDF Corrompido (Erro OCR)

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@corrupted.pdf" \
  -H "X-Trace-Id: test-004-corrupted"
```

**Logs esperados:**

```json
{"timestamp": "2026-01-23T14:36:45.123Z", "level": "error", "event": "ocr_result", "success": false, "error_message": "Erro ao extrair texto do PDF", "trace_id": "test-004-corrupted"}
{"timestamp": "2026-01-23T14:36:45.567Z", "level": "error", "event": "error", "error_type": "OCRExtractionError", "error_message": "Timeout na extração de texto", "trace_id": "test-004-corrupted"}
```

### Teste 5: Health Check (Sem Logs Detalhados)

```bash
curl http://localhost:8000/health
```

**Comportamento esperado:** Não gera logs detalhados (excluído pelo middleware)

## 🔍 Análise de Logs

### Buscar Logs por trace_id

```bash
# Ver todos os logs de uma requisição específica
cat api-ocr.log | jq 'select(.trace_id == "test-001-nubank")'

# Timeline de uma requisição
cat api-ocr.log | jq -s 'sort_by(.timestamp) | .[] | select(.trace_id == "test-001-nubank")'
```

### Filtrar por Evento

```bash
# Ver apenas OCR results
cat api-ocr.log | jq 'select(.event == "ocr_result")'

# Ver apenas erros
cat api-ocr.log | jq 'select(.level == "error")'

# Ver bancos detectados
cat api-ocr.log | jq 'select(.event == "bank_detection") | {bank, confidence}'
```

### Métricas de Performance

```bash
# Tempo médio de processamento
cat api-ocr.log | jq -s '[.[] | select(.event == "request_completed") | .processing_time_ms] | add/length'

# Requisições por segundo
cat api-ocr.log | jq -s '[.[] | select(.event == "request_started")] | length'

# Taxa de sucesso
cat api-ocr.log | jq -s '[.[] | select(.event == "request_completed")] | {total: length, success: [.[] | select(.success == true)] | length}'
```

### Análise de Erros

```bash
# Tipos de erros
cat api-ocr.log | jq -s '[.[] | select(.level == "error") | .error_type] | group_by(.) | map({type: .[0], count: length})'

# Erros por arquivo
cat api-ocr.log | jq -s '[.[] | select(.level == "error")] | group_by(.file_name) | map({file: .[0].file_name, errors: length})'
```

## 🧪 Testes Automatizados

### Script de Teste Básico

```python
# test_logging.py
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_logging_system():
    """Testa o sistema de logging completo"""
    
    print("🧪 Testando Sistema de Logging...")
    print("=" * 60)
    
    # Teste 1: Upload válido
    print("\n✅ Teste 1: Upload Válido")
    trace_id = f"test-{int(time.time())}-valid"
    
    with open("test_files/fatura_test.pdf", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/extract",
            files={"file": f},
            headers={"X-Trace-Id": trace_id}
        )
    
    print(f"Status: {response.status_code}")
    print(f"Trace ID: {trace_id}")
    print(f"Busque nos logs: grep '{trace_id}' api-ocr.log")
    
    # Teste 2: Arquivo inválido
    print("\n❌ Teste 2: Arquivo Inválido")
    trace_id = f"test-{int(time.time())}-invalid"
    
    response = requests.post(
        f"{BASE_URL}/extract",
        files={"file": ("test.txt", b"invalid content", "text/plain")},
        headers={"X-Trace-Id": trace_id}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Trace ID: {trace_id}")
    
    # Teste 3: Health check
    print("\n💚 Teste 3: Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos! Verifique os logs.")

if __name__ == "__main__":
    test_logging_system()
```

**Executar teste:**

```bash
python test_logging.py
```

## 📊 Dashboard de Monitoramento

### Usando Kibana (ELK Stack)

1. **Index Pattern:** `api-ocr-*`
2. **Visualizações sugeridas:**
   - Timeline de requisições
   - Distribuição de tipos de documento
   - Taxa de sucesso/erro
   - Tempo médio de processamento
   - Top arquivos problemáticos
   - Bancos mais detectados

### Queries Úteis no Kibana

```
# Requisições lentas (> 3 segundos)
event: "request_completed" AND processing_time_ms: >3000

# Erros de OCR
event: "error" AND error_type: "OCRExtractionError"

# Alta confiança
event: "extraction_result" AND confidence: >0.9

# Bancos detectados hoje
event: "bank_detection" AND @timestamp: [now-1d TO now]
```

## 🐛 Troubleshooting

### Logs não aparecem em JSON

**Problema:** Logs aparecem em formato texto ao invés de JSON

**Solução:**
```bash
# Verifique a variável de ambiente
echo $LOG_FORMAT_JSON

# Force JSON
export LOG_FORMAT_JSON=true
python main.py
```

### trace_id não aparece nos logs

**Problema:** Logs não contêm trace_id

**Solução:**
- Verifique se o middleware está configurado corretamente
- Confirme que `setup_logging_middleware(app)` foi chamado em main.py

### Logs muito verbosos

**Problema:** Muitos logs DEBUG

**Solução:**
```bash
# Ajuste o nível de log
export LOG_LEVEL=INFO
python main.py
```

### Dados sensíveis nos logs

**Problema:** CPF/CNPJ aparecem completos

**Solução:**
- Verifique se `sanitize_sensitive_data()` está sendo chamado
- Adicione campos personalizados à lista de sanitização

## ✅ Checklist de Validação

- [ ] Logs aparecem em formato JSON (quando configurado)
- [ ] Cada requisição tem um trace_id único
- [ ] Dados sensíveis são mascarados (CPF, CNPJ, etc)
- [ ] Tempo de processamento é registrado
- [ ] Erros contêm contexto suficiente
- [ ] Logs de OCR incluem confiança
- [ ] Detecção de banco é logada
- [ ] Métricas de performance são capturadas
- [ ] Health checks não poluem os logs
- [ ] Stack traces de erros são incluídos

## 📈 Próximos Passos

1. **Integrar com APM**: New Relic, Datadog, etc
2. **Alertas**: Configurar alertas para erros críticos
3. **Dashboards**: Criar painéis de monitoramento em tempo real
4. **Retenção**: Definir política de retenção de logs
5. **Backup**: Configurar backup automático de logs
6. **Análise ML**: Usar logs para treinar modelos de detecção de anomalias

---

**Sistema de logging pronto para produção! 🎉**
