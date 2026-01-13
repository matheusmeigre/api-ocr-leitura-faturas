# Exemplos de Uso da API

Este documento contém exemplos práticos de como usar a API de OCR.

## Índice

1. [cURL](#curl)
2. [Python](#python)
3. [JavaScript/Node.js](#javascript)
4. [TypeScript/Next.js](#typescript)
5. [PHP](#php)

---

## cURL

### Exemplo básico

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/caminho/para/documento.pdf"
```

### Com saída formatada (usando jq)

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@documento.pdf" | jq '.'
```

### Salvando resultado em arquivo

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@documento.pdf" \
  -o resultado.json
```

---

## Python

### Exemplo básico com requests

```python
import requests

# URL da API
url = "http://localhost:8000/extract"

# Abre e envia o arquivo
with open("documento.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

# Processa resposta
if response.status_code == 200:
    data = response.json()
    
    if data["success"]:
        print(f"Tipo: {data['document_type']}")
        print(f"Empresa: {data['data']['empresa']}")
        print(f"Valor: R$ {data['data']['valor_total']:.2f}")
    else:
        print(f"Erro: {data.get('error')}")
else:
    print(f"Erro HTTP: {response.status_code}")
```

### Exemplo com tratamento de erros

```python
import requests
from pathlib import Path

def extrair_dados_pdf(caminho_pdf: str) -> dict:
    """
    Extrai dados de um PDF usando a API.
    """
    try:
        # Verifica se arquivo existe
        pdf_path = Path(caminho_pdf)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_pdf}")
        
        # Faz requisição
        url = "http://localhost:8000/extract"
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = requests.post(url, files=files, timeout=30)
        
        # Verifica resposta
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar à API")
        return None
    except requests.exceptions.Timeout:
        print("Erro: Timeout na requisição")
        return None
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None

# Uso
resultado = extrair_dados_pdf("fatura.pdf")
if resultado and resultado.get("success"):
    print("Dados extraídos com sucesso!")
    print(resultado["data"])
```

### Processamento em lote

```python
import requests
from pathlib import Path
import json

def processar_lote_pdfs(diretorio: str):
    """
    Processa todos os PDFs de um diretório.
    """
    url = "http://localhost:8000/extract"
    pasta = Path(diretorio)
    
    # Lista todos os PDFs
    pdfs = list(pasta.glob("*.pdf"))
    print(f"Encontrados {len(pdfs)} arquivos PDF")
    
    resultados = []
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"\nProcessando {i}/{len(pdfs)}: {pdf.name}")
        
        try:
            with open(pdf, "rb") as f:
                files = {"file": (pdf.name, f, "application/pdf")}
                response = requests.post(url, files=files)
            
            if response.status_code == 200:
                data = response.json()
                resultados.append({
                    "arquivo": pdf.name,
                    "sucesso": data.get("success"),
                    "tipo": data.get("document_type"),
                    "valor": data.get("data", {}).get("valor_total")
                })
                print(f"  ✓ Sucesso - Valor: R$ {data['data'].get('valor_total', 0):.2f}")
            else:
                print(f"  ✗ Erro: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Erro: {str(e)}")
    
    # Salva resumo
    with open("resumo.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Processamento concluído. Resumo salvo em resumo.json")

# Uso
processar_lote_pdfs("./documentos")
```

---

## JavaScript

### Exemplo com Fetch API

```javascript
async function extrairDadosPDF(arquivo) {
  const formData = new FormData();
  formData.append('file', arquivo);

  try {
    const response = await fetch('http://localhost:8000/extract', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.success) {
      console.log('Tipo:', data.document_type);
      console.log('Empresa:', data.data.empresa);
      console.log('Valor:', data.data.valor_total);
      return data;
    } else {
      console.error('Erro:', data.error);
      return null;
    }
  } catch (error) {
    console.error('Erro ao processar:', error);
    return null;
  }
}

// Uso com input file
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const arquivo = e.target.files[0];
  if (arquivo && arquivo.type === 'application/pdf') {
    const resultado = await extrairDadosPDF(arquivo);
    // Processar resultado...
  }
});
```

### Exemplo com Axios

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function extrairDados(caminhoArquivo) {
  const form = new FormData();
  form.append('file', fs.createReadStream(caminhoArquivo));

  try {
    const response = await axios.post('http://localhost:8000/extract', form, {
      headers: form.getHeaders(),
      maxContentLength: Infinity,
      maxBodyLength: Infinity
    });

    return response.data;
  } catch (error) {
    console.error('Erro:', error.message);
    return null;
  }
}

// Uso
extrairDados('./documento.pdf').then(data => {
  if (data && data.success) {
    console.log('Dados extraídos:', data.data);
  }
});
```

---

## TypeScript

### Componente React/Next.js

```typescript
import { useState } from 'react';

interface DadosFinanceiros {
  empresa: string;
  cnpj: string;
  data_emissao: string;
  data_vencimento: string;
  valor_total: number;
  moeda: string;
}

interface RespostaAPI {
  success: boolean;
  document_type: string;
  confidence: number;
  raw_text: string;
  data: DadosFinanceiros;
  metadata: Record<string, any>;
}

export default function UploadPDF() {
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<RespostaAPI | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const arquivo = event.target.files?.[0];
    
    if (!arquivo) return;
    
    if (arquivo.type !== 'application/pdf') {
      setErro('Por favor, selecione um arquivo PDF');
      return;
    }

    setLoading(true);
    setErro(null);

    const formData = new FormData();
    formData.append('file', arquivo);

    try {
      const response = await fetch('http://localhost:8000/extract', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }

      const data: RespostaAPI = await response.json();
      
      if (data.success) {
        setResultado(data);
      } else {
        setErro('Falha ao processar documento');
      }
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Upload de Fatura</h1>
      
      <input
        type="file"
        accept=".pdf"
        onChange={handleUpload}
        disabled={loading}
        className="mb-4"
      />

      {loading && <p>Processando...</p>}
      
      {erro && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {erro}
        </div>
      )}

      {resultado && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          <h2 className="font-bold">Dados Extraídos:</h2>
          <p>Tipo: {resultado.document_type}</p>
          <p>Empresa: {resultado.data.empresa}</p>
          <p>Valor: R$ {resultado.data.valor_total?.toFixed(2)}</p>
          <p>Vencimento: {resultado.data.data_vencimento}</p>
        </div>
      )}
    </div>
  );
}
```

### Hook customizado

```typescript
import { useState } from 'react';

interface UseUploadPDF {
  upload: (arquivo: File) => Promise<void>;
  loading: boolean;
  erro: string | null;
  resultado: RespostaAPI | null;
  resetar: () => void;
}

export function useUploadPDF(apiUrl: string = 'http://localhost:8000/extract'): UseUploadPDF {
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resultado, setResultado] = useState<RespostaAPI | null>(null);

  const upload = async (arquivo: File) => {
    setLoading(true);
    setErro(null);
    setResultado(null);

    const formData = new FormData();
    formData.append('file', arquivo);

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setResultado(data);
      } else {
        setErro(data.error || 'Erro ao processar documento');
      }
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const resetar = () => {
    setErro(null);
    setResultado(null);
  };

  return { upload, loading, erro, resultado, resetar };
}

// Uso
function MeuComponente() {
  const { upload, loading, erro, resultado } = useUploadPDF();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const arquivo = e.target.files?.[0];
    if (arquivo) {
      upload(arquivo);
    }
  };

  // ... resto do componente
}
```

---

## PHP

### Exemplo básico

```php
<?php

function extrairDadosPDF($caminhoArquivo) {
    $url = 'http://localhost:8000/extract';
    
    $curl = curl_init();
    
    $file = new CURLFile($caminhoArquivo, 'application/pdf', basename($caminhoArquivo));
    
    curl_setopt_array($curl, [
        CURLOPT_URL => $url,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => ['file' => $file],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => ['Content-Type: multipart/form-data'],
    ]);
    
    $response = curl_exec($curl);
    $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    
    curl_close($curl);
    
    if ($httpCode === 200) {
        return json_decode($response, true);
    }
    
    return null;
}

// Uso
$resultado = extrairDadosPDF('./documento.pdf');

if ($resultado && $resultado['success']) {
    echo "Empresa: " . $resultado['data']['empresa'] . "\n";
    echo "Valor: R$ " . number_format($resultado['data']['valor_total'], 2, ',', '.') . "\n";
} else {
    echo "Erro ao processar documento\n";
}
?>
```

---

## Tratamento de Erros Comuns

### Python

```python
def processar_com_retry(caminho_pdf, max_tentativas=3):
    """Processa PDF com retry automático"""
    import time
    
    for tentativa in range(max_tentativas):
        try:
            response = requests.post(
                "http://localhost:8000/extract",
                files={"file": open(caminho_pdf, "rb")},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                # Erro de validação, não adianta tentar novamente
                print(f"Erro de validação: {response.json()}")
                return None
            else:
                # Erro do servidor, tenta novamente
                if tentativa < max_tentativas - 1:
                    print(f"Tentativa {tentativa + 1} falhou, tentando novamente...")
                    time.sleep(2 ** tentativa)  # Backoff exponencial
                    
        except requests.exceptions.Timeout:
            print(f"Timeout na tentativa {tentativa + 1}")
            if tentativa < max_tentativas - 1:
                time.sleep(2)
        except Exception as e:
            print(f"Erro: {str(e)}")
            return None
    
    print("Todas as tentativas falharam")
    return None
```

---

## Integração com Bancos de Dados

### Salvar resultado no PostgreSQL

```python
import psycopg2
import requests
import json

def salvar_no_banco(caminho_pdf):
    # Extrai dados
    response = requests.post(
        "http://localhost:8000/extract",
        files={"file": open(caminho_pdf, "rb")}
    )
    
    if response.status_code != 200:
        return False
    
    data = response.json()
    if not data.get("success"):
        return False
    
    # Conecta ao banco
    conn = psycopg2.connect(
        host="localhost",
        database="financeiro",
        user="user",
        password="password"
    )
    
    cursor = conn.cursor()
    
    # Insere dados
    cursor.execute("""
        INSERT INTO documentos_financeiros 
        (tipo, empresa, cnpj, data_emissao, data_vencimento, valor_total, dados_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        data["document_type"],
        data["data"].get("empresa"),
        data["data"].get("cnpj"),
        data["data"].get("data_emissao"),
        data["data"].get("data_vencimento"),
        data["data"].get("valor_total"),
        json.dumps(data)
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True
```

---

Para mais exemplos e documentação, acesse: `http://localhost:8000/docs`
