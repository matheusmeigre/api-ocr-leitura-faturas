# ONDA 3 - Inteligência e Comunidade

## Status: ✅ 100% COMPLETO

Data de conclusão: Janeiro 2025  
Testes: 26/26 passando (100%)

---

## 🎯 Objetivo da ONDA 3

Adicionar **inteligência artificial** e **colaboração comunitária** ao sistema, permitindo:

1. **ML como Assistente**: Machine Learning auxilia na detecção quando regras básicas falham
2. **Aprendizado Contínuo**: Sistema aprende com correções dos usuários
3. **Templates Comunitários**: Comunidade contribui com novos parsers de forma segura

---

## 🧠 Sistema 7: ML para Classificação de Bancos

### Implementação

**Arquivo**: `parsers/utils/ml_classifier.py` (245 linhas)

### Filosofia: ML como ASSISTENTE, não SUBSTITUTO

- ML **só atua** quando confiança do detector baseado em regras < 0.70
- **Nunca substitui** detecção de alta confiança
- **Transparente**: sempre registra quando ML faz override

### Características

- **Feature Engineering**: Extrai 17 features do texto
  - Presença de palavras-chave específicas
  - Contadores (números de conta, CPF, CNPJ)
  - Formato (layouts conhecidos)
  
- **Modelo Simples**: Scoring baseado em features (sem sklearn em produção)
  - Evita dependências pesadas
  - Fácil de debugar
  - Rápido para treinar

- **Treinamento**: Aprende com feedback dos usuários
  - Mínimo 10 amostras por banco
  - Normalização com sigmoid
  - Modelo salvo em JSON

### API

```python
from parsers.utils.ml_classifier import MLBankClassifier

# Inicializar
ml = MLBankClassifier(model_path="ml_model.json")

# Extrair features (17 features)
features = ml.extract_features(text)

# Fazer predição
bank, confidence = ml.predict(text)

# Verificar se deve assistir (confiança < 0.70)
should_help = ml.should_assist(rule_confidence=0.60)

# Treinar com feedback
ml.train_from_feedback(feedback_samples)

# Informações do modelo
info = ml.get_model_info()
```

### Integração no FinancialParser

```python
# Em parse_financial_data (linhas 379-396)
if bank_detection and self.ml_classifier:
    _, _, rule_confidence = bank_detection
    if self.ml_classifier.should_assist(rule_confidence):
        ml_prediction = self.ml_classifier.predict(text)
        if ml_prediction:
            ml_bank, ml_confidence = ml_prediction
            if ml_confidence > rule_confidence:
                logger.info(f"ML override: {ml_bank}")
                bank_detection = (ml_bank, f"ML: {ml_bank}", ml_confidence)
```

### Testes

**Arquivo**: `tests/test_ml_classifier.py` (7 testes)

- ✅ Inicialização
- ✅ Extração de features (17 features)
- ✅ Treinamento com feedback (10 amostras)
- ✅ Predição após treinamento
- ✅ Lógica de threshold (should_assist)
- ✅ Validação de dados insuficientes
- ✅ Informações do modelo

---

## 💬 Sistema 8: Feedback do Usuário

### Implementação

**Arquivo**: `parsers/utils/feedback_system.py` (282 linhas)

### Objetivo

Coletar correções dos usuários para **melhorar continuamente** o sistema através de:
1. Armazenamento de correções
2. Identificação de casos problemáticos
3. Exportação de dados de treinamento

### Características

- **Banco de Dados**: SQLite com índices otimizados
  - Índice em `correct_bank` (buscar por banco)
  - Índice em `processed` (filtrar não processados)
  - Índice em `timestamp` (ordenação temporal)

- **Campos Armazenados**:
  - `detected_bank`: O que o sistema detectou
  - `correct_bank`: A correção do usuário
  - `text_sample`: Trecho do texto (primeiros 500 chars)
  - `confidence`: Confiança da detecção original
  - `extracted_data`: Dados extraídos (JSON)
  - `processed`: Se já foi usado para treinamento

- **Estatísticas**: Agregações por banco, confiança média, casos problemáticos

### API

```python
from parsers.utils.feedback_system import FeedbackSystem

# Inicializar
feedback = FeedbackSystem(db_path="feedback.db")

# Submeter correção
feedback.submit_feedback(
    detected_bank="inter",
    correct_bank="nubank",
    text_sample=text[:500],
    confidence=0.45,
    extracted_data={"valor": "100.00"}
)

# Obter feedback não processado
unprocessed = feedback.get_unprocessed_feedback()

# Marcar como processado (após retreinamento)
feedback.mark_as_processed(feedback_ids=[1, 2, 3])

# Estatísticas
stats = feedback.get_feedback_stats()
# {
#   "nubank": {"count": 15, "avg_confidence": 0.42},
#   "inter": {"count": 8, "avg_confidence": 0.55}
# }

# Casos problemáticos (confiança < 0.5)
problematic = feedback.get_problematic_cases(confidence_threshold=0.5)

# Exportar para JSON (usar em notebooks, análises)
feedback.export_training_data("training_data.json")
```

### Integração no FinancialParser

```python
# Novos métodos em FinancialParser:

# Submeter feedback
parser.submit_feedback(
    detected_bank="inter",
    correct_bank="nubank",
    text_sample=text[:500],
    confidence=0.45,
    extracted_data=result
)

# Retreinar ML com feedback acumulado
retrain_result = parser.retrain_ml_from_feedback()

# Estatísticas de feedback
stats = parser.get_feedback_stats()
```

### Testes

**Arquivo**: `tests/test_feedback_system.py` (8 testes)

- ✅ Inicialização do banco de dados
- ✅ Submissão de feedback
- ✅ Recuperação de feedback não processado
- ✅ Marcação como processado
- ✅ Estatísticas por banco
- ✅ Exportação para JSON
- ✅ Detecção de casos problemáticos
- ✅ Feedback com dados extraídos

---

## 🌐 Sistema 9: Templates Comunitários

### Implementação

**Arquivo**: `parsers/utils/community_templates.py` (370 linhas)

### Objetivo

Permitir que a **comunidade contribua** com novos parsers de bancos através de **configuração apenas** (sem código executável).

### Segurança em Primeiro Lugar

**Validações Rigorosas**:
1. ✅ Apenas regex (sem código Python)
2. ✅ Bloqueia palavras perigosas: `exec`, `eval`, `import`, `__`, `system`, `subprocess`
3. ✅ Valida sintaxe de regex
4. ✅ Valida formato de CNPJ
5. ✅ Apenas campos conhecidos permitidos
6. ✅ Workflow de aprovação (admin-only)

### Workflow

```
Usuário → Submit Template → Validação → Pendente → Admin Aprova → Template Ativo
```

### Campos do Template

```json
{
  "bank_key": "banco_exemplo",
  "bank_name": "Banco Exemplo S.A.",
  "cnpj": "12.345.678/0001-90",
  "detection_patterns": [
    "BANCO EXEMPLO",
    "banco-exemplo\\.com\\.br"
  ],
  "extraction_patterns": {
    "valor_total": "Total: R\\$ ([\\d.,]+)",
    "data_vencimento": "Vencimento: (\\d{2}/\\d{2}/\\d{4})",
    "numero_documento": "Documento: (\\d+)"
  },
  "author": "joao@example.com",
  "description": "Parser para faturas do Banco Exemplo"
}
```

### Campos de Extração Permitidos

- `empresa`: Nome da empresa
- `cnpj`: CNPJ do cliente
- `cpf`: CPF do cliente
- `data_emissao`: Data de emissão
- `data_vencimento`: Data de vencimento
- `valor_total`: Valor total
- `numero_documento`: Número do documento
- `items`: Lista de itens/transações

### API

```python
from parsers.utils.community_templates import CommunityTemplateSystem

# Inicializar
templates = CommunityTemplateSystem(templates_dir="community_templates")

# Submeter template (qualquer usuário)
result = templates.submit_template(
    bank_key="banco_exemplo",
    bank_name="Banco Exemplo S.A.",
    cnpj="12.345.678/0001-90",
    detection_patterns=["BANCO EXEMPLO"],
    extraction_patterns={"valor_total": r"Total: R\$ ([\d.,]+)"},
    author="joao@example.com",
    description="Parser para Banco Exemplo"
)

# Aprovar template (admin apenas)
templates.approve_template(template_hash, reviewer="admin")

# Listar templates
approved = templates.list_approved_templates()
pending = templates.list_pending_templates()

# Obter template específico
template = templates.get_template("banco_exemplo")

# Aplicar template (extrair dados)
data = templates.apply_template("banco_exemplo", text)
```

### Integração no FinancialParser

```python
# Novos métodos em FinancialParser:

# Submeter template comunitário
parser.submit_community_template(
    bank_key="banco_exemplo",
    bank_name="Banco Exemplo",
    cnpj="12.345.678/0001-90",
    detection_patterns=["BANCO EXEMPLO"],
    extraction_patterns={"valor_total": r"Total: ([\d.,]+)"},
    author="joao@example.com"
)

# Aprovar template (admin)
parser.approve_community_template(template_hash, reviewer="admin")

# Listar templates
templates = parser.list_community_templates(status="approved")
```

### Testes

**Arquivo**: `tests/test_community_templates.py` (11 testes)

- ✅ Inicialização
- ✅ Submissão de template válido
- ✅ Rejeição: bank_key inválido (INVALID-KEY!)
- ✅ Rejeição: CNPJ inválido
- ✅ Rejeição: regex malformado
- ✅ Rejeição: padrão perigoso (`exec('code')`)
- ✅ Rejeição: campo desconhecido
- ✅ Aprovação de template
- ✅ Listagem de templates aprovados
- ✅ Listagem de templates pendentes
- ✅ Aplicação de template (extração de dados)

---

## 📊 Resultados

### Cobertura de Testes

```
ONDA 3: 26 testes
├── Sistema 7 (ML): 7 testes ✅
├── Sistema 8 (Feedback): 8 testes ✅
└── Sistema 9 (Templates): 11 testes ✅

Total do Projeto: 74 testes (100% passando)
```

### Arquivos Criados

```
parsers/utils/
├── ml_classifier.py          (245 linhas)
├── feedback_system.py        (282 linhas)
└── community_templates.py    (370 linhas)

tests/
├── test_ml_classifier.py     (123 linhas)
├── test_feedback_system.py   (140 linhas)
└── test_community_templates.py (186 linhas)

Total: 1.346 linhas de código
```

### Arquivos Modificados

- `parsers/financial_parser.py`:
  - Imports dos novos sistemas
  - Inicialização no `__init__()`
  - Integração ML em `parse_financial_data()` (linhas 379-396)
  - 8 novos métodos de API (linhas 661-835)

---

## 🔄 Ciclo de Aprendizado Contínuo

```
1. Sistema detecta banco (BankDetector)
   ↓
2. Se confiança < 0.70 → ML tenta ajudar
   ↓
3. Usuário corrige (via API de feedback)
   ↓
4. Feedback armazenado (SQLite)
   ↓
5. Admin retreina ML com feedback
   ↓
6. ML melhora → menos erros
   ↓
7. Volta para (1)
```

---

## 🎓 Exemplos de Uso

### 1. Usar ML para Detecção

```python
from parsers.financial_parser import FinancialParser

parser = FinancialParser(
    enable_ml=True,  # Ativa ML
    ml_model_path="ml_model.json"
)

# Parse com ML assistindo
result = parser.parse_financial_data(text)

# Se confiança do BankDetector < 0.70, ML pode fazer override
```

### 2. Submeter Correção

```python
# Usuário detectou erro
result = parser.parse_financial_data(text)
detected = result.get('banco', 'unknown')

# Usuário corrige
parser.submit_feedback(
    detected_bank=detected,
    correct_bank="nubank",
    text_sample=text[:500],
    confidence=result.get('confidence', 0.0),
    extracted_data=result
)
```

### 3. Retreinar ML

```python
# Admin retreina com feedback acumulado
result = parser.retrain_ml_from_feedback()

print(f"ML retreinado com {result['samples_used']} amostras")
print(f"Bancos no modelo: {result['banks']}")
```

### 4. Contribuir Template

```python
# Usuário contribui parser para novo banco
result = parser.submit_community_template(
    bank_key="btg",
    bank_name="Banco BTG Pactual",
    cnpj="30.306.294/0001-45",
    detection_patterns=[
        "BTG PACTUAL",
        "btgpactual\\.com"
    ],
    extraction_patterns={
        "valor_total": r"Valor Total: R\$ ([\d.,]+)",
        "data_vencimento": r"Vencimento: (\d{2}/\d{2}/\d{4})"
    },
    author="maria@example.com",
    description="Parser para cartão BTG Pactual"
)

# Admin revisa e aprova
parser.approve_community_template(
    template_hash=result['template_id'],
    reviewer="admin@company.com"
)
```

---

## 🔒 Segurança

### Templates Comunitários

**Princípio**: Never Trust User Input

1. **Apenas Regex**: Nenhum código Python executável
2. **Whitelist de Campos**: Apenas campos conhecidos
3. **Validação de Regex**: Sintaxe verificada antes de aceitar
4. **Blacklist de Palavras**: exec, eval, import, __, system, subprocess
5. **Workflow de Aprovação**: Admin deve revisar antes de ativar
6. **Isolamento**: Templates em diretórios separados (pending/approved)

### Feedback System

- Dados sanitizados antes de armazenar
- Text samples limitados a 500 caracteres
- SQLite com prepared statements (previne SQL injection)
- Sem exposição direta do banco de dados

### ML Classifier

- Modelo serializado em JSON (não pickle - segurança)
- Sem execução de código arbitrário
- Features extraídas de forma determinística

---

## 📈 Métricas e Monitoramento

### ML

```python
info = parser.get_ml_model_info()
# {
#   "trained": True,
#   "banks": ["nubank", "inter", "c6"],
#   "samples_per_bank": {
#     "nubank": 15,
#     "inter": 12,
#     "c6": 10
#   },
#   "last_trained": "2025-01-15T14:30:00"
# }
```

### Feedback

```python
stats = parser.get_feedback_stats()
# {
#   "nubank": {
#     "count": 15,
#     "avg_confidence": 0.42
#   },
#   "inter": {
#     "count": 8,
#     "avg_confidence": 0.55
#   }
# }
```

### Templates

```python
approved = parser.list_community_templates(status="approved")
# [
#   {
#     "bank_key": "btg",
#     "bank_name": "Banco BTG Pactual",
#     "author": "maria@example.com",
#     "approved_at": "2025-01-10T10:00:00"
#   }
# ]
```

---

## 🎯 Próximos Passos

A ONDA 3 está **100% completa**. Todas as 3 ondas da arquitetura estão implementadas:

- ✅ **ONDA 1**: Fundação e Parsers Básicos
- ✅ **ONDA 2**: Performance e Escala
- ✅ **ONDA 3**: Inteligência e Comunidade

### Sugestões para Evolução

1. **Dashboard de Feedback**: Visualizar estatísticas de correções
2. **Auto-Retraining**: Retreinamento automático quando acumular N feedbacks
3. **Template Marketplace**: Interface web para submissão de templates
4. **ML Avançado**: Considerar modelos mais sofisticados (spaCy, transformers) se necessário
5. **A/B Testing**: Comparar performance com/sem ML

---

## 📚 Referências

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Arquitetura completa do projeto
- [ONDA_1_RESUMO.md](./ONDA_1_RESUMO.md) - Sistemas 1-3
- [ONDA_2_RESUMO.md](./ONDA_2_RESUMO.md) - Sistemas 4-6
- [EXAMPLES.md](../EXAMPLES.md) - Exemplos de uso da API

---

**ONDA 3: Inteligência e Comunidade - 100% Implementado** ✅

*"O sistema agora aprende e evolui com a comunidade"*
