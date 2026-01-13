"""Parser especializado para faturas do Banco Inter"""
import re
from typing import List, Optional
from models import DadosFinanceiros, ItemFinanceiro
from parsers.utils.date_parser import DateParser
from parsers.utils.cnpj_database import CNPJDatabase


class InterParser:
    """Parser especializado para faturas do Banco Inter"""
    
    # Identificador do banco suportado
    SUPPORTED_BANK = "inter"
    
    # CNPJ do Banco Inter
    INTER_CNPJ = '00.416.968/0001-01'
    INTER_NAME = 'Banco Inter S.A.'
    
    def __init__(self):
        """Inicializa o parser do Inter"""
        self.date_parser = DateParser()
    
    def can_parse(self, text: str) -> bool:
        """
        Verifica se o texto é uma fatura do Banco Inter.
        
        Args:
            text: Texto do documento
            
        Returns:
            True se for fatura do Inter
        """
        indicators = [
            r'banco inter',
            r'\binter\b',
            r'inter s\.?a\.?',
            r'fatura.*cart[aã]o.*cr[eé]dito',
            r'00\.416\.968/0001-01',
        ]
        
        text_lower = text.lower()
        matches = sum(1 for pattern in indicators if re.search(pattern, text_lower, re.IGNORECASE))
        
        return matches >= 2
    
    def parse(self, text: str) -> DadosFinanceiros:
        """
        Parse completo de fatura do Banco Inter.
        
        Args:
            text: Texto da fatura
            
        Returns:
            DadosFinanceiros extraídos
        """
        dados = DadosFinanceiros()
        
        # Informações do banco
        dados.empresa = self.INTER_NAME
        dados.cnpj = self.INTER_CNPJ
        
        # Infere ano do contexto
        year = self.date_parser.infer_year_from_context(text)
        
        # Extrai datas
        dados.data_emissao = self._extract_emission_date(text, year)
        dados.data_vencimento = self._extract_due_date(text, year)
        
        # Extrai valores
        dados.valor_total = self._extract_total_value(text)
        
        # Extrai número do documento
        dados.numero_documento = self._extract_document_number(text)
        
        # Extrai titular
        titular = self._extract_holder_name(text)
        if titular:
            dados.numero_documento = f"Fatura {titular}"
        
        # Extrai itens/transações
        dados.itens = self._extract_transactions(text, year)
        
        return dados
    
    def _extract_emission_date(self, text: str, year: Optional[int] = None) -> Optional[str]:
        """Extrai data de emissão"""
        patterns = [
            r'(?:data de )?emiss[aã]o[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:data de )?emiss[aã]o[:\s]*(\d{1,2}\s+(?:JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ))',
            r'emitid[ao] em[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed = self.date_parser.parse_date(date_str, context_year=year)
                if parsed:
                    return parsed
        
        return self.date_parser.extract_emission_date(text)
    
    def _extract_due_date(self, text: str, year: Optional[int] = None) -> Optional[str]:
        """Extrai data de vencimento"""
        patterns = [
            r'(?:data de )?vencimento[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:data de )?vencimento[:\s]*(\d{1,2}\s+(?:JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ))',
            r'vence em[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'pagar at[eé][:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed = self.date_parser.parse_date(date_str, context_year=year)
                if parsed:
                    return parsed
        
        return self.date_parser.extract_due_date(text)
    
    def _extract_total_value(self, text: str) -> Optional[float]:
        """Extrai valor total da fatura"""
        patterns = [
            r'(?:valor )?total[:\s]*R?\$?\s*([\d.,]+)',
            r'total a pagar[:\s]*R?\$?\s*([\d.,]+)',
            r'total da fatura[:\s]*R?\$?\s*([\d.,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                try:
                    # Remove pontos de milhar e substitui vírgula por ponto
                    value_str = value_str.replace('.', '').replace(',', '.')
                    return float(value_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_document_number(self, text: str) -> Optional[str]:
        """Extrai número do documento/fatura"""
        patterns = [
            r'fatura[:\s]*n[°º]?\s*(\d+)',
            r'n[úu]mero[:\s]*(\d+)',
            r'documento[:\s]*n[°º]?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_holder_name(self, text: str) -> Optional[str]:
        """Extrai nome do titular"""
        # Procura por padrões comuns de nome antes de "FATURA" ou "CPF"
        patterns = [
            r'([A-ZÀÂÉÊÍÓÔÕÚ][A-Za-zÀ-ÿ\s]{2,50})\s*(?:FATURA|CPF)',
            r'titular[:\s]*([A-ZÀÂÉÊÍÓÔÕÚ][A-Za-zÀ-ÿ\s]{2,50})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Valida que não é um título genérico
                if len(name) > 5 and name.lower() not in ['fatura', 'extrato', 'cartão']:
                    return name
        
        return None
    
    def _extract_transactions(self, text: str, year: Optional[int] = None) -> List[ItemFinanceiro]:
        """
        Extrai transações da fatura do Inter.
        Suporta múltiplos formatos incluindo parcelamento.
        """
        items = []
        lines = text.split('\n')
        
        # Padrão para transações com data e valor na mesma linha
        pattern = r'(\d{1,2}[/-]\d{1,2})\s+(.+?)\s+R?\$?\s*([\d.,]+)'
        
        current_date = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Verifica se a linha tem uma data abreviada no início
            date_match = re.match(r'^(\d{1,2})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)', line, re.IGNORECASE)
            if date_match:
                date_str = f"{date_match.group(1)} {date_match.group(2)}"
                current_date = self.date_parser.parse_date(date_str, context_year=year)
                # Remove a data da linha para processar o resto
                line = line[date_match.end():].strip()
            
            # Procura por valor na linha
            value_match = re.search(r'R?\$?\s*([\d.]+,\d{2})\s*$', line)
            if value_match:
                value_str = value_match.group(1)
                try:
                    value = float(value_str.replace('.', '').replace(',', '.'))
                except ValueError:
                    continue
                
                # Extrai descrição (tudo antes do valor)
                description = line[:value_match.start()].strip()
                
                # Remove caracteres especiais comuns
                description = description.replace('•', '').strip()
                
                if description and 3 < len(description) < 200:
                    items.append(ItemFinanceiro(
                        descricao=description,
                        valor=value,
                        data=current_date
                    ))
        
        # Remove duplicatas (proteção adicional)
        unique_items = {}
        for item in items:
            key = f"{item.data}|{item.descricao}|{item.valor}"
            if key not in unique_items:
                unique_items[key] = item
        
        return list(unique_items.values())[:50]  # Limita a 50 itens
