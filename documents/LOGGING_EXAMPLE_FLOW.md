# 📊 Exemplo de Fluxo Completo de Logs

## 🎬 Cenário: Upload e Processamento de Fatura do Nubank

Este documento mostra **exatamente** como os logs aparecem durante o processamento real de uma fatura.

---

## 📥 Requisição HTTP

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@fatura_nubank_janeiro_2026.pdf" \
  -H "X-Trace-Id: demo-001-nubank-jan2026"
```

---

## 📝 Logs Gerados (Timeline Completa)

### 1️⃣ Middleware - Requisição Iniciada (t=0ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.000Z",
  "level": "info",
  "event": "request_started",
  "method": "POST",
  "path": "/extract",
  "client_host": "192.168.1.100",
  "user_agent": "curl/7.81.0",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 2️⃣ Endpoint - Upload Recebido (t=12ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.012Z",
  "level": "info",
  "event": "request_start",
  "endpoint": "/extract",
  "method": "POST",
  "trace_id": "demo-001-nubank-jan2026",
  "file_name": "fatura_nubank_janeiro_2026.pdf",
  "file_size_mb": 2.45
}
```

### 3️⃣ PDF Detector - Tipo Detectado (t=67ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.067Z",
  "level": "info",
  "event": "pdf_detection",
  "pdf_type": "scanned",
  "confidence": 0.920,
  "detection_time_ms": 45,
  "file_name": "fatura_nubank_janeiro_2026.pdf",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 4️⃣ Text Extractor - OCR Iniciado (t=89ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.089Z",
  "level": "info",
  "event": "ocr_processing",
  "pdf_type": "scanned",
  "total_pages": 3,
  "extraction_method": "paddleocr",
  "detection_confidence": 0.920,
  "file_name": "fatura_nubank_janeiro_2026.pdf",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 5️⃣ Text Extractor - Início da Extração (t=95ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.095Z",
  "level": "info",
  "event": "text_extraction_start",
  "pdf_type": "scanned",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 6️⃣ Text Extractor - Scanning Iniciado (t=102ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.102Z",
  "level": "info",
  "event": "scanned_extraction_start",
  "method": "paddleocr",
  "dpi": 300,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 7️⃣ Text Extractor - PDF → Imagens (t=567ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.567Z",
  "level": "info",
  "event": "pdf_to_images",
  "total_pages": 3,
  "conversion_time_ms": 445,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 8️⃣ Text Extractor - Processando Página 1 (t=612ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.612Z",
  "level": "debug",
  "event": "ocr_page_start",
  "page_number": 1,
  "image_shape": [2480, 3508, 3],
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 9️⃣ Text Extractor - Página 1 Concluída (t=856ms)

```json
{
  "timestamp": "2026-01-23T14:33:22.856Z",
  "level": "debug",
  "event": "ocr_page_complete",
  "page_number": 1,
  "detections": 127,
  "avg_confidence": 0.891,
  "processing_time_ms": 244,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 🔟 Text Extractor - Página 2 Concluída (t=1098ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.098Z",
  "level": "debug",
  "event": "ocr_page_complete",
  "page_number": 2,
  "detections": 156,
  "avg_confidence": 0.904,
  "processing_time_ms": 242,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣1️⃣ Text Extractor - Página 3 Concluída (t=1334ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.334Z",
  "level": "debug",
  "event": "ocr_page_complete",
  "page_number": 3,
  "detections": 89,
  "avg_confidence": 0.867,
  "processing_time_ms": 236,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣2️⃣ Text Extractor - Scanning Completo (t=1367ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.367Z",
  "level": "info",
  "event": "scanned_extraction_complete",
  "total_pages": 3,
  "text_length": 4523,
  "total_detections": 372,
  "avg_confidence": 0.889,
  "processing_time_ms": 1265,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣3️⃣ Text Extractor - Extração Completa (t=1389ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.389Z",
  "level": "info",
  "event": "text_extraction_complete",
  "raw_text_length": 4523,
  "normalized_text_length": 4401,
  "normalization_time_ms": 12,
  "total_processing_time_ms": 1287,
  "extraction_method": "paddleocr",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣4️⃣ Endpoint - OCR Result (t=1401ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.401Z",
  "level": "info",
  "event": "ocr_result",
  "success": true,
  "text_length": 4401,
  "processing_time_ms": 1312,
  "pages_processed": 3,
  "avg_confidence": 0.889,
  "file_name": "fatura_nubank_janeiro_2026.pdf",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣5️⃣ Financial Parser - Detecção de Tipo (t=1423ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.423Z",
  "level": "info",
  "event": "document_detection_complete",
  "document_type": "fatura_cartao",
  "confidence": 0.867,
  "scores": {
    "boleto": 0,
    "fatura_cartao": 6,
    "nota_fiscal": 0,
    "extrato": 1
  },
  "processing_time_ms": 12,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣6️⃣ Endpoint - Tipo de Documento (t=1434ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.434Z",
  "level": "info",
  "event": "document_detection",
  "document_type": "fatura_cartao",
  "confidence": 0.867,
  "file_name": "fatura_nubank_janeiro_2026.pdf",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣7️⃣ Financial Parser - Parsing Iniciado (t=1445ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.445Z",
  "level": "info",
  "event": "parsing_start",
  "document_type": "fatura_cartao",
  "text_length": 4401,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣8️⃣ Financial Parser - Banco Detectado (t=1467ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.467Z",
  "level": "info",
  "event": "bank_detection",
  "bank": "nubank",
  "confidence": 0.950,
  "detection_time_ms": 12,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 1️⃣9️⃣ Financial Parser - Parser Selecionado (t=1478ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.478Z",
  "level": "info",
  "event": "parser_selection",
  "bank": "nubank",
  "parser": "NubankParser",
  "confidence": 0.950,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 2️⃣0️⃣ Financial Parser - Parsing Completo (t=1556ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.556Z",
  "level": "info",
  "event": "specialized_parsing_complete",
  "bank": "nubank",
  "parser": "NubankParser",
  "parsing_time_ms": 78,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 2️⃣1️⃣ Endpoint - Extração de Dados (t=1578ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.578Z",
  "level": "info",
  "event": "extraction_result",
  "document_type": "fatura_cartao",
  "confidence": 0.871,
  "fields_count": 12,
  "extracted_fields": {
    "empresa": "Banco Nubank",
    "cnpj": "CNPJ:**.***.***/****.XX",
    "valor_total": 1523.75,
    "vencimento": "2026-02-10",
    "numero_fatura": "2026-01-001234",
    "periodo_inicio": "2025-12-10",
    "periodo_fim": "2026-01-09",
    "limite_total": 5000.00,
    "limite_disponivel": 3476.25
  },
  "bank_detected": "nubank",
  "parser_used": "NubankParser",
  "parsing_time_ms": 133,
  "file_name": "fatura_nubank_janeiro_2026.pdf",
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 2️⃣2️⃣ Endpoint - Requisição Finalizada (t=1612ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.612Z",
  "level": "info",
  "event": "request_end",
  "endpoint": "/extract",
  "status_code": 200,
  "success": true,
  "processing_time_ms": 1600,
  "document_type": "fatura_cartao",
  "file_name": "fatura_nubank_janeiro_2026.pdf",
  "overall_confidence": 0.871,
  "trace_id": "demo-001-nubank-jan2026"
}
```

### 2️⃣3️⃣ Middleware - Requisição Completa (t=1623ms)

```json
{
  "timestamp": "2026-01-23T14:33:23.623Z",
  "level": "info",
  "event": "request_completed",
  "method": "POST",
  "path": "/extract",
  "status_code": 200,
  "processing_time_ms": 1623,
  "trace_id": "demo-001-nubank-jan2026"
}
```

---

## 📊 Análise do Fluxo

### ⏱️ Breakdown de Tempo

| Etapa | Tempo (ms) | % Total |
|-------|-----------|---------|
| PDF Detection | 45 | 2.8% |
| PDF → Images | 445 | 27.4% |
| OCR Processing | 722 | 44.5% |
| Text Normalization | 12 | 0.7% |
| Document Detection | 12 | 0.7% |
| Bank Detection | 12 | 0.7% |
| Data Parsing | 78 | 4.8% |
| Overhead | 297 | 18.4% |
| **TOTAL** | **1623ms** | **100%** |

### 🎯 Métricas Chave

- **Tempo Total**: 1.623 segundos
- **Confiança OCR**: 88.9%
- **Confiança Documento**: 86.7%
- **Confiança Banco**: 95.0%
- **Confiança Final**: 87.1%
- **Páginas Processadas**: 3
- **Detecções OCR**: 372
- **Campos Extraídos**: 12
- **Parser Usado**: NubankParser (especializado)

### 🔍 Observações

1. **OCR é o gargalo** (44.5% do tempo) - esperado para PDFs escaneados
2. **Conversão PDF→Imagens** também significativa (27.4%)
3. **Parsing muito rápido** (78ms) - parser especializado eficiente
4. **Alta confiança** em todas as etapas (>86%)
5. **Detecção de banco precisa** (95%) - uso do parser correto

### 🚀 Possíveis Otimizações

- Cache de conversão PDF→Imagens para uploads repetidos
- OCR paralelo de múltiplas páginas
- GPU acceleration para PaddleOCR
- Reduzir DPI para faturas pequenas (300 → 200)

---

## 🔎 Queries Úteis

### Buscar todos os logs desta requisição

```bash
cat api-ocr.log | jq 'select(.trace_id == "demo-001-nubank-jan2026")'
```

### Timeline visual

```bash
cat api-ocr.log | jq -s 'sort_by(.timestamp) | .[] | select(.trace_id == "demo-001-nubank-jan2026") | "\(.timestamp) | \(.event)"'
```

### Métricas de performance

```bash
cat api-ocr.log | jq 'select(.trace_id == "demo-001-nubank-jan2026" and .processing_time_ms) | {event, time_ms: .processing_time_ms}'
```

---

**Este é exatamente o tipo de visibilidade que o sistema de logging fornece! 🎉**
