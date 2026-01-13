"""Testes unitários para BankDetector"""
import pytest
from parsers.utils.bank_detector import BankDetector


class TestBankDetector:
    """Testes para o BankDetector"""
    
    def test_detect_nubank(self):
        """Testa detecção de fatura do Nubank"""
        text = """
        Olá, Matheus.
        Esta é a sua fatura de novembro
        Nubank
        Total a pagar R$ 3.038,08
        """
        
        result = BankDetector.detect_bank(text)
        assert result is not None
        
        bank_key, bank_name, confidence = result
        assert bank_key == "nubank"
        assert "Nubank" in bank_name
        assert confidence > 0.5
    
    def test_detect_inter(self):
        """Testa detecção de fatura do Inter"""
        text = """
        Banco Inter S.A.
        Fatura Cartão de Crédito
        Total a pagar R$ 1.500,00
        """
        
        result = BankDetector.detect_bank(text)
        assert result is not None
        
        bank_key, bank_name, confidence = result
        assert bank_key == "inter"
        assert "Inter" in bank_name
    
    def test_detect_unknown_bank(self):
        """Testa comportamento com banco desconhecido"""
        text = """
        Fatura de Cartão
        Total: R$ 500,00
        """
        
        result = BankDetector.detect_bank(text)
        # Pode retornar None ou um banco com baixa confiança
        if result:
            _, _, confidence = result
            assert confidence < 0.5
    
    def test_get_cnpj_nubank(self):
        """Testa obtenção de CNPJ do Nubank"""
        cnpj = BankDetector.get_cnpj("nubank")
        assert cnpj == "18.236.120/0001-58"
    
    def test_get_cnpj_inter(self):
        """Testa obtenção de CNPJ do Inter"""
        cnpj = BankDetector.get_cnpj("inter")
        assert cnpj == "00.416.968/0001-01"
