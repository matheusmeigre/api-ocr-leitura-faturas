"""Testes unitários para NubankParser"""
import pytest
from parsers.banks.nubank_parser import NubankParser
from models import DadosFinanceiros


class TestNubankParser:
    """Testes para o NubankParser"""
    
    @pytest.fixture
    def parser(self):
        """Fixture que retorna uma instância do parser"""
        return NubankParser()
    
    @pytest.fixture
    def sample_nubank_text(self):
        """Texto de exemplo de fatura Nubank (anonimizado)"""
        return """
Olá, João.
Esta é a sua fatura de
novembro, no valor de
R$ 3.038,08
Data de vencimento: 24 NOV 2025
Período vigente: 17 OUT a 17 NOV
Limite total do cartão de crédito: R$ 9.100,00

JOÃO SILVA
FATURA 24 NOV 2025 EMISSÃO E ENVIO 17 NOV 2025

RESUMO DA FATURA ATUAL
Total a pagar R$ 3.038,08

TRANSAÇÕES DE 17 OUT A 17 NOV
17 OUT
 •••• 2300 Loja A - Parcela 2/3 R$ 250,00
17 OUT
 •••• 2300 Loja B R$ 117,56
18 OUT
 •••• 2300 Loja C R$ 100,00
"""
    
    def test_can_parse_nubank(self, parser, sample_nubank_text):
        """Testa se o parser reconhece fatura do Nubank"""
        result = parser.can_parse(sample_nubank_text)
        assert result is True
    
    def test_can_parse_non_nubank(self, parser):
        """Testa se o parser rejeita fatura de outro banco"""
        text = "Banco Inter - Fatura de cartão"
        result = parser.can_parse(text)
        assert result is False
    
    def test_parse_basic_fields(self, parser, sample_nubank_text):
        """Testa extração de campos básicos"""
        dados = parser.parse(sample_nubank_text)
        
        assert isinstance(dados, DadosFinanceiros)
        assert dados.empresa == "Nu Pagamentos S.A."
        assert dados.cnpj == "18.236.120/0001-58"
        assert dados.valor_total == 3038.08
        assert dados.data_vencimento == "2025-11-24"
    
    def test_parse_transactions(self, parser, sample_nubank_text):
        """Testa extração de transações"""
        dados = parser.parse(sample_nubank_text)
        
        assert dados.itens is not None
        assert len(dados.itens) >= 3
        
        # Verifica primeiro item
        primeiro_item = dados.itens[0]
        assert primeiro_item.descricao is not None
        assert primeiro_item.valor is not None
        assert primeiro_item.data is not None
        
        # Verifica que datas foram parseadas corretamente
        assert primeiro_item.data == "2025-10-17"
    
    def test_supported_bank_attribute(self, parser):
        """Testa se o atributo SUPPORTED_BANK está definido"""
        assert hasattr(NubankParser, 'SUPPORTED_BANK')
        assert NubankParser.SUPPORTED_BANK == "nubank"
