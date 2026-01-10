"""
Script auxiliar para testar a API localmente
"""
import requests
import json
import sys
from pathlib import Path


def test_api(pdf_path: str, api_url: str = "http://localhost:8000/extract"):
    """
    Testa a API com um arquivo PDF.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        api_url: URL da API
    """
    # Verifica se o arquivo existe
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ Arquivo não encontrado: {pdf_path}")
        return
    
    print(f"📄 Enviando arquivo: {pdf_file.name}")
    print(f"🌐 URL da API: {api_url}")
    print("-" * 60)
    
    try:
        # Faz a requisição
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file.name, f, 'application/pdf')}
            response = requests.post(api_url, files=files)
        
        # Verifica status
        if response.status_code == 200:
            print("✅ Requisição bem sucedida!")
            print("-" * 60)
            
            # Parse do JSON
            data = response.json()
            
            # Exibe resultado formatado
            print("\n📊 RESULTADO DA EXTRAÇÃO:\n")
            print(f"Tipo de documento: {data.get('document_type', 'N/A')}")
            print(f"Confiança: {data.get('confidence', 0):.2%}")
            print(f"Tipo de PDF: {data.get('metadata', {}).get('pdf_type', 'N/A')}")
            print(f"Páginas: {data.get('metadata', {}).get('pages', 'N/A')}")
            
            print("\n💰 DADOS FINANCEIROS:\n")
            financial_data = data.get('data', {})
            
            for key, value in financial_data.items():
                if value and key != 'itens':
                    print(f"  {key}: {value}")
            
            # Itens
            items = financial_data.get('itens', [])
            if items:
                print(f"\n  📋 Itens encontrados: {len(items)}")
                for i, item in enumerate(items[:5], 1):  # Mostra apenas os 5 primeiros
                    print(f"    {i}. {item.get('descricao', 'N/A')} - R$ {item.get('valor', 0):.2f}")
                if len(items) > 5:
                    print(f"    ... e mais {len(items) - 5} itens")
            
            # Salva resultado completo
            output_file = pdf_file.stem + '_resultado.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Resultado completo salvo em: {output_file}")
            
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(response.json())
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("   Certifique-se de que o servidor está rodando em", api_url)
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_api.py <caminho_do_pdf> [url_api]")
        print("\nExemplo:")
        print("  python test_api.py documento.pdf")
        print("  python test_api.py documento.pdf http://localhost:8000/extract")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000/extract"
    
    test_api(pdf_path, api_url)
