# 🚀 Guia de Início Rápido

Este é um guia rápido para colocar a API funcionando em menos de 5 minutos!

## ⚡ Quick Start (Windows)

```powershell
# 1. Crie o ambiente virtual
python -m venv venv

# 2. Ative o ambiente virtual
venv\Scripts\activate

# 3. Instale as dependências (pode demorar alguns minutos)
pip install -r requirements.txt

# 4. Inicie o servidor
python run.py
```

✅ Pronto! A API está rodando em: http://localhost:8000

## ⚡ Quick Start (Linux/Mac)

```bash
# 1. Crie o ambiente virtual
python3 -m venv venv

# 2. Ative o ambiente virtual
source venv/bin/activate

# 3. Instale as dependências (pode demorar alguns minutos)
pip install -r requirements.txt

# 4. Inicie o servidor
python run.py
```

✅ Pronto! A API está rodando em: http://localhost:8000

## 📖 Documentação Interativa

Acesse: http://localhost:8000/docs

Aqui você pode testar a API diretamente pelo navegador!

## 🧪 Primeiro Teste

### Opção 1: Interface Web (Mais fácil)

1. Acesse: http://localhost:8000/docs
2. Clique em `POST /extract`
3. Clique em "Try it out"
4. Faça upload de um PDF
5. Clique em "Execute"
6. Veja o resultado!

### Opção 2: cURL (Linha de comando)

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@seu_documento.pdf" \
  -o resultado.json
```

### Opção 3: Script Python

```python
import requests

with open("seu_documento.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/extract",
        files={"file": f}
    )

print(response.json())
```

### Opção 4: Script de teste incluído

```bash
python test_api.py seu_documento.pdf
```

## 📁 Estrutura do Projeto

```
api-ocr-leitura-faturas/
│
├── 📄 main.py                   # API FastAPI principal
├── 📄 models.py                 # Modelos de dados (schemas)
├── 📄 config.py                 # Configurações
├── 📄 run.py                    # Script para iniciar o servidor
├── 📄 test_api.py              # Script de teste
│
├── 📁 utils/                    # Utilitários
│   └── pdf_detector.py         # Detecção de tipo de PDF
│
├── 📁 extractors/               # Extratores de texto
│   └── text_extractor.py       # pdfplumber + PaddleOCR
│
├── 📁 parsers/                  # Parsers de dados
│   └── financial_parser.py     # Extração de campos financeiros
│
├── 📄 requirements.txt          # Dependências
├── 📄 .env                      # Configurações (criado automaticamente)
│
└── 📚 Documentação/
    ├── README.md                # Documentação principal
    ├── INSTALL.md              # Guia de instalação detalhado
    └── EXAMPLES.md             # Exemplos de uso
```

## 🎯 O que a API Faz?

1. **Recebe** um PDF (nativo ou escaneado)
2. **Detecta** automaticamente o tipo de PDF
3. **Extrai** o texto (usando pdfplumber ou OCR)
4. **Identifica** o tipo de documento (boleto, fatura, nota fiscal, etc.)
5. **Extrai** dados financeiros estruturados
6. **Retorna** JSON com todos os dados

## 📊 Exemplo de Resposta

```json
{
  "success": true,
  "document_type": "fatura_cartao",
  "confidence": 0.85,
  "data": {
    "empresa": "Banco Exemplo S.A.",
    "cnpj": "12.345.678/0001-90",
    "data_emissao": "2026-01-01",
    "data_vencimento": "2026-01-15",
    "valor_total": 1500.00,
    "moeda": "BRL",
    "itens": [
      {
        "descricao": "Compra Loja X",
        "valor": 500.00
      }
    ]
  }
}
```

## 🔧 Configurações Rápidas

Edite o arquivo `.env` para personalizar:

```env
API_PORT=8000              # Porta da API
MAX_FILE_SIZE_MB=10        # Tamanho máximo de arquivo
PADDLE_OCR_LANG=pt         # Idioma do OCR (pt, en, es, etc.)
LOG_LEVEL=INFO             # Nível de log (DEBUG, INFO, WARNING, ERROR)
```

## 📌 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/health` | GET | Status de saúde |
| `/extract` | POST | Extração de dados |
| `/docs` | GET | Documentação interativa |

## 🎨 Integração com Frontend

### React/Next.js

```typescript
const handleUpload = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/extract', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  console.log(data);
};
```

### Vue.js

```javascript
async uploadPDF(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await this.$axios.post(
    'http://localhost:8000/extract',
    formData
  );
  
  this.resultado = response.data;
}
```

## ❓ Problemas Comuns

### "ModuleNotFoundError"
```bash
# Certifique-se de estar no ambiente virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstale as dependências
pip install -r requirements.txt
```

### "Port 8000 already in use"
```bash
# Mude a porta no .env
API_PORT=8001
```

### "Unable to find poppler"
**Windows:** Baixe e instale Poppler do link abaixo:
- https://github.com/oschwartz10612/poppler-windows/releases

**Linux:**
```bash
sudo apt-get install poppler-utils
```

## 📚 Próximos Passos

1. ✅ Testar com seus próprios PDFs
2. 📖 Ler a [documentação completa](README.md)
3. 🎨 Integrar com seu frontend
4. 🚀 Fazer [deploy em produção](INSTALL.md#deploy-em-cloud)
5. 🔧 Personalizar os [parsers de dados](parsers/financial_parser.py)

## 💡 Dicas

- 📄 A API funciona melhor com PDFs de **boa qualidade**
- 🖼️ PDFs escaneados devem ter pelo menos **200 DPI**
- 📦 Mantenha os arquivos abaixo de **10 MB**
- 🔄 Use a documentação interativa para testes rápidos
- 📊 Verifique o campo `confidence` para avaliar a qualidade da extração

## 🆘 Precisa de Ajuda?

1. 📖 Consulte a [documentação completa](README.md)
2. 🔍 Veja os [exemplos de código](EXAMPLES.md)
3. ⚙️ Leia o [guia de instalação](INSTALL.md)
4. 🌐 Acesse a documentação interativa em `/docs`

## ⭐ Recursos da API

- ✅ Detecção automática de tipo de PDF
- ✅ OCR para documentos escaneados
- ✅ Extração de tabelas
- ✅ Identificação de tipo de documento
- ✅ Campos financeiros estruturados
- ✅ API stateless e escalável
- ✅ Documentação OpenAPI/Swagger
- ✅ CORS habilitado
- ✅ Validação de dados com Pydantic
- ✅ Logs estruturados

---

**🚀 Agora é só começar a usar!**

Acesse: http://localhost:8000/docs
