"""Detector automático de banco/instituição financeira"""
import re
from typing import Optional, Tuple
from .cnpj_database import CNPJDatabase


class BankDetector:
    """Detecta automaticamente o banco emissor do documento"""
    
    # Padrões específicos de identificação
    BANK_PATTERNS = {
        'nubank': [
            r'nubank',
            r'nu pagamentos',
            r'roxinho',  # apelido popular
            r'Olá.*Esta é a sua fatura',  # Padrão de abertura do Nubank
        ],
        'inter': [
            r'banco inter',
            r'inter',
            r'banco inter s\.?a\.?',
        ],
        'c6': [
            r'c6 bank',
            r'c6bank',
            r'banco c6',
        ],
        'picpay': [
            r'picpay',
            r'pic pay',
        ],
        'itau': [
            r'ita[uú]',
            r'itau unibanco',
            r'ita[uú] unibanco',
        ],
        'bradesco': [
            r'bradesco',
        ],
        'santander': [
            r'santander',
        ],
        'bb': [
            r'banco do brasil',
            r'\bbb\b',
        ],
        'caixa': [
            r'caixa econ[oô]mica',
            r'caixa',
        ],
    }
    
    @classmethod
    def detect_bank(cls, text: str) -> Optional[Tuple[str, str, float]]:
        """
        Detecta o banco a partir do texto.
        
        Args:
            text: Texto do documento
            
        Returns:
            Tupla (banco_key, nome_amigavel, confianca) ou None
        """
        text_lower = text.lower()
        
        scores = {}
        
        # Verifica cada padrão de banco
        for bank_key, patterns in cls.BANK_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches
            
            if score > 0:
                scores[bank_key] = score
        
        if not scores:
            return None
        
        # Pega o banco com maior score
        best_bank = max(scores, key=scores.get)
        max_score = scores[best_bank]
        
        # Calcula confiança (normaliza até 5 menções)
        confidence = min(1.0, max_score / 3.0)
        
        # Busca informações do banco
        bank_info = CNPJDatabase.identify_bank(text)
        if bank_info:
            bank_name, cnpj = bank_info
        else:
            bank_name = cls._get_friendly_name(best_bank)
            cnpj = CNPJDatabase.get_cnpj_by_name(best_bank)
        
        return (best_bank, bank_name, confidence)
    
    @classmethod
    def get_cnpj(cls, bank_key: str) -> Optional[str]:
        """Retorna o CNPJ do banco"""
        return CNPJDatabase.get_cnpj_by_name(bank_key)
    
    @classmethod
    def _get_friendly_name(cls, bank_key: str) -> str:
        """Retorna nome amigável do banco"""
        name_mapping = {
            'nubank': 'Nubank',
            'inter': 'Banco Inter',
            'c6': 'C6 Bank',
            'picpay': 'PicPay',
            'itau': 'Itaú Unibanco',
            'bradesco': 'Bradesco',
            'santander': 'Santander',
            'bb': 'Banco do Brasil',
            'caixa': 'Caixa Econômica Federal',
        }
        
        return name_mapping.get(bank_key, bank_key.title())
