"""Testes de integração para o fluxo completo de parsing"""
import pytest
from parsers.financial_parser import FinancialParser
from models import DadosFinanceiros


class TestFinancialParserIntegration:
    """Testes de integração do FinancialParser"""
    
    @pytest.fixture
    def parser(self):
        """Fixture que retorna uma instância do parser"""
        return FinancialParser()
    
    def test_parse_nubank_complete_flow(self, parser):
        """Testa fluxo completo de parsing de fatura Nubank"""
        text = """
Olá, João.
Esta é a sua fatura de novembro
R$ 3.038,08
Data de vencimento: 24 NOV 2025
Nubank
Total a pagar R$ 3.038,08
17 OUT
 •••• 2300 Loja A R$ 250,00
"""
        
        dados = parser.parse_financial_data(text)
        
        assert isinstance(dados, DadosFinanceiros)
        assert dados.cnpj is not None  # Deve ter CNPJ do Nubank
        assert dados.empresa is not None
        assert dados.valor_total is not None
    
    def test_parse_inter_complete_flow(self, parser):
        """Testa fluxo completo de parsing de fatura Inter"""
        text = """
Banco Inter S.A.
FATURA CARTÃO DE CRÉDITO
Data de vencimento: 10/11/2025
Total a pagar: R$ 1.500,00
15/10 Supermercado ABC R$ 350,00
"""
        
        dados = parser.parse_financial_data(text)
        
        assert isinstance(dados, DadosFinanceiros)
        assert dados.cnpj is not None  # Deve ter CNPJ do Inter
        assert dados.empresa is not None
    
    def test_parse_unknown_bank_fallback(self, parser):
        """Testa fallback para parser genérico com banco desconhecido"""
        text = """
Banco Desconhecido XYZ
Fatura de Cartão
Data de vencimento: 15/11/2025
Total: R$ 500,00
"""
        
        dados = parser.parse_financial_data(text)
        
        # Deve retornar DadosFinanceiros mesmo sem parser especializado
        assert isinstance(dados, DadosFinanceiros)
    
    def test_specialized_parser_priority(self, parser):
        """Testa que parser especializado tem prioridade sobre genérico"""
        # Texto claramente do Nubank
        text = """
Olá, João.
Esta é a sua fatura de novembro
Nubank
R$ 3.038,08
"""
        
        dados = parser.parse_financial_data(text)
        
        # Deve usar parser especializado e ter CNPJ correto
        assert dados.cnpj == "18.236.120/0001-58"
        assert dados.empresa in ["Nubank", "Nu Pagamentos S.A."]  # Aceita ambos os formatos
    
    def test_document_type_detection(self, parser):
        """Testa detecção de tipo de documento"""
        text = """
Fatura Cartão de Crédito
Nubank
Total a pagar R$ 1.000,00
"""
        
        doc_type, confidence = parser.detect_document_type(text)
        
        assert doc_type == "fatura_cartao"
        assert confidence > 0.5
