# 📊 Sistema de Logging Estruturado - API OCR Leitura Faturas

## 🎯 Visão Geral

Sistema completo de **logging estruturado JSON** implementado para rastreabilidade, observabilidade e debugging de alta qualidade em toda a API de processamento OCR de faturas.

## 🏗️ Arquitetura

### Camada de Logging (Clean Architecture)

```
core/
├── __init__.py
└── logging/
    ├── __init__.py
    ├── structured_logger.py    # Logger estruturado com structlog
    └── middleware.py            # Middlewares FastAPI para logging automático
```

### Componentes Principais

1. **structured_logger.py** - Logger estruturado com:
   - Logging JSON usando `structlog`
   - Sanitização automática de dados sensíveis (CPF, CNPJ, senhas, tokens)
   - Funções helper especializadas para cada tipo de evento
   - Suporte a trace_id para rastreamento end-to-end
   - Context vars para propagação de contexto

2. **middleware.py** - Middlewares FastAPI:
   - `RequestLoggingMiddleware` - Intercepta todas as requisições HTTP
   - `FileUploadLoggingMiddleware` - Logging específico para uploads
   - Adiciona trace_id automaticamente
   - Mede tempo de processamento
   - Captura exceções não tratadas

## 📝 Funções Helper de Logging

### Configuração Inicial

```python
from core.logging.structured_logger import configure_logging

configure_logging(
    log_level="INFO",
    json_logs=True,
    include_timestamp=True
)
```

### Logging de Requisições

```python
from core.logging.structured_logger import (
    get_logger,
    add_trace_id_to_context,
    log_request_start,
    log_request_end
)

logger = get_logger(__name__)

# Gera trace_id único para rastreamento
trace_id = add_trace_id_to_context()

# Log de início
log_request_start(
    logger=logger,
    endpoint="/extract",
    method="POST",
    file_name="fatura.pdf",
    file_size_bytes=1048576
)

# Log de conclusão
log_request_end(
    logger=logger,
    endpoint="/extract",
    status_code=200,
    start_time=start_time,
    success=True,
    document_type="fatura_cartao"
)
```

### Logging de OCR

```python
from core.logging.structured_logger import (
    log_ocr_processing,
    log_ocr_result
)

# Log do início do OCR
log_ocr_processing(
    logger=logger,
    pdf_type="scanned",
    total_pages=3,
    method="paddleocr",
    confidence=0.92
)

# Log do resultado
log_ocr_result(
    logger=logger,
    success=True,
    text_length=4523,
    processing_time_ms=824,
    pages_processed=3,
    avg_confidence=0.89
)
```

### Logging de Extração de Dados

```python
from core.logging.structured_logger import log_extraction_result

log_extraction_result(
    logger=logger,
    document_type="fatura_cartao",
    fields_extracted={
        "empresa": "Banco XYZ",
        "valor_total": 1523.75,
        "vencimento": "2026-02-10"
    },
    confidence=0.87,
    bank_detected="nubank",
    parser_used="NubankParser"
)
```

### Logging de Erros

```python
from core.logging.structured_logger import log_error

log_error(
    logger=logger,
    error_type="OCRExtractionError",
    error_message="Timeout na extração",
    endpoint="/extract",
    file_name="fatura.pdf",
    stacktrace=traceback.format_exc()
)
```

## 🔐 Sanitização de Dados Sensíveis

O sistema **automaticamente mascara** dados sensíveis nos logs:

### Campos Mascarados Automaticamente

- CPF: `123.456.789-01` → `CPF:***.**.***.XX`
- CNPJ: `12.345.678/0001-90` → `CNPJ:**.***.***/****.XX`
- Senhas, tokens, API keys
- Números de conta bancária
- Chaves de autorização

### Uso Manual

```python
from core.logging.structured_logger import sanitize_sensitive_data

data = {
    "cpf": "123.456.789-01",
    "conta": "12345-6",
    "valor": 1000.00
}

sanitized = sanitize_sensitive_data(data)
# Resultado: {"cpf": "12*******01", "conta": "***MASKED***", "valor": 1000.00}
```

## 📊 Exemplos de Saída de Logs JSON

### 1. Requisição Iniciada

```json
{
  "timestamp": "2026-01-23T14:33:22.123Z",
  "level": "info",
  "event": "request_started",
  "method": "POST",
  "path": "/extract",
  "client_host": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "trace_id": "abc123-def456-ghi789"
}
```

### 2. Upload de Arquivo

```json
{
  "timestamp": "2026-01-23T14:33:22.234Z",
  "level": "info",
  "event": "request_start",
  "endpoint": "/extract",
  "method": "POST",
  "trace_id": "abc123-def456-ghi789",
  "file_name": "fatura_janeiro_2026.pdf",
  "file_size_mb": 2.45
}
```

### 3. Detecção de Tipo de PDF

```json
{
  "timestamp": "2026-01-23T14:33:22.567Z",
  "level": "info",
  "event": "pdf_detection",
  "pdf_type": "scanned",
  "confidence": 0.920,
  "detection_time_ms": 45,
  "file_name": "fatura_janeiro_2026.pdf",
  "trace_id": "abc123-def456-ghi789"
}
```

### 4. Processamento OCR

```json
{
  "timestamp": "2026-01-23T14:33:22.678Z",
  "level": "info",
  "event": "ocr_processing",
  "pdf_type": "scanned",
  "total_pages": 3,
  "extraction_method": "paddleocr",
  "detection_confidence": 0.920,
  "file_name": "fatura_janeiro_2026.pdf",
  "trace_id": "abc123-def456-ghi789"
}
```

### 5. Conversão PDF → Imagens

```json
{
  "timestamp": "2026-01-23T14:33:23.123Z",
  "level": "info",
  "event": "pdf_to_images",
  "total_pages": 3,
  "conversion_time_ms": 445,
  "trace_id": "abc123-def456-ghi789"
}
```

### 6. OCR por Página

```json
{
  "timestamp": "2026-01-23T14:33:23.456Z",
  "level": "debug",
  "event": "ocr_page_complete",
  "page_number": 1,
  "detections": 127,
  "avg_confidence": 0.891,
  "processing_time_ms": 234,
  "trace_id": "abc123-def456-ghi789"
}
```

### 7. Resultado do OCR Completo

```json
{
  "timestamp": "2026-01-23T14:33:24.234Z",
  "level": "info",
  "event": "ocr_result",
  "success": true,
  "text_length": 4523,
  "processing_time_ms": 824,
  "pages_processed": 3,
  "avg_confidence": 0.889,
  "file_name": "fatura_janeiro_2026.pdf",
  "trace_id": "abc123-def456-ghi789"
}
```

### 8. Detecção de Banco

```json
{
  "timestamp": "2026-01-23T14:33:24.345Z",
  "level": "info",
  "event": "bank_detection",
  "bank": "nubank",
  "confidence": 0.950,
  "detection_time_ms": 12,
  "trace_id": "abc123-def456-ghi789"
}
```

### 9. Seleção de Parser Especializado

```json
{
  "timestamp": "2026-01-23T14:33:24.456Z",
  "level": "info",
  "event": "parser_selection",
  "bank": "nubank",
  "parser": "NubankParser",
  "confidence": 0.950,
  "trace_id": "abc123-def456-ghi789"
}
```

### 10. Resultado da Extração (Dados Sanitizados!)

```json
{
  "timestamp": "2026-01-23T14:33:24.678Z",
  "level": "info",
  "event": "extraction_result",
  "document_type": "fatura_cartao",
  "confidence": 0.871,
  "fields_count": 8,
  "extracted_fields": {
    "empresa": "Banco Nubank",
    "cnpj": "CNPJ:**.***.***/****.XX",
    "valor_total": 1523.75,
    "vencimento": "2026-02-10",
    "numero_fatura": "2026-01-001234"
  },
  "bank_detected": "nubank",
  "parser_used": "NubankParser",
  "parsing_time_ms": 67,
  "file_name": "fatura_janeiro_2026.pdf",
  "trace_id": "abc123-def456-ghi789"
}
```

### 11. Requisição Concluída

```json
{
  "timestamp": "2026-01-23T14:33:24.789Z",
  "level": "info",
  "event": "request_end",
  "endpoint": "/extract",
  "status_code": 200,
  "success": true,
  "processing_time_ms": 2567,
  "document_type": "fatura_cartao",
  "file_name": "fatura_janeiro_2026.pdf",
  "overall_confidence": 0.871,
  "trace_id": "abc123-def456-ghi789"
}
```

### 12. Erro de Validação

```json
{
  "timestamp": "2026-01-23T14:35:12.123Z",
  "level": "warning",
  "event": "validation_error",
  "validation_type": "size",
  "reason": "Arquivo excede o tamanho máximo de 10MB",
  "file_name": "fatura_grande.pdf",
  "file_size_mb": 15.67,
  "trace_id": "xyz789-abc123-def456"
}
```

### 13. Erro no OCR

```json
{
  "timestamp": "2026-01-23T14:36:45.567Z",
  "level": "error",
  "event": "error",
  "error_type": "OCRExtractionError",
  "error_message": "Timeout na extração de texto",
  "endpoint": "/extract",
  "file_name": "fatura_corrompida.pdf",
  "trace_id": "mno456-pqr789-stu012"
}
```

## 🔍 Rastreamento End-to-End com trace_id

Todos os logs de uma mesma requisição compartilham o **mesmo trace_id**, permitindo rastreamento completo:

```bash
# Buscar todos os logs de uma requisição específica
cat logs.json | jq 'select(.trace_id == "abc123-def456-ghi789")'

# Ver timeline de processamento
cat logs.json | jq -s 'sort_by(.timestamp) | .[] | select(.trace_id == "abc123-def456-ghi789")'
```

## 📈 Integração com Ferramentas de Observabilidade

### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# logstash.conf
input {
  file {
    path => "/var/log/api-ocr/*.json"
    codec => json
  }
}

filter {
  if [trace_id] {
    mutate {
      add_tag => ["traced"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "api-ocr-%{+YYYY.MM.dd}"
  }
}
```

### Datadog

```python
# Adicione ao config.py
import datadog
from pythonjsonlogger import jsonlogger

handler = datadog.api.handler.DatadogLogHandler()
handler.setFormatter(jsonlogger.JsonFormatter())
```

### Grafana Loki

```yaml
# promtail.yaml
scrape_configs:
  - job_name: api-ocr
    static_configs:
      - targets:
          - localhost
        labels:
          job: api-ocr
          __path__: /var/log/api-ocr/*.json
    pipeline_stages:
      - json:
          expressions:
            trace_id: trace_id
            event: event
            level: level
```

## 🎛️ Configuração via Variáveis de Ambiente

Adicione ao `.env`:

```env
# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT_JSON=true
LOG_INCLUDE_TIMESTAMP=true
```

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar API com Logging

```python
# main.py já está configurado!
from core.logging.structured_logger import configure_logging
from core.logging.middleware import setup_logging_middleware

# Configuração automática no startup
configure_logging(
    log_level=settings.log_level,
    json_logs=settings.log_format_json,
    include_timestamp=settings.log_include_timestamp
)

# Middlewares já configurados
setup_logging_middleware(app)
```

### 3. Ver Logs em Tempo Real

```bash
# Logs formatados para humanos (desenvolvimento)
python main.py

# Logs JSON para produção (redirecionar para arquivo)
python main.py > logs/api-ocr.json 2>&1

# Filtrar por evento específico
python main.py | jq 'select(.event == "ocr_result")'

# Ver apenas erros
python main.py | jq 'select(.level == "error")'
```

## 📊 Métricas e KPIs Capturados

- ⏱️ **Tempo de processamento**: Total e por etapa (OCR, parsing, etc)
- 📄 **Taxa de sucesso**: % de extrações bem-sucedidas
- 🎯 **Confiança média**: OCR e detecção de documentos
- 🏦 **Bancos detectados**: Distribuição por banco
- 🔧 **Parsers utilizados**: Especializados vs genéricos
- 💾 **Cache hit rate**: Eficiência do cache
- ⚠️ **Erros por tipo**: Categorização de falhas

## ✅ Benefícios

1. **Rastreabilidade Completa** - trace_id em todos os logs
2. **Debugging Facilitado** - Contexto rico em cada log
3. **Segurança** - Sanitização automática de dados sensíveis
4. **Performance** - Métricas detalhadas de tempo
5. **Observabilidade** - Integração com ferramentas modernas
6. **Clean Code** - Separação clara de responsabilidades
7. **Produção-Ready** - JSON estruturado para parsing automatizado

## 📚 Referências

- [structlog Documentation](https://www.structlog.org/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/advanced/middleware/)
- [12-Factor App: Logs](https://12factor.net/logs)
- [OpenTelemetry Logging](https://opentelemetry.io/docs/specs/otel/logs/)

---

**Desenvolvido com ❤️ para observabilidade de classe mundial**
