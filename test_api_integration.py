"""Teste final da integração completa com API"""
import requests
import json

# URL da API (ajuste se necessário)
API_URL = "http://localhost:8000/extract"

# Caminho do arquivo
PDF_PATH = r"c:\Users\Matheus Meigre\Downloads\Nubank_2025-11-24.pdf"

print("=" * 80)
print("TESTE DE INTEGRAÇÃO COMPLETA - API + Parser Especializado Nubank")
print("=" * 80)

try:
    # Abre o arquivo
    with open(PDF_PATH, 'rb') as f:
        files = {'file': ('fatura_nubank.pdf', f, 'application/pdf')}
        
        print("\n📤 Enviando arquivo para API...")
        response = requests.post(API_URL, files=files, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("\n✅ SUCESSO!")
        
        data = response.json()
        
        print("\n" + "=" * 80)
        print("DADOS EXTRAÍDOS:")
        print("=" * 80)
        
        financial_data = data.get('data', {})
        
        print(f"\n🏦 Banco/Empresa: {financial_data.get('empresa')}")
        print(f"📋 CNPJ: {financial_data.get('cnpj')}")
        print(f"📅 Data Emissão: {financial_data.get('data_emissao')}")
        print(f"📅 Data Vencimento: {financial_data.get('data_vencimento')}")
        print(f"💰 Valor Total: R$ {financial_data.get('valor_total')}")
        print(f"🔢 Número Documento: {financial_data.get('numero_documento')}")
        
        itens = financial_data.get('itens', [])
        print(f"\n📊 Total de Itens: {len(itens)}")
        
        if itens:
            print("\n📝 Primeiros 5 Itens:")
            print("-" * 80)
            for i, item in enumerate(itens[:5], 1):
                data_item = item.get('data', 'N/A')
                descricao = item.get('descricao', 'N/A')
                valor = item.get('valor', 0)
                print(f"{i}. [{data_item}] {descricao}: R$ {valor:.2f}")
        
        # Verifica se todos os itens têm data
        items_com_data = sum(1 for item in itens if item.get('data'))
        print(f"\n✅ Itens com data: {items_com_data}/{len(itens)}")
        
        # Verifica campos críticos
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE CAMPOS CRÍTICOS:")
        print("=" * 80)
        
        validations = {
            "CNPJ presente": bool(financial_data.get('cnpj')),
            "CNPJ correto (Nubank)": financial_data.get('cnpj') == '18.236.120/0001-58',
            "Data vencimento presente": bool(financial_data.get('data_vencimento')),
            "Valor total presente": bool(financial_data.get('valor_total')),
            "Valor total correto": financial_data.get('valor_total') == 3038.08,
            "Todos itens com data": items_com_data == len(itens) if itens else False,
        }
        
        for check, passed in validations.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        
        all_passed = all(validations.values())
        
        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 TODOS OS TESTES PASSARAM!")
            print("Sistema está funcionando perfeitamente!")
        else:
            print("⚠️ ALGUNS TESTES FALHARAM")
            print("Verifique os campos acima")
        print("=" * 80)
        
    else:
        print("\n❌ ERRO!")
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERRO: Não foi possível conectar à API")
    print("Certifique-se de que a API está rodando:")
    print("  python main.py")
    print("  ou")
    print("  uvicorn main:app --reload")
    
except FileNotFoundError:
    print(f"\n❌ ERRO: Arquivo não encontrado")
    print(f"Caminho: {PDF_PATH}")
    
except Exception as e:
    print(f"\n❌ ERRO INESPERADO: {e}")
    import traceback
    traceback.print_exc()
