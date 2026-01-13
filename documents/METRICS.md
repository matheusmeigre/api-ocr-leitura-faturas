# Sistema de Métricas - OCR Financeiro

## Visão Geral

O sistema de métricas (`ParserMetrics`) coleta dados em tempo real sobre o desempenho do parser financeiro, permitindo monitoramento e otimização contínua.

## Métricas Coletadas

### 1. Métricas Globais

- **total_requests**: Total de requisições processadas
- **successful_parses**: Parsings bem-sucedidos
- **failed_parses**: Parsings que falharam
- **success_rate**: Taxa de sucesso (0.0 a 1.0)

### 2. Métricas por Banco

Para cada banco detectado (Nubank, Inter, C6, PicPay, etc.):

- **total_requests**: Requisições para este banco
- **success_count**: Sucessos específicos
- **success_rate**: Taxa de sucesso (%)
- **fallback_rate**: Quão frequentemente usa parser genérico (%)
- **avg_confidence**: Confiança média da detecção (0.0 a 1.0)
- **avg_processing_time**: Tempo médio em segundos
- **most_extracted_fields**: Campos mais comuns extraídos

### 3. Métricas de Cache

- **hits**: Número de cache hits
- **misses**: Número de cache misses
- **total_requests**: Total de consultas ao cache
- **hit_rate**: Taxa de acerto do cache (%)

### 4. Uso de Parsers

- **specialized**: Uso de parsers especializados
- **generic**: Uso do parser genérico (fallback)

## Uso no Código

### Acessando Métricas

```python
from parsers.financial_parser import FinancialParser

parser = FinancialParser()

# Processar documentos...
parser.parse_financial_data(text1)
parser.parse_financial_data(text2)

# Obter resumo das métricas
summary = parser.get_metrics_summary()
print(summary)
```

### Exportando para JSON

```python
# Exporta métricas completas em JSON
json_metrics = parser.export_metrics_json()

# Salvar em arquivo
with open("metrics_report.json", "w") as f:
    f.write(json_metrics)
```

### Logging de Métricas

```python
# Loga resumo no logger estruturado
parser.log_metrics_summary()
```

### Reset de Métricas

```python
# Reseta todas as métricas
parser.reset_metrics()
```

## Exemplo de Output

```json
{
  "timestamp": "2025-01-15T10:30:45.123456",
  "total_requests": 150,
  "successful_parses": 148,
  "failed_parses": 2,
  "success_rate": 0.987,
  "by_bank": {
    "nubank": {
      "total_requests": 80,
      "success_count": 80,
      "success_rate": 1.0,
      "fallback_rate": 0.0,
      "avg_confidence": 0.95,
      "avg_processing_time": 0.123,
      "most_extracted_fields": [
        {"field": "empresa", "count": 80},
        {"field": "cnpj", "count": 80},
        {"field": "valor_total", "count": 78},
        {"field": "data_vencimento", "count": 75},
        {"field": "itens", "count": 80}
      ]
    },
    "inter": {
      "total_requests": 50,
      "success_count": 50,
      "success_rate": 1.0,
      "fallback_rate": 0.0,
      "avg_confidence": 0.92,
      "avg_processing_time": 0.110,
      "most_extracted_fields": [
        {"field": "empresa", "count": 50},
        {"field": "cnpj", "count": 50},
        {"field": "valor_total", "count": 48}
      ]
    }
  },
  "parser_usage": {
    "specialized": 130,
    "generic": 20
  },
  "cache_stats": {
    "hits": 45,
    "misses": 105,
    "total_requests": 150,
    "hit_rate": 0.30
  }
}
```

## Interpretação das Métricas

### Taxa de Sucesso por Banco

- **> 95%**: Excelente - Parser especializado funcionando bem
- **80-95%**: Bom - Pode haver espaço para melhorias
- **< 80%**: Crítico - Requer análise e ajustes

### Taxa de Fallback

- **< 5%**: Excelente - Parser especializado confiável
- **5-20%**: Aceitável - Alguns casos extremos
- **> 20%**: Problema - Parser pode não estar detectando corretamente

### Confiança Média

- **> 0.9**: Alta confiança na detecção
- **0.7-0.9**: Confiança média
- **< 0.7**: Baixa confiança - revisar padrões de detecção

### Cache Hit Rate

- **> 40%**: Excelente - Cache efetivo
- **20-40%**: Bom - Cache útil
- **< 20%**: Baixo - Documentos muito únicos ou TTL curto

## Casos de Uso

### 1. Dashboard de Monitoramento

Crie um endpoint para expor métricas:

```python
@app.get("/metrics")
async def get_metrics():
    return parser.get_metrics_summary()
```

### 2. Alertas Automáticos

```python
summary = parser.get_metrics_summary()

for bank, metrics in summary["by_bank"].items():
    if metrics["success_rate"] < 0.80:
        send_alert(f"Taxa de sucesso baixa para {bank}: {metrics['success_rate']}")
    
    if metrics["fallback_rate"] > 0.20:
        send_alert(f"Taxa de fallback alta para {bank}: {metrics['fallback_rate']}")
```

### 3. Relatórios Periódicos

```python
import schedule

def export_daily_metrics():
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"metrics_{timestamp}.json"
    
    with open(filename, "w") as f:
        f.write(parser.export_metrics_json())
    
    # Reset para próximo período
    parser.reset_metrics()

schedule.every().day.at("00:00").do(export_daily_metrics)
```

### 4. A/B Testing

```python
# Comparar desempenho de diferentes versões
parser_v1 = FinancialParser()
parser_v2 = FinancialParser()  # com novos parsers

# Processar mesmos docs
for doc in test_dataset:
    parser_v1.parse_financial_data(doc)
    parser_v2.parse_financial_data(doc)

# Comparar
metrics_v1 = parser_v1.get_metrics_summary()
metrics_v2 = parser_v2.get_metrics_summary()

print(f"V1 Success Rate: {metrics_v1['success_rate']}")
print(f"V2 Success Rate: {metrics_v2['success_rate']}")
```

## Integração com ONDA 3

As métricas coletadas serão essenciais para:

1. **Machine Learning (Sistema 7)**
   - Dados de treinamento para classificação
   - Validação de performance do modelo

2. **Feedback do Usuário (Sistema 8)**
   - Correlacionar feedback com métricas objetivas
   - Identificar casos problemáticos

3. **Templates Comunitários (Sistema 9)**
   - Avaliar eficácia de templates contribuídos
   - Priorizar melhorias baseado em dados

## Performance

O sistema de métricas é:

- **Leve**: Overhead < 1ms por requisição
- **Thread-safe**: Pode ser usado em ambientes concorrentes
- **Opcional**: Pode ser desabilitado se necessário

## Limitações Conhecidas

1. Métricas são voláteis (apenas em memória)
2. Não persiste entre reinicializações
3. Para análise histórica, usar exportação periódica

## Próximos Passos (ONDA 3)

- Persistência de métricas em banco de dados
- Visualização em dashboard web
- Integração com ferramentas de APM (Datadog, New Relic)
- Métricas de ML após implementação do Sistema 7
