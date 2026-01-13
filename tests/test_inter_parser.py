"""Testes unitários para InterParser"""
import pytest
from parsers.banks.inter_parser import InterParser
from models import DadosFinanceiros


class TestInterParser:
    """Testes para o InterParser"""
    
    @pytest.fixture
    def parser(self):
        """Fixture que retorna uma instância do parser"""
        return InterParser()
    
    @pytest.fixture
    def sample_inter_text(self):
        """Texto de exemplo de fatura Inter (anonimizado)"""
        return """
Banco Inter S.A.
00.416.968/0001-01

MARIA SANTOS
FATURA CARTÃO DE CRÉDITO

Data de emissão: 15/10/2025
Data de vencimento: 10/11/2025

Total a pagar: R$ 1.500,00

LANÇAMENTOS
15/10 Supermercado ABC R$ 350,00
16/10 Farmácia XYZ - Parcela 1/3 R$ 150,00
17/10 Loja de Roupas R$ 200,00
18/10 Restaurante R$ 100,00
"""
    
    def test_can_parse_inter(self, parser, sample_inter_text):
        """Testa se o parser reconhece fatura do Inter"""
        result = parser.can_parse(sample_inter_text)
        assert result is True
    
    def test_can_parse_non_inter(self, parser):
        """Testa se o parser rejeita fatura de outro banco"""
        text = "Nubank - Esta é a sua fatura"
        result = parser.can_parse(text)
        assert result is False
    
    def test_parse_basic_fields(self, parser, sample_inter_text):
        """Testa extração de campos básicos"""
        dados = parser.parse(sample_inter_text)
        
        assert isinstance(dados, DadosFinanceiros)
        assert dados.empresa == "Banco Inter S.A."
        assert dados.cnpj == "00.416.968/0001-01"
        assert dados.valor_total == 1500.00
        assert dados.data_emissao == "2025-10-15"
        assert dados.data_vencimento == "2025-11-10"
    
    def test_parse_transactions(self, parser, sample_inter_text):
        """Testa extração de transações"""
        dados = parser.parse(sample_inter_text)
        
        assert dados.itens is not None
        assert len(dados.itens) >= 3
        
        # Verifica que transações foram extraídas
        for item in dados.itens:
            assert item.descricao is not None
            assert item.valor is not None
            # Data pode ser None dependendo do formato
    
    def test_supported_bank_attribute(self, parser):
        """Testa se o atributo SUPPORTED_BANK está definido"""
        assert hasattr(InterParser, 'SUPPORTED_BANK')
        assert InterParser.SUPPORTED_BANK == "inter"
    
    def test_parse_parceled_transaction(self, parser, sample_inter_text):
        """Testa se parser identifica transações parceladas"""
        dados = parser.parse(sample_inter_text)
        
        # Procura por item com "Parcela" na descrição
        parceled = [item for item in dados.itens if "Parcela" in item.descricao]
        assert len(parceled) > 0
