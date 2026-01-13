"""Parser especializado para faturas do Nubank"""
import re
from typing import List, Optional
from models import DadosFinanceiros, ItemFinanceiro
from parsers.utils.date_parser import DateParser
from parsers.utils.cnpj_database import CNPJDatabase


class NubankParser:
    """Parser especializado para faturas do Nubank"""
    
    # Identificador do banco suportado
    SUPPORTED_BANK = "nubank"
    
    # CNPJ do Nubank (conhecido, não aparece na fatura)
    NUBANK_CNPJ = '18.236.120/0001-58'
    NUBANK_NAME = 'Nu Pagamentos S.A.'
    
    def __init__(self):
        """Inicializa o parser do Nubank"""
        self.date_parser = DateParser()
    
    def can_parse(self, text: str) -> bool:
        """
        Verifica se o texto é uma fatura do Nubank.
        
        Args:
            text: Texto do documento
            
        Returns:
            True se for fatura do Nubank
        """
        indicators = [
            r'nubank',
            r'nu pagamentos',
            r'Olá.*Esta é a sua fatura',
            r'Total a pagar R\$',
            r'Data de vencimento:.*NOV|DEZ|JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT',
        ]
        
        text_lower = text.lower()
        matches = sum(1 for pattern in indicators if re.search(pattern, text, re.IGNORECASE))
        
        return matches >= 2
    
    def parse(self, text: str) -> DadosFinanceiros:
        """
        Parse completo de fatura do Nubank.
        
        Args:
            text: Texto da fatura
            
        Returns:
            DadosFinanceiros extraídos
        """
        dados = DadosFinanceiros()
        
        # Informações fixas do Nubank
        dados.empresa = self.NUBANK_NAME
        dados.cnpj = self.NUBANK_CNPJ
        
        # Infere o ano do documento
        year = self.date_parser.infer_year_from_context(text) or 2025
        
        # Extrai datas
        dados.data_vencimento = self._extract_due_date(text, year)
        dados.data_emissao = self._extract_emission_date(text, year)
        
        # Extrai valores
        dados.valor_total = self._extract_total_value(text)
        
        # Extrai nome do titular
        titular = self._extract_holder_name(text)
        if titular:
            dados.numero_documento = f"Fatura {titular}"
        
        # Extrai itens/transações
        dados.itens = self._extract_transactions(text, year)
        
        return dados
    
    def _extract_due_date(self, text: str, year: int) -> Optional[str]:
        """Extrai data de vencimento no formato do Nubank"""
        # Padrão: "Data de vencimento: 24 NOV 2025"
        pattern = r'Data de vencimento:\s*(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            day, month, year_found = match.groups()
            date_str = f"{day} {month}"
            return self.date_parser.parse_date(date_str, context_year=int(year_found))
        
        # Fallback: procura por "vencimento" + data abreviada
        pattern_alt = r'vencimento:\s*(\d{1,2}\s+\w+)'
        match_alt = re.search(pattern_alt, text, re.IGNORECASE)
        if match_alt:
            return self.date_parser.parse_date(match_alt.group(1), context_year=year)
        
        return None
    
    def _extract_emission_date(self, text: str, year: int) -> Optional[str]:
        """Extrai data de emissão no formato do Nubank"""
        # Padrão: "EMISSÃO E ENVIO 17 NOV 2025"
        pattern = r'EMISS[AÃ]O E ENVIO\s+(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            day, month, year_found = match.groups()
            date_str = f"{day} {month}"
            return self.date_parser.parse_date(date_str, context_year=int(year_found))
        
        return None
    
    def _extract_total_value(self, text: str) -> Optional[float]:
        """Extrai o valor total da fatura"""
        # Padrão: "Total a pagar R$ 3.038,08"
        pattern = r'Total a pagar\s+R\$\s*([\d.,]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            value_str = match.group(1)
            return self._parse_value(value_str)
        
        # Fallback: procura no cabeçalho
        pattern_alt = r'no valor de\s+R\$\s*([\d.,]+)'
        match_alt = re.search(pattern_alt, text, re.IGNORECASE)
        if match_alt:
            value_str = match_alt.group(1)
            return self._parse_value(value_str)
        
        return None
    
    def _extract_holder_name(self, text: str) -> Optional[str]:
        """Extrai o nome do titular do cartão"""
        # Padrão: Nome em CAPS antes de "FATURA"
        pattern = r'([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s]{10,})\s+FATURA'
        match = re.search(pattern, text)
        
        if match:
            name = match.group(1).strip()
            # Remove palavras comuns que não são nomes
            exclude_words = ['RESUMO', 'TRANSAÇÕES', 'PRÓXIMAS', 'LIMITES']
            if not any(word in name for word in exclude_words):
                return name.title()
        
        return None
    
    def _extract_transactions(self, text: str, year: int) -> List[ItemFinanceiro]:
        """
        Extrai transações da fatura do Nubank.
        
        Filtra apenas COMPRAS, excluindo:
        - Pagamentos (valores negativos)
        - Créditos (valores negativos)
        - Juros e IOF
        
        Formato típico:
        17 OUT •••• 2300 Moreira Vidracaria - Parcela 2/3 R$ 250,00
        
        Ou formato alternativo (múltiplas linhas):
        17 OUT
         •••• 2300 Moreira Vidracaria - Parcela 2/3 R$ 250,00
        """
        items = []
        
        # Divide o texto em linhas
        lines = text.split('\n')
        
        # Padrão de transação em UMA linha (formato novo):
        # "17 OUT •••• 2300 Moreira Vidracaria - Parcela 2/3 R$ 250,00"
        single_line_pattern = r'^(\d{1,2})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s+[•●*]+\s+\d{4}\s+(.+?)\s+R\$\s*([\d.,]+)$'
        
        # Padrão de data sozinha (formato antigo)
        date_pattern = r'^(\d{1,2})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)$'
        
        # Padrão de transação sem data (formato antigo):
        # " •••• 2300 Moreira Vidracaria - Parcela 2/3 R$ 250,00"
        transaction_pattern = r'^\s*[•●*]+\s+\d{4}\s+(.+?)\s+R\$\s*([\d.,]+)$'
        
        # Padrões para EXCLUIR (não são compras)
        exclude_patterns = [
            r'Pagamento',
            r'Crédito',
            r'Juros',
            r'IOF',
            r'Saldo',
            r'^-',  # Valores negativos
            r'−'    # Sinal de menos unicode
        ]
        
        current_date = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # Tenta formato de UMA linha (novo)
            match_single = re.match(single_line_pattern, line_stripped, re.IGNORECASE)
            if match_single:
                day, month, descricao, valor_str = match_single.groups()
                
                # Verifica se deve excluir esta transação
                should_exclude = any(
                    re.search(pattern, line_stripped, re.IGNORECASE) 
                    for pattern in exclude_patterns
                )
                
                if not should_exclude:
                    valor = self._parse_value(valor_str)
                    
                    # Filtra descrições muito curtas ou valores inválidos
                    if valor and valor > 0 and len(descricao) > 2:
                        # Parse da data
                        date_str = f"{day} {month}"
                        data = self.date_parser.parse_date(date_str, context_year=year)
                        
                        items.append(ItemFinanceiro(
                            descricao=descricao.strip(),
                            valor=valor,
                            data=data
                        ))
                continue
            
            # Tenta formato de MÚLTIPLAS linhas (antigo)
            # Primeiro verifica se é uma linha de data
            match_date = re.match(date_pattern, line_stripped, re.IGNORECASE)
            if match_date:
                day, month = match_date.groups()
                date_str = f"{day} {month}"
                current_date = self.date_parser.parse_date(date_str, context_year=year)
                continue
            
            # Depois verifica se é uma transação (precisa ter data corrente)
            match_transaction = re.match(transaction_pattern, line_stripped, re.IGNORECASE)
            if match_transaction and current_date:
                descricao, valor_str = match_transaction.groups()
                
                # Verifica se deve excluir esta transação
                should_exclude = any(
                    re.search(pattern, line_stripped, re.IGNORECASE) 
                    for pattern in exclude_patterns
                )
                
                if not should_exclude:
                    valor = self._parse_value(valor_str)
                    
                    # Filtra descrições muito curtas ou valores inválidos
                    if valor and valor > 0 and len(descricao) > 2:
                        items.append(ItemFinanceiro(
                            descricao=descricao.strip(),
                            valor=valor,
                            data=current_date
                        ))
        
        # Remove duplicatas (proteção adicional)
        # Cria chave única: data + descrição + valor
        unique_items = {}
        for item in items:
            key = f"{item.data}|{item.descricao}|{item.valor}"
            if key not in unique_items:
                unique_items[key] = item
        
        return list(unique_items.values())
    
    def _parse_value(self, value_str: str) -> Optional[float]:
        """Converte string de valor para float"""
        try:
            # Remove R$ e espaços
            value_str = value_str.replace('R$', '').replace('R', '').strip()
            # Remove pontos de milhar e substitui vírgula por ponto
            value_str = value_str.replace('.', '').replace(',', '.')
            return float(value_str)
        except:
            return None
