"""Testes unitários para DateParser"""
import pytest
from parsers.utils.date_parser import DateParser


class TestDateParser:
    """Testes para o DateParser"""
    
    def test_parse_date_abreviada(self):
        """Testa parsing de data abreviada (formato Nubank)"""
        parser = DateParser(default_year=2025)
        
        result = parser.parse_date("17 OUT")
        assert result == "2025-10-17"
        
        result = parser.parse_date("24 NOV")
        assert result == "2025-11-24"
    
    def test_parse_date_tradicional(self):
        """Testa parsing de data tradicional DD/MM/YYYY"""
        parser = DateParser()
        
        result = parser.parse_date("17/10/2025")
        assert result == "2025-10-17"
        
        result = parser.parse_date("24-11-2025")
        assert result == "2025-11-24"
    
    def test_parse_date_por_extenso(self):
        """Testa parsing de data por extenso"""
        parser = DateParser()
        
        result = parser.parse_date("17 de outubro de 2025")
        assert result == "2025-10-17"
    
    def test_infer_year_from_context(self):
        """Testa inferência de ano do contexto"""
        parser = DateParser()
        
        text = "FATURA 24 NOV 2025 EMISSÃO E ENVIO 17 NOV 2025"
        year = parser.infer_year_from_context(text)
        
        assert year == 2025
    
    def test_extract_all_dates(self):
        """Testa extração de todas as datas"""
        parser = DateParser(default_year=2025)
        
        text = """
        17 OUT
        18 OUT
        Data de vencimento: 24/11/2025
        """
        
        dates = parser.extract_all_dates(text)
        assert len(dates) >= 3
        assert any("2025-10-17" in date[1] for date in dates)
        assert any("2025-11-24" in date[1] for date in dates)
    
    def test_extract_emission_date(self):
        """Testa extração de data de emissão com contexto"""
        parser = DateParser(default_year=2025)
        
        text = "EMISSÃO E ENVIO 17 NOV 2025"
        result = parser.extract_emission_date(text)
        
        assert result == "2025-11-17"
    
    def test_extract_due_date(self):
        """Testa extração de data de vencimento com contexto"""
        parser = DateParser(default_year=2025)
        
        text = "Data de vencimento: 24 NOV 2025"
        result = parser.extract_due_date(text)
        
        assert result == "2025-11-24"
