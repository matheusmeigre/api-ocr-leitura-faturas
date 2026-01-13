"""Parser de datas com suporte a múltiplos formatos"""
import re
from datetime import datetime
from typing import Optional, List, Tuple


class DateParser:
    """Parser de datas que suporta múltiplos formatos brasileiros"""
    
    # Mapeamento de meses abreviados em português
    MONTH_ABBR_PT = {
        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4,
        'MAI': 5, 'JUN': 6, 'JUL': 7, 'AGO': 8,
        'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
    }
    
    # Mapeamento de meses por extenso
    MONTH_FULL_PT = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    # Padrões de data suportados
    PATTERNS = [
        # DD/MM/YYYY ou DD-MM-YYYY
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', 'numeric'),
        # DD MMM (ex: 17 OUT, 24 NOV)
        (r'\b(\d{1,2})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\b', 'abbr'),
        # DD de MMM de YYYY (ex: 17 de outubro de 2025)
        (r'\b(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\b', 'full'),
    ]
    
    def __init__(self, default_year: Optional[int] = None):
        """
        Inicializa o parser de datas.
        
        Args:
            default_year: Ano padrão para datas que não incluem ano (ex: "17 OUT")
        """
        self.default_year = default_year or datetime.now().year
    
    def parse_date(self, date_str: str, context_year: Optional[int] = None) -> Optional[str]:
        """
        Parse de uma data em vários formatos possíveis.
        
        Args:
            date_str: String contendo a data
            context_year: Ano do contexto (usado se data não tiver ano)
            
        Returns:
            Data no formato YYYY-MM-DD ou None se não conseguir parsear
        """
        year = context_year or self.default_year
        
        for pattern, format_type in self.PATTERNS:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if format_type == 'numeric':
                        day, month, year_found = match.groups()
                        return f"{int(year_found):04d}-{int(month):02d}-{int(day):02d}"
                    
                    elif format_type == 'abbr':
                        day, month_abbr = match.groups()
                        month = self.MONTH_ABBR_PT.get(month_abbr.upper())
                        if month:
                            return f"{year:04d}-{month:02d}-{int(day):02d}"
                    
                    elif format_type == 'full':
                        day, month_name, year_found = match.groups()
                        month = self.MONTH_FULL_PT.get(month_name.lower())
                        if month:
                            return f"{int(year_found):04d}-{month:02d}-{int(day):02d}"
                
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def extract_all_dates(self, text: str, context_year: Optional[int] = None) -> List[Tuple[str, str]]:
        """
        Extrai todas as datas encontradas no texto.
        
        Args:
            text: Texto para extrair datas
            context_year: Ano do contexto
            
        Returns:
            Lista de tuplas (data_original, data_normalizada)
        """
        results = []
        year = context_year or self.default_year
        
        for pattern, format_type in self.PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                original = match.group()
                normalized = self.parse_date(original, context_year=year)
                if normalized:
                    results.append((original, normalized))
        
        return results
    
    def infer_year_from_context(self, text: str) -> Optional[int]:
        """
        Tenta inferir o ano do documento a partir do contexto.
        Procura por padrões como "FATURA 24 NOV 2025" ou "ano de 2025".
        
        Args:
            text: Texto do documento
            
        Returns:
            Ano inferido ou None
        """
        # Procura por anos de 4 dígitos
        year_pattern = r'\b(20\d{2})\b'
        matches = re.findall(year_pattern, text)
        
        if matches:
            # Retorna o ano mais comum
            from collections import Counter
            year_counts = Counter(matches)
            most_common_year = year_counts.most_common(1)[0][0]
            return int(most_common_year)
        
        return None
    
    def extract_emission_date(self, text: str) -> Optional[str]:
        """Extrai data de emissão com contexto específico"""
        emission_patterns = [
            r'(?:data de )?emiss[aã]o[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:EMISS[AÃ]O)[:\s]*(\d{1,2}\s+\w+\s+\d{4})',
            r'emitid[ao] em[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        year = self.infer_year_from_context(text)
        
        for pattern in emission_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                return self.parse_date(date_str, context_year=year)
        
        # Se não encontrou contexto específico, tenta todas as datas
        dates = self.extract_all_dates(text, context_year=year)
        return dates[0][1] if dates else None
    
    def extract_due_date(self, text: str) -> Optional[str]:
        """Extrai data de vencimento com contexto específico"""
        due_patterns = [
            r'(?:data de )?vencimento[:\s]*(\d{1,2}\s+\w+\s+\d{4})',
            r'(?:data de )?vencimento[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'vence em[:\s]*(\d{1,2}\s+\w+\s+\d{4})',
            r'vence em[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'pagar até[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        year = self.infer_year_from_context(text)
        
        for pattern in due_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                return self.parse_date(date_str, context_year=year)
        
        # Se não encontrou contexto específico, tenta a última data
        dates = self.extract_all_dates(text, context_year=year)
        return dates[-1][1] if dates else None
