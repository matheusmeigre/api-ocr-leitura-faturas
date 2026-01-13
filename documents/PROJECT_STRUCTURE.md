# 📂 Estrutura do Projeto

```
api-ocr-leitura-faturas/
│
├── 📁 extractors/                    # Extratores de texto
│   ├── __init__.py
│   └── text_extractor.py             # pdfplumber + PaddleOCR
│
├── 📁 parsers/                       # Parsers de dados financeiros
│   ├── __init__.py
│   └── financial_parser.py           # Regex e extração de campos
│
├── 📁 utils/                         # Utilitários
│   ├── __init__.py
│   └── pdf_detector.py               # Detecção de tipo de PDF
│
├── 📄 main.py                        # ⭐ Aplicação FastAPI principal
├── 📄 models.py                      # Modelos Pydantic (schemas)
├── 📄 config.py                      # Configurações e variáveis de ambiente
│
├── 📄 run.py                         # 🚀 Script para iniciar o servidor
├── 📄 test_api.py                    # 🧪 Script de teste da API
│
├── 📄 requirements.txt               # 📦 Dependências do projeto
├── 📄 .env                           # ⚙️ Configurações (não versionado)
├── 📄 .env.example                   # Exemplo de configuração
├── 📄 .gitignore                     # Arquivos ignorados pelo Git
│
├── 📚 Documentação/
│   ├── 📄 README.md                  # Documentação principal
│   ├── 📄 QUICKSTART.md              # Guia de início rápido
│   ├── 📄 INSTALL.md                 # Guia de instalação e deploy
│   ├── 📄 EXAMPLES.md                # Exemplos de uso em várias linguagens
│   ├── 📄 CHANGELOG.md               # Histórico de versões
│   └── 📄 LICENSE                    # Licença MIT
│
└── 📁 temp/                          # (criado automaticamente) Arquivos temporários
    └── uploads/                      # PDFs em processamento
```

## 📝 Descrição dos Arquivos Principais

### 🎯 Core da API

#### `main.py` (⭐ Arquivo Principal)
Aplicação FastAPI com:
- Endpoint POST `/extract` - Extração de dados
- Endpoint GET `/health` - Health check
- Endpoint GET `/` - Informações da API
- Configuração de CORS
- Middleware de tratamento de erros
- Documentação automática

**Principais funções:**
- `extract_financial_data()` - Processa PDFs e retorna dados
- Validação de arquivos
- Orquestração do pipeline de extração

#### `models.py`
Schemas Pydantic para validação:
- `DadosFinanceiros` - Dados extraídos
- `ItemFinanceiro` - Item de fatura/nota
- `ExtractionResponse` - Resposta da API
- `ErrorResponse` - Resposta de erro

#### `config.py`
Configurações centralizadas:
- Variáveis de ambiente
- Configurações de API (host, porta, debug)
- Configurações de upload (tamanho máximo, extensões)
- Configurações de OCR (idioma, GPU)

### 🔧 Utilitários

#### `utils/pdf_detector.py`
Detecção de tipo de PDF:
- `detect_pdf_type()` - Identifica se é nativo ou escaneado
- `is_valid_pdf()` - Valida arquivo PDF
- `get_pdf_metadata()` - Extrai metadados

**Como funciona:**
1. Analisa as primeiras páginas do PDF
2. Conta caracteres de texto extraíveis
3. Determina confiança da detecção
4. Retorna tipo ('native' ou 'scanned') e confiança

### 📄 Extratores

#### `extractors/text_extractor.py`
Classe `TextExtractor` com:
- `extract_from_native_pdf()` - Usa pdfplumber
- `extract_from_scanned_pdf()` - Usa PaddleOCR
- `normalize_text()` - Limpa e normaliza texto
- `extract_text()` - Método unificado

**Recursos:**
- Lazy loading do PaddleOCR (otimização)
- Extração de tabelas
- Conversão PDF → Imagem → OCR
- Múltiplas páginas
- Cálculo de confiança

### 🔍 Parsers

#### `parsers/financial_parser.py`
Classe `FinancialParser` com:
- `detect_document_type()` - Identifica tipo de documento
- `extract_cnpj()` - Extrai CNPJ
- `extract_cpf()` - Extrai CPF
- `extract_dates()` - Extrai datas
- `extract_values()` - Extrai valores monetários
- `extract_company_name()` - Extrai nome da empresa
- `parse_financial_data()` - Parsing completo

**Padrões regex incluídos:**
- CNPJ: `\b\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}\b`
- CPF: `\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b`
- Data: `\b\d{2}[/-]\d{2}[/-]\d{4}\b`
- Valor: `R?\$?\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})`
- Código de barras: `\b\d{47,48}\b`

**Tipos de documentos detectados:**
- Boleto bancário
- Fatura de cartão de crédito
- Nota fiscal (NF-e)
- Extrato bancário

### 🚀 Scripts

#### `run.py`
Script para iniciar o servidor de desenvolvimento:
```bash
python run.py
```
- Mostra informações de inicialização
- Usa configurações do `.env`
- Habilita reload automático em modo debug

#### `test_api.py`
Script de teste da API:
```bash
python test_api.py documento.pdf
```
- Envia PDF para a API
- Exibe resultado formatado
- Salva JSON completo
- Mostra informações resumidas

### 📦 Dependências

#### `requirements.txt`
Todas as bibliotecas necessárias:
- **FastAPI** - Framework web
- **Uvicorn** - Servidor ASGI
- **pdfplumber** - Extração de PDFs nativos
- **PaddleOCR** - OCR
- **OpenCV** - Processamento de imagens
- **Pydantic** - Validação de dados
- **python-dotenv** - Variáveis de ambiente

### ⚙️ Configuração

#### `.env`
Configurações da aplicação:
```env
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
MAX_FILE_SIZE_MB=10
PADDLE_OCR_LANG=pt
LOG_LEVEL=INFO
```

#### `.gitignore`
Arquivos não versionados:
- `__pycache__/` - Cache do Python
- `venv/` - Ambiente virtual
- `.env` - Configurações locais
- `*.pdf` - PDFs de teste
- `temp/` - Arquivos temporários

## 🔄 Fluxo de Execução

```
1. Cliente envia PDF → POST /extract
   ↓
2. main.py recebe e valida arquivo
   ↓
3. utils/pdf_detector.py detecta tipo
   ↓
4. extractors/text_extractor.py extrai texto
   ↓
5. parsers/financial_parser.py identifica documento
   ↓
6. parsers/financial_parser.py extrai dados
   ↓
7. models.py valida resposta
   ↓
8. main.py retorna JSON
```

## 📊 Tamanho dos Arquivos

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| main.py | ~200 | API principal |
| models.py | ~100 | Schemas Pydantic |
| text_extractor.py | ~200 | Extração de texto |
| financial_parser.py | ~300 | Parsing de dados |
| pdf_detector.py | ~100 | Detecção de PDF |
| config.py | ~30 | Configurações |

**Total:** ~1000 linhas de código Python

## 🎨 Padrões de Design

### Arquitetura em Camadas

```
┌─────────────────────────────────────┐
│         API Layer (main.py)         │  ← Endpoints HTTP
├─────────────────────────────────────┤
│    Business Logic (extractors,     │  ← Lógica de negócio
│         parsers, utils)             │
├─────────────────────────────────────┤
│     Models Layer (models.py)        │  ← Validação de dados
├─────────────────────────────────────┤
│   Configuration (config.py, .env)   │  ← Configurações
└─────────────────────────────────────┘
```

### Separação de Responsabilidades

- **main.py** → API e orquestração
- **extractors/** → Extração de texto
- **parsers/** → Análise e parsing
- **utils/** → Utilitários auxiliares
- **models.py** → Estruturas de dados
- **config.py** → Configurações

### Princípios SOLID

- ✅ **Single Responsibility** - Cada classe tem uma responsabilidade
- ✅ **Open/Closed** - Fácil de estender sem modificar
- ✅ **Dependency Inversion** - Depende de abstrações

## 🧪 Como Testar Cada Componente

### Testar detector de PDF
```python
from utils.pdf_detector import detect_pdf_type

with open("documento.pdf", "rb") as f:
    pdf_bytes = f.read()
    pdf_type, confidence = detect_pdf_type(pdf_bytes)
    print(f"Tipo: {pdf_type}, Confiança: {confidence}")
```

### Testar extrator de texto
```python
from extractors.text_extractor import TextExtractor

extractor = TextExtractor()
with open("documento.pdf", "rb") as f:
    text, metadata = extractor.extract_text(f.read(), "native")
    print(text)
```

### Testar parser
```python
from parsers.financial_parser import FinancialParser

parser = FinancialParser()
dados = parser.parse_financial_data(texto_extraido)
print(dados.model_dump_json(indent=2))
```

## 📚 Documentação Adicional

- **[README.md](README.md)** - Documentação principal
- **[QUICKSTART.md](QUICKSTART.md)** - Início rápido (5 minutos)
- **[INSTALL.md](INSTALL.md)** - Instalação e deploy detalhado
- **[EXAMPLES.md](EXAMPLES.md)** - Exemplos de código
- **[CHANGELOG.md](CHANGELOG.md)** - Histórico de versões

## 🔗 Links Úteis

- Documentação FastAPI: https://fastapi.tiangolo.com
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- pdfplumber: https://github.com/jsvine/pdfplumber

---

**Última atualização:** Janeiro 2026
