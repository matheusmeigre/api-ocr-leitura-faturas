# OCR Financeiro — Arquitetura, Evolução e Padrões

Este documento define diretrizes técnicas obrigatórias para a evolução do sistema de OCR financeiro, com foco em precisão, escalabilidade e extensibilidade, mantendo compatibilidade com versões anteriores.

O sistema já utiliza uma arquitetura híbrida baseada em parsers especializados por banco, com fallback genérico e detecção automática.

## 🎯 Objetivo do Sistema

Extrair dados financeiros estruturados de faturas bancárias (PDFs), com:

- Alta precisão por banco
- Tolerância a formatos variados
- Evolução incremental sem quebra
- Observabilidade e métricas claras
- Base preparada para ML e comunidade

## 🧠 Arquitetura Atual (Resumo)

```
PDF
 ├─ OCR / Texto bruto
 ↓
BankDetector
 ↓
Parser Especializado (se existir)
 ↓ (fallback)
Parser Genérico
 ↓
Normalização
 ↓
JSON Financeiro
```

### Componentes-chave

- **FinancialParser** → Orquestrador
- **BankDetector** → Identificação do banco
- **DateParser** → Datas flexíveis (ex: "17 OUT")
- **CNPJDatabase** → Enriquecimento automático
- **Parsers por banco** (ex: NubankParser)

---

## 🟢 PRIMEIRA ONDA — Robustez e Confiabilidade
### ✅ STATUS: 100% COMPLETO

### 🎯 Objetivo
Aumentar observabilidade, cobertura bancária inicial e segurança de regressão.

### 1️⃣ Logs de rastreamento de parser

#### Requisitos obrigatórios

Logar qual parser foi utilizado:
- Especializado
- Genérico (fallback)

Logar:
- Banco detectado
- Score de confiança
- Motivo do fallback (se aplicável)

#### Padrão de log sugerido
```json
{
  "event": "parser_selection",
  "bank": "nubank",
  "parser": "NubankParser",
  "confidence": 0.92,
  "fallback": false
}
```

📌 **Logs devem ser estruturados e prontos para observabilidade futura.**

---

### 2️⃣ Implementar Parser do Banco Inter

#### Diretrizes

- Criar `inter_parser.py`
- **NÃO duplicar lógica genérica**
- Reutilizar:
  - DateParser
  - CNPJDatabase
- Tratar:
  - Datas abreviadas
  - Parcelas
  - Layouts multiline

#### Obrigatório

Parser deve declarar:
```python
SUPPORTED_BANK = "inter"
```

---

### 3️⃣ Testes automatizados

#### Tipos de testes

**Unitários:**
- DateParser
- BankDetector
- Parsers especializados

**Integração:**
- Texto real de faturas (anonimizado)

#### Regras

- Todo novo parser **exige testes**
- Nenhuma PR sem testes passa

---

## 🟡 SEGUNDA ONDA — Performance e Escala
### ✅ STATUS: 100% COMPLETO

### 🎯 Objetivo
Reduzir custo computacional, aumentar cobertura e criar visibilidade operacional.

### 4️⃣ Sistema de cache de detecção

#### Motivação

- Bank detection é determinística
- OCR + parsing é caro

#### Diretriz

Cachear:
- Hash do texto → banco detectado
- Hash → parser escolhido

Exemplo:
```python
SHA256(text) → nubank_parser
```

📌 **Cache deve ser:**
- Opcional
- Desativável
- Transparente ao fluxo

---

### 5️⃣ Parsers para C6 Bank e PicPay

#### Regras

- Um parser por banco
- **Nunca criar "parser genérico bancário"**
- Priorizar precisão, não cobertura artificial

#### Arquivos esperados:
- `c6_parser.py`
- `picpay_parser.py`

---

### 6️⃣ Dashboard de métricas

#### Métricas mínimas

- Taxa de sucesso por banco
- Parser mais usado
- Fallback rate
- Confidence médio
- Tempo médio de processamento

📌 **Métricas devem ser pensadas desde o código (instrumentação).**

---

## 🔵 TERCEIRA ONDA — Inteligência e Comunidade
### ✅ STATUS: 100% COMPLETO

### 🎯 Objetivo
Permitir evolução automática, aprendizado contínuo e ecossistema.

### 7️⃣ Machine Learning para novos formatos
#### ✅ IMPLEMENTADO
**Arquivo**: `parsers/utils/ml_classifier.py`

#### Diretriz clara

- **ML NÃO substitui parsers** ✅
- ML entra apenas para:
  - Classificação ✅
  - Sugestão de parser ✅
  - Detecção de layout desconhecido ✅

**Implementação**:
- MLBankClassifier com 17 features
- Ativação apenas quando confiança < 0.70
- Treinamento com feedback dos usuários
- Modelo salvo em JSON (não pickle)

📌 **Parser especializado continua sendo a fonte de verdade.**

---

### 8️⃣ Sistema de feedback do usuário
#### ✅ IMPLEMENTADO
**Arquivo**: `parsers/utils/feedback_system.py`

#### Conceito

Usuário corrige:
- Datas ✅
- Valores ✅
- Itens ✅

Sistema deve:
- Registrar correções ✅
- Associar ao banco + layout ✅
- Alimentar métricas e ML ✅

**Implementação**:
- Banco SQLite com índices otimizados
- API de feedback completa
- Estatísticas por banco
- Exportação de dados de treinamento
- Detecção de casos problemáticos

📌 **Feedback humano = ativo estratégico.**

---

### 9️⃣ API pública de templates da comunidade
#### ✅ IMPLEMENTADO
**Arquivo**: `parsers/utils/community_templates.py`

#### Visão

Criar um ecossistema onde:
- Desenvolvedores contribuem templates ✅
- Parsers comunitários são versionados ✅
- Sistema escolhe automaticamente ✅

#### Regras

- Templates **nunca executam código** ✅
- Apenas configuração + regex + layout ✅
- Validação obrigatória ✅

**Implementação**:
- Validação de segurança (bloqueia exec, eval, import, etc)
- Workflow de aprovação (admin-only)
- Aplicação de templates via regex
- Diretórios separados (pending/approved)

**Documentação**: Ver [ONDA_3_RESUMO.md](./ONDA_3_RESUMO.md) para detalhes completos.

---

## 🧱 Princípios Não-Negociáveis

❌ **Nunca quebrar compatibilidade**

❌ **Nunca confiar cegamente no OCR**

✅ **Especialização > generalização**

✅ **Logs antes de ML**

✅ **Humano no loop sempre**

---

## 🏁 Encerramento

**Este sistema não é apenas OCR.**
Ele é um motor financeiro inteligente, construído para evoluir com segurança, precisão e comunidade.

**Qualquer IA ou desenvolvedor que trabalhe neste código deve seguir este guideline integralmente.**

---

## 🎉 TODAS AS ONDAS COMPLETAS

### ✅ Status do Projeto: 100% Implementado

**ONDA 1** (Robustez e Confiabilidade): ✅ COMPLETO
- Sistema 1: Logs de rastreamento
- Sistema 2: Parser do Banco Inter
- Sistema 3: Testes automatizados

**ONDA 2** (Performance e Escala): ✅ COMPLETO
- Sistema 4: Cache de detecção
- Sistema 5: Parsers C6 Bank e PicPay
- Sistema 6: Dashboard de métricas

**ONDA 3** (Inteligência e Comunidade): ✅ COMPLETO
- Sistema 7: ML para classificação (assistente)
- Sistema 8: Sistema de feedback
- Sistema 9: Templates comunitários

### 📊 Números Finais

- **9 Sistemas**: Todos implementados e testados
- **74 Testes**: 100% passando
- **5 Parsers Bancários**: Nubank, Inter, C6, PicPay + Genérico
- **3 Sistemas de IA**: ML, Feedback, Templates Comunitários

### 📚 Documentação Completa

- [ONDA_1_RESUMO.md](./ONDA_1_RESUMO.md) - Sistemas 1-3
- [ONDA_2_RESUMO.md](./ONDA_2_RESUMO.md) - Sistemas 4-6
- [ONDA_3_RESUMO.md](./ONDA_3_RESUMO.md) - Sistemas 7-9

**O sistema está pronto para produção e evolução contínua.** 🚀
