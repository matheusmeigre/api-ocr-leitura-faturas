"""Testes para o parser do C6 Bank"""
import pytest
from parsers.banks.c6_parser import C6Parser
from models import DadosFinanceiros


class TestC6Parser:
    """Testes do parser especializado do C6 Bank"""
    
    @pytest.fixture
    def parser(self):
        """Fixture do parser C6"""
        return C6Parser()
    
    @pytest.fixture
    def c6_invoice_text(self):
        """Fixture com texto simulado de fatura do C6 Bank"""
        return """
        C6 BANK
        Fatura do Cartão de Crédito
        
        Titular: JOAO SILVA
        CNPJ: 31.872.495/0001-72
        
        Data de Emissão: 15/11/2024
        Data de Vencimento: 10/12/2024
        
        RESUMO DA FATURA
        Total a Pagar: R$ 2.450,00
        Número da Fatura: 202411001
        
        LANÇAMENTOS
        05/11 MERCADO LIVRE                 R$ 150,00
        08/11 NETFLIX                       R$ 39,90
        12/11 UBER                          R$ 45,50
        15/11 RESTAURANTE ABC               R$ 120,00
        20/11 POSTO DE GASOLINA            R$ 280,00
        """
    
    def test_can_parse_c6_invoice(self, parser, c6_invoice_text):
        """Testa se detecta fatura do C6 Bank"""
        assert parser.can_parse(c6_invoice_text) is True
    
    def test_cannot_parse_non_c6_invoice(self, parser):
        """Testa que não detecta faturas de outros bancos"""
        other_text = """
        NUBANK
        Fatura do Cartão de Crédito
        Total: R$ 500,00
        """
        assert parser.can_parse(other_text) is False
    
    def test_parse_basic_info(self, parser, c6_invoice_text):
        """Testa extração de informações básicas"""
        result = parser.parse(c6_invoice_text)
        
        assert isinstance(result, DadosFinanceiros)
        assert result.empresa == 'C6 Bank'
        assert result.cnpj == '31.872.495/0001-72'
        assert result.data_emissao == '2024-11-15'
        assert result.data_vencimento == '2024-12-10'
        assert result.valor_total == 2450.00
    
    def test_parse_transactions(self, parser, c6_invoice_text):
        """Testa extração de transações"""
        result = parser.parse(c6_invoice_text)
        
        assert len(result.itens) >= 5
        
        # Verifica primeira transação
        first_item = result.itens[0]
        assert 'MERCADO LIVRE' in first_item.descricao
        assert first_item.valor == 150.00
        assert first_item.data == '2024-11-05'
    
    def test_parse_with_cnpj(self, parser):
        """Testa que detecta C6 mesmo com apenas CNPJ"""
        text_with_cnpj = """
        Fatura Cartão
        31.872.495/0001-72
        C6 Bank
        Total: R$ 1000,00
        """
        assert parser.can_parse(text_with_cnpj) is True
        result = parser.parse(text_with_cnpj)
        assert result.cnpj == '31.872.495/0001-72'
    
    def test_supported_bank_attribute(self, parser):
        """Testa se tem o atributo SUPPORTED_BANK definido"""
        assert hasattr(parser, 'SUPPORTED_BANK')
        assert parser.SUPPORTED_BANK == 'c6'
