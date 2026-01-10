# API de OCR e Extração de Dados Financeiros

API REST desenvolvida em Python/FastAPI para extração automática de dados financeiros de documentos PDF (nativos e escaneados).

## 🎯 Objetivo

Receber arquivos PDF, extrair texto usando OCR quando necessário, e retornar dados financeiros estruturados em JSON para uso em sistemas de gestão financeira.

## 🚀 Funcionalidades

- ✅ Detecção automática de tipo de PDF (nativo vs escaneado)
- ✅ Extração de texto de PDFs nativos usando `pdfplumber`
- ✅ OCR para PDFs escaneados usando `PaddleOCR`
- ✅ Identificação automática do tipo de documento (boleto, fatura, nota fiscal, etc.)
- ✅ Extração de campos financeiros estruturados
- ✅ Normalização e limpeza de texto
- ✅ **Confidence score inteligente** baseado em múltiplos fatores
- ✅ **Preparação de texto para LLMs** (Groq, OpenAI, Claude)
- ✅ API stateless e pronta para produção
- ✅ Documentação automática (Swagger/OpenAPI)
- ✅ CORS configurado para integração com frontend
- ✅ **Docker-ready** com Dockerfile e docker-compose

## 📋 Requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd api-ocr-leitura-faturas
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
```

### 3. Ative o ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente

Copie o arquivo de exemplo e ajuste conforme necessário:

```bash
copy .env.example .env
```

Edite o arquivo `.env` com suas configurações.

## ▶️ Como Executar

### Desenvolvimento

```bash
python main.py
```

Ou usando uvicorn diretamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: `http://localhost:8000`

### Produção

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints

### POST `/extract`

Extrai dados financeiros de um arquivo PDF.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: arquivo PDF

### POST `/extract-for-llm`

Extrai dados e prepara texto otimizado para LLMs (Groq, OpenAI, Claude, etc).

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: arquivo PDF

**Use este endpoint quando quiser:**
- Integrar com modelos de linguagem
- Fazer análises avançadas com IA
- Extrair informações não estruturadas
- Combinar extração tradicional + LLM

📚 **Guia completo:** [LLM_INTEGRATION.md](LLM_INTEGRATION.md)

**Exemplo usando cURL:**

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/caminho/para/seu/documento.pdf"
```

**Exemplo usando Python:**

```python
import requests

url = "http://localhost:8000/extract"
files = {"file": open("documento.pdf", "rb")}
response = requests.post(url, files=files)

print(response.json())
```

**Exemplo usando JavaScript/Fetch:**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/extract', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Erro:', error));
```

**Response (200 OK):**

```json
{
  "success": true,
  "document_type": "fatura_cartao",
  "confidence": 0.85,
  "raw_text": "FATURA CARTÃO DE CRÉDITO\n...",
  "data": {
    "empresa": "Banco Exemplo S.A.",
    "cnpj": "12.345.678/0001-90",
    "cpf": null,
    "data_emissao": "2026-01-01",
    "data_vencimento": "2026-01-15",
    "valor_total": 1500.00,
    "moeda": "BRL",
    "numero_documento": "123456",
    "codigo_barras": null,
    "linha_digitavel": null,
    "itens": [
      {
        "descricao": "Compra Loja X",
        "valor": 500.00,
        "quantidade": null,
        "data": null
      }
    ]
  },
  "metadata": {
    "pdf_type": "native",
    "pdf_detection_confidence": 0.95,
    "document_detection_confidence": 0.75,
    "extraction_confidence": 0.87,
    "llm_ready": true,
    "pages": 2,
    "extraction_method": "pdfplumber"
  }
}
```

**Confidence Score:**

O campo `confidence` é calculado considerando:
- 20% - Confiança na detecção do tipo de PDF
- 30% - Confiança na identificação do tipo de documento
- 50% - Confiança baseada nos campos extraídos (com pesos por importância)

### GET `/health`

Verifica o status da API.

**Response:**
```json
{
  "status": "healthy",
  "service": "api-ocr-leitura-faturas"
}
```

## 📊 Campos Extraídos

A API extrai os seguintes campos financeiros:

| Campo | Descrição | Tipo |
|-------|-----------|------|
| `empresa` | Nome da empresa emissora | string |
| `cnpj` | CNPJ da empresa | string |
| `cpf` | CPF (quando aplicável) | string |
| `data_emissao` | Data de emissão | string (YYYY-MM-DD) |
| `data_vencimento` | Data de vencimento | string (YYYY-MM-DD) |
| `valor_total` | Valor total do documento | float |
| `moeda` | Código da moeda (padrão: BRL) | string |
| `numero_documento` | Número do documento | string |
| `codigo_barras` | Código de barras (boletos) | string |
| `linha_digitavel` | Linha digitável (boletos) | string |
| `itens` | Lista de itens/transações | array |

## 🗂️ Tipos de Documentos Suportados

A API identifica automaticamente os seguintes tipos de documentos:

- **Boleto bancário** - Detecta código de barras e linha digitável
- **Fatura de cartão de crédito** - Extrai transações e valores
- **Nota fiscal (NF-e)** - Identifica produtos e totais
- **Extrato bancário** - Lista lançamentos e saldos

## 🏗️ Arquitetura do Projeto

```
api-ocr-leitura-faturas/
├── main.py                 # Aplicação FastAPI principal
├── config.py              # Configurações e variáveis de ambiente
├── models.py              # Modelos Pydantic (schemas)
├── requirements.txt       # Dependências do projeto
├── .env.example          # Exemplo de configuração
├── .gitignore            # Arquivos ignorados pelo Git
├── utils/
│   ├── __init__.py
│   └── pdf_detector.py   # Detecção de tipo de PDF
├── extractors/
│   ├── __init__.py
│   └── text_extractor.py # Extração de texto (pdfplumber + OCR)
└── parsers/
    ├── __init__.py
    └── financial_parser.py # Parsing de dados financeiros
```

## 🔍 Tecnologias Utilizadas

- **FastAPI** - Framework web moderno e rápido
- **pdfplumber** - Extração de texto de PDFs nativos
- **PaddleOCR** - OCR para documentos escaneados
- **OpenCV** - Processamento de imagens
- **Pydantic** - Validação de dados
- **Uvicorn** - Servidor ASGI

## ⚙️ Configurações Avançadas

### Variáveis de Ambiente

Edite o arquivo `.env` para configurar:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False

# Upload Configuration
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf

# OCR Configuration
PADDLE_OCR_LANG=pt
PADDLE_OCR_USE_GPU=False

# Logging
LOG_LEVEL=INFO
```

### Usando GPU para OCR

Se você tiver uma GPU NVIDIA disponível:

1. Instale o PaddlePaddle GPU:
```bash
pip uninstall paddlepaddle
pip install paddlepaddle-gpu
```

2. Configure no `.env`:
```env
PADDLE_OCR_USE_GPU=True
```

## 🧪 Testando a API

### Com arquivo de teste

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@exemplo.pdf" \
  -o resultado.json
```

### Interface Swagger

Acesse `http://localhost:8000/docs` e use a interface interativa para testar.

## 🐛 Tratamento de Erros

A API retorna erros estruturados:

```json
{
  "success": false,
  "error": "Descrição do erro",
  "detail": "Detalhes adicionais"
}
```

**Códigos de status HTTP:**
- `200` - Sucesso
- `400` - Erro de validação (arquivo inválido, formato incorreto)
- `500` - Erro interno do servidor

## 🚀 Deploy

### Docker (Recomendado)

Crie um `Dockerfile`:

```dpoppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build e execute:

```bash
docker build -t api-ocr .
docker run -p 8000:8000 api-ocr
```

**Ou use o docker-compose incluído:**

```bash
docker-compose up -d
```

O projeto já inclui [Dockerfile](Dockerfile) e [docker-compose.yml](docker-compose.yml) prontos!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build e execute:

```bash
docker build -t api-ocr . (configurável)

### Melhorias Futuras
- [ ] Suporte a múltiplos arquivos em batch
- [ ] Análise avançada de tabelas com Camelot
- [ ] Machine Learning para melhor detecção de campos
- [ ] Cache de resultados com Redis
- [ ] Fila assíncrona para processamento
- [ ] Suporte a outros formatos (imagens, DOCX)

## 🤖 Integração com LLMs

A API possui suporte nativo para integração com Large Language Models:

```python
import requests
from groq import Groq

# 1. Extrai via API
response = requests.post(
    "http://localhost:8000/extract-for-llm",
    files={"file": open("fatura.pdf", "rb")}
)

llm_data = response.json()["llm_prompt_data"]

# 2. Usa com Groq
client = Groq(api_key="sua-chave")
completion = client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[
        {"role": "system", "content": llm_data["system_instruction"]},
        {"role": "user", "content": llm_data["suggested_prompt"]}
    ]
)

print(completion.choices[0].message.content)
```

📚 **Guia completo de integração com LLMs:** [LLM_INTEGRATION.md](LLM_INTEGRATION.md)

Inclui exemplos para:
- ✅ Groq (Mixtral, Llama)
- ✅ OpenAI (GPT-4, GPT-3.5)
- ✅ Anthropic (Claude)
- ✅ Abordagem híbrida (tradicional + LLM
- Limite de 10MB por arquivo

### Melhorias Futuras
- [ ] Suporte a múltiplos arquivos em batch
- [ � Documentação Adicional

- **[QUICKSTART.md](QUICKSTART.md)** - Comece em 5 minutos
- **[INSTALL.md](INSTALL.md)** - Guia completo de instalação e deploy
- **[EXAMPLES.md](EXAMPLES.md)** - Exemplos em Python, JavaScript, TypeScript, PHP
- **[LLM_INTEGRATION.md](LLM_INTEGRATION.md)** - Integração com Groq, OpenAI, Claude
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Arquitetura e estrutura
- **[CHANGELOG.md](CHANGELOG.md)** - Histórico de versões
- **[COMPLIANCE.md](COMPLIANCE.md)** - Análise de conformidade com requisitos

## 👤 Autor

Desenvolvido para processamento de documentos financeiros.

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique a documentação em `/docs`
2. Consulte os logs da aplicação
3. Leia os guias em [QUICKSTART.md](QUICKSTART.md) e [INSTALL.md](INSTALL.md)
4. Veja exemplos práticos em [EXAMPLES.md](EXAMPLES.md)

---

**Nota**: Esta é a versão 1.0.0 da API. Consulte o [CHANGELOG.md](CHANGELOG.md)

  try {
    const response = await fetch('http://localhost:8000/extract', {
      method: 'POST',
      body: formData,
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Dados extraídos:', data.data);
      // Processar dados...
    }
  } catch (error) {
    console.error('Erro:', error);
  }
};
```

## 📄 Licença

Este projeto está sob a licença MIT.

## 👤 Autor

Desenvolvido para processamento de documentos financeiros.

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique a documentação em `/docs`
2. Consulte os logs da aplicação
3. Abra uma issue no repositório

---

**Nota**: Esta é a versão 1.0.0 da API. Consulte o changelog para atualizações.
