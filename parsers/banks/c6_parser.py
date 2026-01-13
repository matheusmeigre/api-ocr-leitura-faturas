"""Parser especializado para faturas do C6 Bank"""
import re
from typing import List, Optional
from models import DadosFinanceiros, ItemFinanceiro
from parsers.utils.date_parser import DateParser
from parsers.utils.cnpj_database import CNPJDatabase


class C6Parser:
    """Parser especializado para faturas do C6 Bank"""
    
    # Identificador do banco suportado
    SUPPORTED_BANK = "c6"
    
    # CNPJ do C6 Bank
    C6_CNPJ = '31.872.495/0001-72'
    C6_NAME = 'C6 Bank'
    
    def __init__(self):
        """Inicializa o parser do C6"""
        self.date_parser = DateParser()
    
    def can_parse(self, text: str) -> bool:
        """
        Verifica se o texto é uma fatura do C6 Bank.
        
        Args:
            text: Texto do documento
            
        Returns:
            True se for fatura do C6
        """
        indicators = [
            r'c6\s*bank',
            r'c6bank',
            r'banco c6',
            r'31\.872\.495/0001-72',
            r'fatura.*c6',
        ]
        
        text_lower = text.lower()
        matches = sum(1 for pattern in indicators if re.search(pattern, text_lower, re.IGNORECASE))
        
        return matches >= 2
    
    def parse(self, text: str) -> DadosFinanceiros:
        """
        Parse completo de fatura do C6 Bank.
        
        Args:
            text: Texto da fatura
            
        Returns:
            DadosFinanceiros extraídos
        """
        dados = DadosFinanceiros()
        
        # Informações do banco
        dados.empresa = self.C6_NAME
        dados.cnpj = self.C6_CNPJ
        
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
        patterns = [
            r'([A-ZÀÂÉÊÍÓÔÕÚ][A-Za-zÀ-ÿ\s]{2,50})\s*(?:FATURA|CPF)',
            r'titular[:\s]*([A-ZÀÂÉÊÍÓÔÕÚ][A-Za-zÀ-ÿ\s]{2,50})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 5 and name.lower() not in ['fatura', 'extrato', 'cartão']:
                    return name
        
        return None
    
    def _extract_transactions(self, text: str, year: Optional[int] = None) -> List[ItemFinanceiro]:
        """Extrai transações da fatura do C6"""
        items = []
        lines = text.split('\n')
        
        # Palavras-chave para ignorar
        skip_keywords = [
            'total', 'resumo', 'fatura', 'vencimento', 'emissão', 'titular',
            'cnpj', 'cpf', 'cartão', 'limite', 'pagamento'
        ]
        
        current_date = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Ignora linhas com palavras-chave de resumo
            if any(keyword in line.lower() for keyword in skip_keywords):
                continue
            
            # Verifica se a linha tem uma data no formato DD/MM
            date_match = re.match(r'^(\d{1,2}[/-]\d{1,2})', line)
            if date_match:
                date_str = date_match.group(1)
                current_date = self.date_parser.parse_date(f"{date_str}/{year}" if year else date_str, context_year=year)
                line = line[date_match.end():].strip()
            
            # Procura por valor na linha
            value_match = re.search(r'R?\$?\s*([\d.]+,\d{2})\s*$', line)
            if value_match:
                value_str = value_match.group(1)
                try:
                    value = float(value_str.replace('.', '').replace(',', '.'))
                except ValueError:
                    continue
                
                # Extrai descrição
                description = line[:value_match.start()].strip()
                
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
        
        return list(unique_items.values())[:50]
