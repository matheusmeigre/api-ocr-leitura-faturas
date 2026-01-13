"""Testes para o parser do PicPay"""
import pytest
from parsers.banks.picpay_parser import PicPayParser
from models import DadosFinanceiros


class TestPicPayParser:
    """Testes do parser especializado do PicPay"""
    
    @pytest.fixture
    def parser(self):
        """Fixture do parser PicPay"""
        return PicPayParser()
    
    @pytest.fixture
    def picpay_invoice_text(self):
        """Fixture com texto simulado de fatura do PicPay"""
        return """
        PICPAY
        Fatura do Cartão de Crédito
        
        Cliente: MARIA SANTOS
        CNPJ: 22.896.431/0001-10
        
        Data de Fechamento: 20/11/2024
        Data de Vencimento: 05/12/2024
        
        RESUMO
        Total a Pagar: R$ 1.850,50
        Referência: 202411002
        
        COMPRAS
        02/11 AMAZON                        R$ 250,00
        05/11 SPOTIFY                       R$ 21,90
        10/11 IFOOD                         R$ 89,00
        15/11 FARMACIA                      R$ 65,00
        18/11 SHOPPING                      R$ 420,00
        """
    
    def test_can_parse_picpay_invoice(self, parser, picpay_invoice_text):
        """Testa se detecta fatura do PicPay"""
        assert parser.can_parse(picpay_invoice_text) is True
    
    def test_cannot_parse_non_picpay_invoice(self, parser):
        """Testa que não detecta faturas de outros bancos"""
        other_text = """
        NUBANK
        Fatura do Cartão de Crédito
        Total: R$ 500,00
        """
        assert parser.can_parse(other_text) is False
    
    def test_parse_basic_info(self, parser, picpay_invoice_text):
        """Testa extração de informações básicas"""
        result = parser.parse(picpay_invoice_text)
        
        assert isinstance(result, DadosFinanceiros)
        assert result.empresa == 'PicPay'
        assert result.cnpj == '22.896.431/0001-10'
        assert result.data_emissao == '2024-11-20'
        assert result.data_vencimento == '2024-12-05'
        assert result.valor_total == 1850.50
    
    def test_parse_transactions(self, parser, picpay_invoice_text):
        """Testa extração de transações"""
        result = parser.parse(picpay_invoice_text)
        
        assert len(result.itens) >= 5
        
        # Verifica primeira transação
        first_item = result.itens[0]
        assert 'AMAZON' in first_item.descricao
        assert first_item.valor == 250.00
        assert first_item.data == '2024-11-02'
    
    def test_parse_with_cnpj(self, parser):
        """Testa que detecta PicPay mesmo com apenas CNPJ"""
        text_with_cnpj = """
        Fatura Cartão
        22.896.431/0001-10
        PicPay
        Total: R$ 800,00
        """
        assert parser.can_parse(text_with_cnpj) is True
        result = parser.parse(text_with_cnpj)
        assert result.cnpj == '22.896.431/0001-10'
    
    def test_supported_bank_attribute(self, parser):
        """Testa se tem o atributo SUPPORTED_BANK definido"""
        assert hasattr(parser, 'SUPPORTED_BANK')
        assert parser.SUPPORTED_BANK == 'picpay'
