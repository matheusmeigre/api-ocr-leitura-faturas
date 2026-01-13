"""Base de dados de CNPJs conhecidos de instituições financeiras"""
from typing import Optional, Dict


class CNPJDatabase:
    """Database de CNPJs de bancos e instituições financeiras"""
    
    # CNPJs conhecidos de bancos brasileiros
    KNOWN_CNPJS: Dict[str, str] = {
        # Bancos Digitais
        'nubank': '18.236.120/0001-58',
        'nu pagamentos': '18.236.120/0001-58',
        'inter': '00.416.968/0001-01',
        'banco inter': '00.416.968/0001-01',
        'c6 bank': '31.872.495/0001-72',
        'c6': '31.872.495/0001-72',
        'picpay': '14.176.050/0001-70',
        'neon': '20.855.875/0001-40',
        'next': '92.894.922/0001-08',
        'original': '92.894.922/0001-08',
        'banco original': '92.894.922/0001-08',
        'will bank': '36.113.876/0001-91',
        'will': '36.113.876/0001-91',
        
        # Bancos Tradicionais
        'banco do brasil': '00.000.000/0001-91',
        'bb': '00.000.000/0001-91',
        'itau': '60.701.190/0001-04',
        'itaú': '60.701.190/0001-04',
        'bradesco': '60.746.948/0001-12',
        'santander': '90.400.888/0001-42',
        'caixa': '00.360.305/0001-04',
        'caixa economica': '00.360.305/0001-04',
        'caixa econômica': '00.360.305/0001-04',
        'safra': '58.160.789/0001-28',
        'banco safra': '58.160.789/0001-28',
        'btg': '30.306.294/0001-45',
        'btg pactual': '30.306.294/0001-45',
        'citibank': '33.479.023/0001-80',
        'hsbc': '01.701.201/0001-89',
        'banrisul': '92.702.067/0001-96',
        
        # Fintechs e Cartões
        'creditas': '17.262.245/0001-78',
        'stone': '16.501.555/0001-57',
        'pagseguro': '08.561.701/0001-01',
        'mercado pago': '10.573.521/0001-91',
        'paypal': '10.573.521/0001-91',
        'american express': '74.173.113/0001-00',
        'amex': '74.173.113/0001-00',
    }
    
    # Aliases de nomes
    NAME_ALIASES: Dict[str, str] = {
        'nu pagamentos sa': 'nubank',
        'nu pagamentos s.a.': 'nubank',
        'nu pagamentos': 'nubank',
        'banco inter sa': 'inter',
        'banco inter s.a.': 'inter',
        'itau unibanco': 'itau',
        'itaú unibanco': 'itau',
        'banco bradesco sa': 'bradesco',
        'banco bradesco s.a.': 'bradesco',
    }
    
    @classmethod
    def get_cnpj_by_name(cls, bank_name: str) -> Optional[str]:
        """
        Busca CNPJ pelo nome do banco.
        
        Args:
            bank_name: Nome do banco (case-insensitive)
            
        Returns:
            CNPJ formatado ou None se não encontrado
        """
        if not bank_name:
            return None
        
        # Normaliza o nome
        name_lower = bank_name.lower().strip()
        
        # Remove caracteres especiais comuns
        name_normalized = name_lower.replace('.', '').replace('-', '').strip()
        
        # Busca direta
        if name_normalized in cls.KNOWN_CNPJS:
            return cls.KNOWN_CNPJS[name_normalized]
        
        # Busca por alias
        if name_normalized in cls.NAME_ALIASES:
            alias = cls.NAME_ALIASES[name_normalized]
            return cls.KNOWN_CNPJS.get(alias)
        
        # Busca parcial (se o nome contém alguma palavra-chave)
        for key, cnpj in cls.KNOWN_CNPJS.items():
            if key in name_normalized or name_normalized in key:
                return cnpj
        
        return None
    
    @classmethod
    def identify_bank(cls, text: str) -> Optional[tuple[str, str]]:
        """
        Identifica o banco a partir do texto do documento.
        
        Args:
            text: Texto do documento
            
        Returns:
            Tupla (nome_do_banco, cnpj) ou None
        """
        text_lower = text.lower()
        
        # Procura por menções diretas aos bancos
        for bank_key in cls.KNOWN_CNPJS.keys():
            if bank_key in text_lower:
                cnpj = cls.KNOWN_CNPJS[bank_key]
                # Retorna o nome mais amigável
                bank_name = cls._get_friendly_name(bank_key)
                return (bank_name, cnpj)
        
        return None
    
    @classmethod
    def _get_friendly_name(cls, key: str) -> str:
        """Retorna nome amigável do banco"""
        name_mapping = {
            'nubank': 'Nubank',
            'nu pagamentos': 'Nubank',
            'inter': 'Banco Inter',
            'c6': 'C6 Bank',
            'c6 bank': 'C6 Bank',
            'picpay': 'PicPay',
            'banco do brasil': 'Banco do Brasil',
            'bb': 'Banco do Brasil',
            'itau': 'Itaú',
            'bradesco': 'Bradesco',
            'santander': 'Santander',
            'caixa': 'Caixa Econômica Federal',
        }
        
        return name_mapping.get(key, key.title())
    
    @classmethod
    def format_cnpj(cls, cnpj: str) -> str:
        """
        Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX.
        
        Args:
            cnpj: CNPJ (com ou sem formatação)
            
        Returns:
            CNPJ formatado
        """
        # Remove tudo que não é dígito
        import re
        digits = re.sub(r'\D', '', cnpj)
        
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        
        return cnpj
