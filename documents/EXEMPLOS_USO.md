# Exemplos de Uso - Sistema de Parsers por Banco

## Exemplo 1: Processando Fatura do Nubank

### Código Python
```python
from parsers.financial_parser import FinancialParser
import PyPDF2

# Ler PDF
with open('fatura_nubank.pdf', 'rb') as f:
    pdf_reader = PyPDF2.PdfReader(f)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

# Criar parser
parser = FinancialParser()

# Parse automático (detecta Nubank e usa parser especializado)
dados = parser.parse_financial_data(text)

# Resultado
print(f"Banco: {dados.empresa}")
# Output: "Nu Pagamentos S.A."

print(f"CNPJ: {dados.cnpj}")
# Output: "18.236.120/0001-58"

print(f"Vencimento: {dados.data_vencimento}")
# Output: "2025-11-24"

print(f"Total: R$ {dados.valor_total}")
# Output: "3038.08"

print(f"Transações: {len(dados.itens)}")
# Output: "35"

# Ver primeiras transações com data
for item in dados.itens[:3]:
    print(f"{item.data} - {item.descricao}: R$ {item.valor}")
# Output:
# 2025-10-17 - Moreira Vidracaria - Parcela 2/3: R$ 250.0
# 2025-10-17 - C S - Parcela 3/3: R$ 117.56
# 2025-10-17 - C&A Variedades - Parcela 2/4: R$ 47.62
```

## Exemplo 2: Via API REST

### Request
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@fatura_nubank.pdf"
```

### Response (Antes)
```json
{
  "success": false,
  "error": "Resposta da API OCR está em formato inválido",
  "detail": [
    "data.cnpj: Expected string, received null",
    "data.itens.0.data: Expected string, received null",
    "..."
  ]
}
```

### Response (Depois)
```json
{
  "success": true,
  "document_type": "fatura_cartao",
  "confidence": 0.95,
  "data": {
    "empresa": "Nu Pagamentos S.A.",
    "cnpj": "18.236.120/0001-58",
    "cpf": null,
    "data_emissao": "2025-11-17",
    "data_vencimento": "2025-11-24",
    "valor_total": 3038.08,
    "moeda": "BRL",
    "numero_documento": "Fatura Matheus Meigre E Silva",
    "itens": [
      {
        "descricao": "Moreira Vidracaria - Parcela 2/3",
        "valor": 250.0,
        "quantidade": null,
        "data": "2025-10-17"
      },
      {
        "descricao": "Supermercado Morais",
        "valor": 126.32,
        "quantidade": null,
        "data": "2025-10-17"
      }
    ]
  },
  "metadata": {
    "bank_detected": "nubank",
    "parser_used": "specialized",
    "extraction_time_ms": 245
  }
}
```

## Exemplo 3: Detectando Banco Manualmente

```python
from parsers.utils.bank_detector import BankDetector

text = "Olá, Matheus. Esta é a sua fatura de novembro..."

# Detecta banco
result = BankDetector.detect_bank(text)

if result:
    bank_key, bank_name, confidence = result
    print(f"Banco: {bank_name}")
    print(f"Confiança: {confidence:.2%}")
    print(f"CNPJ: {BankDetector.get_cnpj(bank_key)}")
else:
    print("Banco não identificado")

# Output:
# Banco: Nubank
# Confiança: 100.00%
# CNPJ: 18.236.120/0001-58
```

## Exemplo 4: Parsing de Datas Abreviadas

```python
from parsers.utils.date_parser import DateParser

parser = DateParser(default_year=2025)

# Formato abreviado (Nubank)
date1 = parser.parse_date("17 OUT")
print(date1)  # Output: "2025-10-17"

# Formato tradicional
date2 = parser.parse_date("24/11/2025")
print(date2)  # Output: "2025-11-24"

# Formato por extenso
date3 = parser.parse_date("17 de outubro de 2025")
print(date3)  # Output: "2025-10-17"

# Extrair todas as datas do texto
text = """
17 OUT
18 OUT
Data de vencimento: 24/11/2025
"""

dates = parser.extract_all_dates(text)
for original, normalized in dates:
    print(f"{original} → {normalized}")

# Output:
# 17 OUT → 2025-10-17
# 18 OUT → 2025-10-18
# 24/11/2025 → 2025-11-24
```

## Exemplo 5: Busca de CNPJ por Nome

```python
from parsers.utils.cnpj_database import CNPJDatabase

# Busca exata
cnpj1 = CNPJDatabase.get_cnpj_by_name("nubank")
print(cnpj1)  # Output: "18.236.120/0001-58"

# Busca case-insensitive
cnpj2 = CNPJDatabase.get_cnpj_by_name("BANCO INTER")
print(cnpj2)  # Output: "00.416.968/0001-01"

# Busca parcial
cnpj3 = CNPJDatabase.get_cnpj_by_name("c6")
print(cnpj3)  # Output: "31.872.495/0001-72"

# Identifica banco do texto
bank_info = CNPJDatabase.identify_bank("Fatura do C6 Bank")
if bank_info:
    name, cnpj = bank_info
    print(f"{name}: {cnpj}")
# Output: "C6 Bank: 31.872.495/0001-72"
```

## Exemplo 6: Criando Parser Customizado

```python
from parsers.banks.nubank_parser import NubankParser
from models import DadosFinanceiros

class MeuBancoParser:
    def can_parse(self, text: str) -> bool:
        return 'meu banco' in text.lower()
    
    def parse(self, text: str) -> DadosFinanceiros:
        dados = DadosFinanceiros()
        dados.empresa = "Meu Banco S.A."
        dados.cnpj = "12.345.678/0001-90"
        
        # Sua lógica de extração aqui
        import re
        
        # Exemplo: extrair valor total
        match = re.search(r'Total:\s*R\$\s*([\d.,]+)', text)
        if match:
            valor_str = match.group(1).replace('.', '').replace(',', '.')
            dados.valor_total = float(valor_str)
        
        return dados

# Usar parser customizado
parser = MeuBancoParser()
text = "Meu Banco - Total: R$ 1.500,00"

if parser.can_parse(text):
    dados = parser.parse(text)
    print(f"{dados.empresa}: R$ {dados.valor_total}")
# Output: "Meu Banco S.A.: R$ 1500.0"
```

## Exemplo 7: Integração com FastAPI

```python
from fastapi import FastAPI, UploadFile, File
from parsers.financial_parser import FinancialParser
import PyPDF2
import io

app = FastAPI()
parser = FinancialParser()

@app.post("/extract")
async def extract_invoice(file: UploadFile = File(...)):
    # Lê PDF
    pdf_bytes = await file.read()
    pdf_file = io.BytesIO(pdf_bytes)
    
    # Extrai texto
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    # Parse automático
    dados = parser.parse_financial_data(text)
    
    # Detecta qual parser foi usado
    bank_info = None
    if 'nubank' in text.lower():
        bank_info = {
            "bank": "Nubank",
            "parser": "specialized"
        }
    
    return {
        "success": True,
        "data": dados.model_dump(),
        "metadata": bank_info
    }
```

## Exemplo 8: Comparação Genérico vs Especializado

```python
from parsers.financial_parser import FinancialParser

text_nubank = """
Olá, Matheus.
Esta é a sua fatura de novembro
Data de vencimento: 24 NOV 2025
Total a pagar R$ 3.038,08

TRANSAÇÕES
17 OUT
 •••• 2300 Moreira Vidracaria R$ 250,00
"""

parser = FinancialParser()

# Parse automático (usa especializado se disponível)
dados_especializado = parser.parse_financial_data(text_nubank)

print("Parser Especializado (Nubank):")
print(f"  CNPJ: {dados_especializado.cnpj}")
print(f"  Vencimento: {dados_especializado.data_vencimento}")
print(f"  Total: {dados_especializado.valor_total}")
print(f"  Itens com data: {sum(1 for i in dados_especializado.itens if i.data)}")

# Output:
# Parser Especializado (Nubank):
#   CNPJ: 18.236.120/0001-58
#   Vencimento: 2025-11-24
#   Total: 3038.08
#   Itens com data: 1
```

## Exemplo 9: Tratamento de Erros

```python
from parsers.financial_parser import FinancialParser
from pydantic import ValidationError

parser = FinancialParser()
text = "Documento sem dados estruturados"

try:
    dados = parser.parse_financial_data(text)
    
    # Verifica campos obrigatórios
    if not dados.valor_total:
        print("Aviso: Valor total não encontrado")
    
    if not dados.cnpj:
        print("Aviso: CNPJ não encontrado (pode ser normal para algumas fintechs)")
    
    # Serializa para JSON
    json_data = dados.model_dump()
    print("Extração bem-sucedida!")
    
except ValidationError as e:
    print("Erro de validação:")
    for error in e.errors():
        field = error['loc'][0]
        msg = error['msg']
        print(f"  - {field}: {msg}")
        
except Exception as e:
    print(f"Erro inesperado: {e}")
```

## Exemplo 10: Estatísticas de Extração

```python
from parsers.financial_parser import FinancialParser

def calculate_extraction_quality(dados):
    """Calcula qualidade da extração"""
    total_fields = 7  # cnpj, empresa, datas, valor, etc
    filled_fields = 0
    
    if dados.cnpj:
        filled_fields += 1
    if dados.empresa:
        filled_fields += 1
    if dados.data_emissao:
        filled_fields += 1
    if dados.data_vencimento:
        filled_fields += 1
    if dados.valor_total:
        filled_fields += 1
    if dados.itens and len(dados.itens) > 0:
        filled_fields += 1
    if dados.numero_documento:
        filled_fields += 1
    
    quality = (filled_fields / total_fields) * 100
    
    # Verifica qualidade dos itens
    if dados.itens:
        items_with_date = sum(1 for i in dados.itens if i.data)
        items_quality = (items_with_date / len(dados.itens)) * 100
    else:
        items_quality = 0
    
    return {
        "overall_quality": quality,
        "fields_filled": f"{filled_fields}/{total_fields}",
        "items_quality": items_quality,
        "total_items": len(dados.itens) if dados.itens else 0
    }

# Testar
parser = FinancialParser()
text = "..." # texto da fatura
dados = parser.parse_financial_data(text)

stats = calculate_extraction_quality(dados)
print(f"Qualidade geral: {stats['overall_quality']:.1f}%")
print(f"Campos preenchidos: {stats['fields_filled']}")
print(f"Itens com data: {stats['items_quality']:.1f}%")
print(f"Total de itens: {stats['total_items']}")

# Output (Nubank):
# Qualidade geral: 100.0%
# Campos preenchidos: 7/7
# Itens com data: 100.0%
# Total de itens: 35
```

## Bancos Suportados

| Banco | Parser | CNPJ | Status |
|-------|--------|------|--------|
| Nubank | ✅ Especializado | 18.236.120/0001-58 | 100% funcional |
| Inter | 🔄 Genérico | 00.416.968/0001-01 | Em desenvolvimento |
| C6 Bank | 🔄 Genérico | 31.872.495/0001-72 | Em desenvolvimento |
| PicPay | 🔄 Genérico | 14.176.050/0001-70 | Em desenvolvimento |
| BB | 🔄 Genérico | 00.000.000/0001-91 | Parser genérico |
| Itaú | 🔄 Genérico | 60.701.190/0001-04 | Parser genérico |
| Bradesco | 🔄 Genérico | 60.746.948/0001-12 | Parser genérico |

✅ = Parser especializado implementado
🔄 = Usa parser genérico com detecção de CNPJ
