# 🤖 Integração com LLMs (Groq, OpenAI, Claude)

Este documento mostra como usar a API com Large Language Models para extração avançada de dados.

## 🎯 Endpoint Específico para LLM

A API possui o endpoint `/extract-for-llm` que prepara o texto otimizado para consumo por LLMs.

### Diferença entre os endpoints

| Endpoint | Uso | Retorno |
|----------|-----|---------|
| `/extract` | Extração tradicional com regex | Dados estruturados |
| `/extract-for-llm` | Texto preparado para LLM | Texto + prompt + dados estruturados |

## 🚀 Como Funciona

```
PDF → API → Texto Limpo + Prompt Otimizado → LLM → Dados Avançados
```

## 📝 Exemplo de Requisição

```python
import requests

# 1. Envie o PDF para o endpoint LLM
with open("fatura.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/extract-for-llm",
        files={"file": f}
    )

data = response.json()

# 2. Extraia os dados preparados
llm_data = data["llm_prompt_data"]
system_instruction = llm_data["system_instruction"]
document_content = llm_data["document_content"]
suggested_prompt = llm_data["suggested_prompt"]

print(f"Texto tem {llm_data['document_stats']['total_words']} palavras")
```

## 🌟 Integração com Groq

### Setup

```bash
pip install groq
```

### Código Completo

```python
import requests
from groq import Groq

# 1. Extrai texto via API
with open("fatura.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/extract-for-llm",
        files={"file": f}
    )

api_data = response.json()
llm_data = api_data["llm_prompt_data"]

# 2. Envia para Groq
client = Groq(api_key="sua-chave-groq")

completion = client.chat.completions.create(
    model="mixtral-8x7b-32768",  # ou "llama3-70b-8192"
    messages=[
        {
            "role": "system",
            "content": llm_data["system_instruction"]
        },
        {
            "role": "user",
            "content": llm_data["suggested_prompt"]
        }
    ],
    temperature=0.1,  # Baixa temperatura para mais precisão
    max_tokens=2000
)

# 3. Processa resposta do LLM
llm_response = completion.choices[0].message.content
print("Resposta do LLM:")
print(llm_response)

# 4. Compare com extração tradicional
traditional = api_data["traditional_extraction"]
print(f"\nExtração Tradicional (confiança: {traditional['confidence']}):")
print(f"Empresa: {traditional['data']['empresa']}")
print(f"Valor: R$ {traditional['data']['valor_total']}")
```

## 🔓 Integração com OpenAI

```python
import requests
from openai import OpenAI

# 1. Extrai via API
with open("documento.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/extract-for-llm",
        files={"file": f}
    )

api_data = response.json()
llm_data = api_data["llm_prompt_data"]

# 2. Usa OpenAI
client = OpenAI(api_key="sua-chave-openai")

completion = client.chat.completions.create(
    model="gpt-4-turbo-preview",  # ou "gpt-3.5-turbo"
    messages=[
        {
            "role": "system",
            "content": llm_data["system_instruction"]
        },
        {
            "role": "user",
            "content": llm_data["suggested_prompt"]
        }
    ],
    temperature=0.2,
    response_format={"type": "json_object"}  # Força resposta em JSON
)

result = completion.choices[0].message.content
print(result)
```

## 🧠 Integração com Claude (Anthropic)

```python
import requests
import anthropic

# 1. Extrai via API
with open("nota_fiscal.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/extract-for-llm",
        files={"file": f}
    )

api_data = response.json()
llm_data = api_data["llm_prompt_data"]

# 2. Usa Claude
client = anthropic.Anthropic(api_key="sua-chave-anthropic")

message = client.messages.create(
    model="claude-3-opus-20240229",  # ou "claude-3-sonnet-20240229"
    max_tokens=2000,
    system=llm_data["system_instruction"],
    messages=[
        {
            "role": "user",
            "content": llm_data["suggested_prompt"]
        }
    ]
)

print(message.content[0].text)
```

## 💡 Prompt Customizado

Você pode criar seu próprio prompt em vez de usar o sugerido:

```python
# Extrai dados da API
response = requests.post(
    "http://localhost:8000/extract-for-llm",
    files={"file": open("fatura.pdf", "rb")}
)

llm_data = response.json()["llm_prompt_data"]

# Prompt customizado para análise específica
custom_prompt = f"""
Analise este documento financeiro e responda em JSON:

1. Qual o tipo exato de documento?
2. Existe algum valor em atraso?
3. Há multas ou juros aplicados?
4. Qual a data limite para pagamento?
5. Existem descontos para pagamento antecipado?

Documento:
{llm_data['document_content']}

Responda APENAS com JSON válido seguindo esta estrutura:
{{
  "tipo_documento": "",
  "valor_atraso": 0.0,
  "multas_juros": 0.0,
  "data_limite": "",
  "desconto_antecipado": 0.0
}}
"""

# Use este prompt com seu LLM preferido
```

## 🎨 Casos de Uso Avançados

### 1. Validação e Correção de Dados

```python
# Combina extração tradicional + LLM para validação
api_response = requests.post(
    "http://localhost:8000/extract-for-llm",
    files={"file": open("boleto.pdf", "rb")}
).json()

traditional = api_response["traditional_extraction"]["data"]
llm_data = api_response["llm_prompt_data"]

# Cria prompt de validação
validation_prompt = f"""
Os seguintes dados foram extraídos automaticamente de um boleto:

Empresa: {traditional['empresa']}
CNPJ: {traditional['cnpj']}
Valor: R$ {traditional['valor_total']}
Vencimento: {traditional['data_vencimento']}

Baseado no texto completo do documento abaixo, valide se estes dados estão corretos
e corrija qualquer erro encontrado:

{llm_data['document_content']}

Responda em JSON com os dados validados/corrigidos.
"""

# Envia para LLM para validação
```

### 2. Extração de Dados Não Estruturados

```python
# Usa LLM para extrair informações que regex não consegue
prompt = f"""
Do documento abaixo, extraia:
1. Todos os nomes de pessoas mencionados
2. Endereços completos
3. Observações ou notas importantes
4. Condições especiais de pagamento
5. Qualquer informação sobre garantias ou seguros

{llm_data['document_content']}

Retorne em JSON estruturado.
"""
```

### 3. Análise Comparativa

```python
# Processa múltiplos documentos e compara
documentos = ["fatura_jan.pdf", "fatura_fev.pdf", "fatura_mar.pdf"]
extracted_data = []

for doc in documentos:
    response = requests.post(
        "http://localhost:8000/extract-for-llm",
        files={"file": open(doc, "rb")}
    ).json()
    extracted_data.append(response)

# Cria prompt de análise comparativa
comparison_prompt = f"""
Compare estas 3 faturas mensais e identifique:
1. Tendência de aumento ou diminuição de valores
2. Novos itens ou serviços adicionados
3. Itens removidos
4. Variação percentual média
5. Alertas ou anomalias

Fatura Janeiro:
{extracted_data[0]['llm_prompt_data']['document_content'][:500]}...

Fatura Fevereiro:
{extracted_data[1]['llm_prompt_data']['document_content'][:500]}...

Fatura Março:
{extracted_data[2]['llm_prompt_data']['document_content'][:500]}...
"""
```

## 📊 Estrutura de Resposta do Endpoint

```json
{
  "success": true,
  "llm_prompt_data": {
    "system_instruction": "Você receberá um documento financeiro...",
    "document_content": "Texto completo extraído e limpo",
    "document_stats": {
      "total_lines": 150,
      "total_words": 1250,
      "total_chars": 8500,
      "has_sections": true
    },
    "extraction_metadata": {
      "pdf_type": "native",
      "extraction_method": "pdfplumber",
      "pages": 2
    },
    "structured_sections": {
      "header": "...",
      "dados do cliente": "...",
      "valores": "..."
    },
    "suggested_prompt": "Analise o seguinte documento..."
  },
  "traditional_extraction": {
    "document_type": "fatura_cartao",
    "confidence": 0.85,
    "data": {
      "empresa": "Banco Exemplo",
      "valor_total": 1500.00,
      ...
    }
  },
  "usage_example": {
    "description": "Use o 'suggested_prompt' com seu LLM favorito",
    "groq_example": "...",
    "openai_example": "..."
  }
}
```

## 🔥 Exemplo Completo: Pipeline Híbrido

Combina extração tradicional (rápida) com LLM (precisa):

```python
import requests
from groq import Groq

def extract_with_hybrid_approach(pdf_path: str) -> dict:
    """
    Abordagem híbrida: usa extração tradicional primeiro,
    depois LLM apenas se confiança for baixa.
    """
    
    # 1. Extração completa
    with open(pdf_path, "rb") as f:
        response = requests.post(
            "http://localhost:8000/extract-for-llm",
            files={"file": f}
        ).json()
    
    traditional = response["traditional_extraction"]
    confidence = traditional["confidence"]
    
    # 2. Se confiança for alta, usa dados tradicionais
    if confidence > 0.8:
        print(f"✅ Alta confiança ({confidence}), usando extração tradicional")
        return traditional["data"]
    
    # 3. Se confiança for baixa, usa LLM para melhorar
    print(f"⚠️ Baixa confiança ({confidence}), usando LLM para refinar")
    
    llm_data = response["llm_prompt_data"]
    
    groq = Groq(api_key="sua-chave")
    completion = groq.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "system", "content": llm_data["system_instruction"]},
            {"role": "user", "content": llm_data["suggested_prompt"]}
        ],
        temperature=0.1
    )
    
    llm_result = completion.choices[0].message.content
    
    # 4. Combina resultados
    return {
        "traditional": traditional["data"],
        "llm_enhanced": llm_result,
        "method": "hybrid",
        "confidence": confidence
    }

# Uso
result = extract_with_hybrid_approach("fatura_complexa.pdf")
print(result)
```

## 💰 Economia de Tokens

A API já faz pré-processamento e limpeza, economizando tokens do LLM:

| Sem API | Com API |
|---------|---------|
| ~5000 tokens | ~2000 tokens |
| Texto sujo com OCR bruto | Texto limpo e estruturado |
| Múltiplas tentativas | Prompt otimizado |

**Economia estimada: 60% de tokens!**

## 🎯 Melhores Práticas

1. **Use temperatura baixa** (0.1-0.3) para dados estruturados
2. **Especifique formato JSON** na resposta quando possível
3. **Combine com extração tradicional** para validação
4. **Cache resultados** de documentos processados
5. **Use modelos adequados**: Mixtral/GPT-4 para precisão, GPT-3.5 para velocidade

## 🔗 Links Úteis

- [Groq API Docs](https://console.groq.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude Docs](https://docs.anthropic.com/)

---

**Dica:** Para documentos muito grandes, use o campo `structured_sections` do LLM data para processar seção por seção, economizando ainda mais tokens!
