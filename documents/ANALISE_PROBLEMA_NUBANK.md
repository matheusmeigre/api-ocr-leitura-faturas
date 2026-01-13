# Análise do Problema: Fatura Nubank

## Data da Análise
12 de Janeiro de 2026

## Problema Reportado
O usuário tentou importar uma fatura do Nubank (Nubank_2025-11-24.pdf) e recebeu os seguintes erros:

```
• Resposta da API OCR está em formato inválido
• data.cnpj: Expected string, received null
• data.itens.0.data: Expected string, received null
• data.itens.1.data: Expected string, received null
... (todos os 19 itens sem data)
```

## Diagnóstico Detalhado

### 1. Estrutura da Fatura do Nubank

A fatura do Nubank tem características únicas:

#### Formato de Datas
- **Formato encontrado**: "17 OUT", "18 OUT", "24 NOV" (dia + mês abreviado)
- **Formato esperado pelo sistema**: "DD/MM/YYYY" ou "DD-MM-YYYY"
- **Impacto**: O parser não reconhece esse formato de data

#### Ausência de CNPJ
- **Observação**: A fatura do Nubank **não exibe CNPJ visível**
- **Motivo**: Comum em fintechs modernas que priorizam design minimalista
- **CNPJ do Nubank**: 18.236.120/0001-58 (conhecido, mas não aparece no documento)
- **Impacto**: Campo obrigatório vem como null

#### Formato dos Itens de Transação
```
17 OUT
 •••• 2300 Moreira Vidracaria - Parcela 2/3 R$ 250,00
```
- A data está **separada** da descrição
- O parser atual busca data e valor na mesma linha
- **Resultado**: Itens extraídos sem data

### 2. Problemas Identificados no Parser Atual

#### A. Padrões de Data Limitados
```python
"data": r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',
```
- Só reconhece formato DD/MM/YYYY ou DD-MM-YYYY
- **Não reconhece**: "17 OUT", "24 NOV", etc.

#### B. Extração de Itens Simplificada
```python
pattern = r'(.+?)\s+R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))'
```
- Busca descrição + valor na mesma linha
- **Não captura**: Data em linha separada

#### C. Validação Estrita
- Modelo Pydantic exige `cnpj: str` quando deveria ser `Optional[str]`
- Modelo ItemFinanceiro permite `data: Optional[str]`, mas o problema é na extração

## Análise: Templates por Banco

### Cenário 1: Parser Genérico Melhorado
**Prós:**
- Mantém código simples
- Funciona para múltiplos formatos
- Fácil manutenção

**Contras:**
- Pode não capturar todas as nuances
- Precisão pode variar entre bancos

### Cenário 2: Templates Especializados por Banco
**Prós:**
- Máxima precisão para cada banco
- Pode extrair campos específicos (ex: pontos, milhas)
- Melhor UX para usuários

**Contras:**
- Mais código para manter
- Precisa atualizar quando bancos mudarem layout
- Requer identificação automática do banco

## Recomendação: Solução Híbrida

### Abordagem Recomendada
1. **Parser Genérico Robusto** (base)
   - Suporte a múltiplos formatos de data
   - Extração flexível de itens
   - Campos opcionais inteligentes

2. **Parsers Especializados** (quando necessário)
   - Ativados automaticamente ao detectar banco
   - Herdam do parser genérico
   - Apenas override de métodos específicos

### Bancos Prioritários para Templates
Com base em market share no Brasil (2025):

1. **Nubank** (60M+ clientes) - ✓ **Prioridade 1**
2. **Inter** (30M+ clientes)
3. **C6 Bank** (20M+ clientes)
4. **PicPay** (15M+ clientes)
5. **Banco do Brasil** (formato tradicional)
6. **Itaú** (formato tradicional)
7. **Bradesco** (formato tradicional)
8. **Santander** (formato tradicional)

### Dados Públicos Disponíveis
- Nubank: CNPJ 18.236.120/0001-58
- Inter: CNPJ 00.416.968/0001-01
- C6 Bank: CNPJ 31.872.495/0001-72
- PicPay: CNPJ 14.176.050/0001-70

## Plano de Implementação

### Fase 1: Melhorias Imediatas
1. Adicionar suporte a datas abreviadas ("DD MMM")
2. Melhorar extração de itens com contexto
3. Adicionar banco de dados de CNPJs conhecidos
4. Relaxar validação de campos opcionais

### Fase 2: Sistema de Templates
1. Criar classe base `BankParser`
2. Implementar detector automático de banco
3. Criar `NubankParser` especializado
4. Adicionar sistema de fallback (genérico → especializado → genérico)

### Fase 3: Expansão
1. Adicionar templates para outros bancos digitais
2. Criar sistema de aprendizado (ML) para novos formatos
3. Implementar validação/correção pós-extração

## Estrutura de Código Proposta

```
parsers/
├── __init__.py
├── financial_parser.py (Parser genérico melhorado)
├── bank_detector.py (Detecta banco automaticamente)
├── bank_parser_base.py (Classe base para parsers especializados)
├── banks/
│   ├── __init__.py
│   ├── nubank_parser.py
│   ├── inter_parser.py
│   ├── c6_parser.py
│   └── ...
└── utils/
    ├── date_parser.py (Suporte a múltiplos formatos)
    ├── cnpj_database.py (CNPJs conhecidos)
    └── item_extractor.py (Extração inteligente de itens)
```

## Métricas de Sucesso
- [ ] Fatura do Nubank processada sem erros
- [ ] 95%+ dos campos extraídos corretamente
- [ ] Sistema escalável para novos bancos
- [ ] Performance mantida (<2s por documento)
