import re
import logging
import json
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from models import DadosFinanceiros, ItemFinanceiro

# Importa parsers especializados
try:
    from parsers.banks.nubank_parser import NubankParser
    from parsers.banks.inter_parser import InterParser
    from parsers.banks.c6_parser import C6Parser
    from parsers.banks.picpay_parser import PicPayParser
    from parsers.utils.date_parser import DateParser
    from parsers.utils.bank_detector import BankDetector
    from parsers.utils.cnpj_database import CNPJDatabase
    from parsers.utils.parser_cache import ParserCache
    from config import settings
    SPECIALIZED_PARSERS_AVAILABLE = True
except ImportError as e:
    SPECIALIZED_PARSERS_AVAILABLE = False
    print(f"Aviso: Parsers especializados não disponíveis. Erro: {e}")

# Logger estruturado para rastreamento
logger = logging.getLogger(__name__)


class FinancialParser:
    """Classe para parsing de dados financeiros de documentos com suporte a parsers especializados"""
    
    # Padrões regex para extração
    PATTERNS = {
        "cnpj": r'\b\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}\b',
        "cpf": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
        "data": r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',
        "data_alt": r'\b\d{2}\s+de\s+\w+\s+de\s+\d{4}\b',
        "valor": r'R?\$?\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})',
        "codigo_barras": r'\b\d{47,48}\b',
        "linha_digitavel": r'\b\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d{1}\s+\d{14}\b'
    }
    
    # Palavras-chave para identificação de tipo de documento
    DOCUMENT_KEYWORDS = {
        "boleto": ["boleto", "código de barras", "linha digitável", "banco do brasil", "caixa econômica", "bradesco", "itaú", "santander"],
        "fatura_cartao": ["fatura", "cartão de crédito", "limite disponível", "pagamento mínimo", "vencimento da fatura"],
        "nota_fiscal": ["nota fiscal", "nf-e", "danfe", "destinatário", "natureza da operação"],
        "extrato": ["extrato", "saldo anterior", "saldo atual", "lançamentos"]
    }
    
    def __init__(self):
        """Inicializa o parser"""
        # Inicializa parsers especializados se disponíveis
        self.specialized_parsers = {}
        if SPECIALIZED_PARSERS_AVAILABLE:
            self.specialized_parsers['nubank'] = NubankParser()
            self.specialized_parsers['inter'] = InterParser()
            self.specialized_parsers['c6'] = C6Parser()
            self.specialized_parsers['picpay'] = PicPayParser()
            self.date_parser = DateParser()
            self.bank_detector = BankDetector()
            self.cnpj_db = CNPJDatabase()
            
            # Inicializa cache (transparente e opcional)
            self.cache = ParserCache(
                ttl_seconds=settings.parser_cache_ttl_seconds,
                max_size=settings.parser_cache_max_size,
                enabled=settings.parser_cache_enabled
            )
        else:
            self.date_parser = None
            self.bank_detector = None
            self.cnpj_db = None
            self.cache = None
    
    def _log_parser_selection(self, event_data: Dict[str, Any]) -> None:
        """
        Registra log estruturado sobre seleção de parser.
        
        Args:
            event_data: Dados do evento de parsing
        """
        log_entry = {
            "event": "parser_selection",
            "timestamp": datetime.now().isoformat(),
            **event_data
        }
        logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        Retorna estatísticas do cache (se disponível).
        
        Returns:
            Dict com estatísticas ou None se cache não disponível
        """
        if self.cache:
            return self.cache.get_stats()
        return None
    
    def detect_document_type(self, text: str) -> Tuple[str, float]:
        """
        Detecta o tipo de documento baseado em palavras-chave.
        
        Args:
            text: Texto do documento
            
        Returns:
            Tuple (tipo, confiança)
        """
        text_lower = text.lower()
        scores = {}
        
        for doc_type, keywords in self.DOCUMENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[doc_type] = score
        
        if not scores or max(scores.values()) == 0:
            return "desconhecido", 0.0
        
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        confidence = min(1.0, max_score / 3)  # Normaliza até 3 palavras-chave
        
        return best_type, confidence
    
    def extract_cnpj(self, text: str) -> Optional[str]:
        """Extrai CNPJ do texto"""
        match = re.search(self.PATTERNS["cnpj"], text)
        if match:
            cnpj = match.group()
            # Normaliza formato
            cnpj = re.sub(r'\D', '', cnpj)
            if len(cnpj) == 14:
                return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return None
    
    def extract_cpf(self, text: str) -> Optional[str]:
        """Extrai CPF do texto"""
        match = re.search(self.PATTERNS["cpf"], text)
        if match:
            cpf = match.group()
            # Normaliza formato
            cpf = re.sub(r'\D', '', cpf)
            if len(cpf) == 11:
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return None
    
    def extract_dates(self, text: str) -> List[str]:
        """Extrai todas as datas do texto"""
        dates = []
        
        # Busca padrão DD/MM/YYYY ou DD-MM-YYYY
        for match in re.finditer(self.PATTERNS["data"], text):
            date_str = match.group()
            # Normaliza para formato YYYY-MM-DD
            date_str = date_str.replace('/', '-')
            parts = date_str.split('-')
            if len(parts) == 3:
                try:
                    # Valida data
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        dates.append(f"{year:04d}-{month:02d}-{day:02d}")
                except:
                    pass
        
        return dates
    
    def extract_emission_date(self, text: str) -> Optional[str]:
        """Extrai data de emissão"""
        dates = self.extract_dates(text)
        
        # Procura por contexto de emissão
        emission_patterns = [
            r'(?:data de )?emiss[aã]o[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'emitid[ao] em[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})'
        ]
        
        for pattern in emission_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).replace('/', '-')
                parts = date_str.split('-')
                if len(parts) == 3:
                    day, month, year = parts[0], parts[1], parts[2]
                    return f"{year}-{month}-{day}"
        
        # Se não encontrou contexto, retorna a primeira data
        return dates[0] if dates else None
    
    def extract_due_date(self, text: str) -> Optional[str]:
        """Extrai data de vencimento"""
        dates = self.extract_dates(text)
        
        # Procura por contexto de vencimento
        due_patterns = [
            r'(?:data de )?vencimento[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'vence em[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'pagar até[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})'
        ]
        
        for pattern in due_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).replace('/', '-')
                parts = date_str.split('-')
                if len(parts) == 3:
                    day, month, year = parts[0], parts[1], parts[2]
                    return f"{year}-{month}-{day}"
        
        # Se não encontrou contexto, retorna a última data
        return dates[-1] if dates else None
    
    def parse_value(self, value_str: str) -> Optional[float]:
        """Converte string de valor para float"""
        try:
            # Remove R$ e espaços
            value_str = value_str.replace('R$', '').replace('R', '').strip()
            # Remove pontos de milhar e substitui vírgula por ponto
            value_str = value_str.replace('.', '').replace(',', '.')
            return float(value_str)
        except:
            return None
    
    def extract_values(self, text: str) -> List[float]:
        """Extrai todos os valores monetários do texto"""
        values = []
        
        for match in re.finditer(self.PATTERNS["valor"], text):
            value_str = match.group()
            value = self.parse_value(value_str)
            if value is not None:
                values.append(value)
        
        return values
    
    def extract_total_value(self, text: str) -> Optional[float]:
        """Extrai o valor total do documento"""
        # Procura por contexto de valor total
        total_patterns = [
            r'(?:valor )?total[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))',
            r'(?:valor )?a pagar[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))',
            r'total geral[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                return self.parse_value(value_str)
        
        # Se não encontrou contexto, retorna o maior valor
        values = self.extract_values(text)
        return max(values) if values else None
    
    def extract_company_name(self, text: str) -> Optional[str]:
        """Extrai nome da empresa do documento"""
        lines = text.split('\n')
        
        # Procura por padrões comuns de nome de empresa
        for i, line in enumerate(lines[:10]):  # Verifica primeiras 10 linhas
            line = line.strip()
            
            # Se tem CNPJ na linha ou próxima, provavelmente é o nome da empresa
            if re.search(self.PATTERNS["cnpj"], line) or (i + 1 < len(lines) and re.search(self.PATTERNS["cnpj"], lines[i + 1])):
                # Pega a linha anterior ou atual como nome
                if i > 0 and len(lines[i - 1].strip()) > 3:
                    return lines[i - 1].strip()
                elif len(line) > 3:
                    return line.strip()
            
            # Procura por palavras-chave de empresa
            if any(word in line.lower() for word in ['ltda', 's.a.', 's/a', 'eireli', 'me', 'epp']):
                return line.strip()
        
        # Se não encontrou, retorna a primeira linha não vazia com tamanho razoável
        for line in lines[:5]:
            if 5 < len(line.strip()) < 100:
                return line.strip()
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """Extrai número do documento"""
        patterns = [
            r'(?:n[úu]mero|n[ºo]|numero)[:\s]*(\d+)',
            r'(?:fatura|documento|nota)[:\s]*n[ºo]?\s*(\d+)',
            r'(?:nf-e|nfe)[:\s]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def parse_financial_data(self, text: str, document_type: str = None) -> DadosFinanceiros:
        """
        Parse completo dos dados financeiros com suporte a parsers especializados.
        
        Args:
            text: Texto do documento
            document_type: Tipo do documento (opcional)
            
        Returns:
            DadosFinanceiros com todos os campos extraídos
        """
        # Tenta usar parser especializado se disponível
        if SPECIALIZED_PARSERS_AVAILABLE and self.specialized_parsers:
            # Tenta obter detecção do cache
            bank_detection = None
            if self.cache:
                bank_detection = self.cache.get_bank_detection(text)
            
            # Se não está no cache, detecta o banco
            if bank_detection is None:
                bank_detection = self.bank_detector.detect_bank(text)
                
                # Armazena no cache
                if bank_detection and self.cache:
                    self.cache.set_bank_detection(text, bank_detection)
            
            if bank_detection:
                bank_key, bank_name, confidence = bank_detection
                
                # Verifica se temos parser especializado para este banco
                if bank_key in self.specialized_parsers:
                    parser = self.specialized_parsers[bank_key]
                    parser_name = parser.__class__.__name__
                    
                    # Verifica se o parser pode processar este documento
                    if hasattr(parser, 'can_parse') and parser.can_parse(text):
                        try:
                            # Log: usando parser especializado
                            self._log_parser_selection({
                                "bank": bank_key,
                                "bank_name": bank_name,
                                "parser": parser_name,
                                "confidence": round(confidence, 3),
                                "fallback": False,
                                "reason": None
                            })
                            
                            # Usa parser especializado
                            dados = parser.parse(text)
                            # Se CNPJ não foi encontrado, tenta buscar do banco de dados
                            if not dados.cnpj and bank_key:
                                dados.cnpj = self.bank_detector.get_cnpj(bank_key)
                            return dados
                        except Exception as e:
                            # Log: fallback por erro
                            self._log_parser_selection({
                                "bank": bank_key,
                                "bank_name": bank_name,
                                "parser": "GenericParser",
                                "confidence": round(confidence, 3),
                                "fallback": True,
                                "reason": f"specialized_parser_error: {str(e)}"
                            })
                            logger.warning(f"Parser especializado falhou, usando genérico. Erro: {e}")
                else:
                    # Log: banco detectado mas sem parser especializado
                    self._log_parser_selection({
                        "bank": bank_key,
                        "bank_name": bank_name,
                        "parser": "GenericParser",
                        "confidence": round(confidence, 3),
                        "fallback": True,
                        "reason": "no_specialized_parser_available"
                    })
            else:
                # Log: banco não detectado
                self._log_parser_selection({
                    "bank": "unknown",
                    "bank_name": "Unknown",
                    "parser": "GenericParser",
                    "confidence": 0.0,
                    "fallback": True,
                    "reason": "bank_not_detected"
                })
        else:
            # Log: parsers especializados não disponíveis
            self._log_parser_selection({
                "bank": "unknown",
                "bank_name": "Unknown",
                "parser": "GenericParser",
                "confidence": 0.0,
                "fallback": True,
                "reason": "specialized_parsers_not_available"
            })
        
        # Fallback: usa parser genérico
        dados = DadosFinanceiros()
        
        # Tenta detectar banco e adicionar CNPJ conhecido
        if SPECIALIZED_PARSERS_AVAILABLE and self.bank_detector:
            bank_info = self.bank_detector.detect_bank(text)
            if bank_info:
                bank_key, bank_name, confidence = bank_info
                dados.empresa = bank_name
                dados.cnpj = self.bank_detector.get_cnpj(bank_key)
        
        # Extrai campos básicos com parser genérico
        if not dados.empresa:
            dados.empresa = self.extract_company_name(text)
        if not dados.cnpj:
            dados.cnpj = self.extract_cnpj(text)
        
        dados.cpf = self.extract_cpf(text)
        
        # Usa DateParser melhorado se disponível
        if SPECIALIZED_PARSERS_AVAILABLE and self.date_parser:
            year = self.date_parser.infer_year_from_context(text)
            dados.data_emissao = self.date_parser.extract_emission_date(text)
            dados.data_vencimento = self.date_parser.extract_due_date(text)
        else:
            dados.data_emissao = self.extract_emission_date(text)
            dados.data_vencimento = self.extract_due_date(text)
        
        dados.valor_total = self.extract_total_value(text)
        dados.numero_documento = self.extract_document_number(text)
        
        # Extrai campos específicos de boleto
        if document_type == "boleto":
            codigo_barras = re.search(self.PATTERNS["codigo_barras"], text)
            if codigo_barras:
                dados.codigo_barras = codigo_barras.group()
            
            linha_digitavel = re.search(self.PATTERNS["linha_digitavel"], text)
            if linha_digitavel:
                dados.linha_digitavel = linha_digitavel.group()
        
        # Extrai itens
        dados.itens = self.extract_items(text)
        
        return dados
    
    def calculate_extraction_confidence(self, dados: DadosFinanceiros, document_type: str = None) -> float:
        """
        Calcula um score de confiança baseado nos campos extraídos.
        
        Args:
            dados: Dados financeiros extraídos
            document_type: Tipo do documento
            
        Returns:
            Score de confiança de 0.0 a 1.0
        """
        score = 0.0
        max_score = 0.0
        
        # Pontuação por campo (campos mais importantes valem mais)
        field_weights = {
            'empresa': 0.15,
            'cnpj': 0.15,
            'cpf': 0.10,
            'data_emissao': 0.10,
            'data_vencimento': 0.15,
            'valor_total': 0.20,
            'numero_documento': 0.10,
            'itens': 0.05
        }
        
        # Campos específicos de boleto
        if document_type == "boleto":
            field_weights['codigo_barras'] = 0.15
            field_weights['linha_digitavel'] = 0.15
        
        # Calcula score
        for field, weight in field_weights.items():
            max_score += weight
            value = getattr(dados, field, None)
            
            if value:
                if isinstance(value, list) and len(value) > 0:
                    score += weight
                elif isinstance(value, (str, float, int)) and value:
                    score += weight
        
        # Normaliza para 0-1
        confidence = score / max_score if max_score > 0 else 0.0
        
        return round(confidence, 3)
    
    def extract_items(self, text: str) -> List[ItemFinanceiro]:
        """
        Extrai itens/linhas do documento.
        Esta é uma implementação básica que pode ser melhorada.
        """
        items = []
        
        # Procura por padrões de item com descrição e valor
        # Exemplo: "Serviço de internet R$ 100,00"
        pattern = r'(.+?)\s+R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))'
        
        lines = text.split('\n')
        for line in lines:
            match = re.search(pattern, line)
            if match:
                descricao = match.group(1).strip()
                valor_str = match.group(2)
                valor = self.parse_value(valor_str)
                
                # Filtra descrições muito curtas ou muito longas
                if valor and 5 < len(descricao) < 100:
                    items.append(ItemFinanceiro(
                        descricao=descricao,
                        valor=valor
                    ))
        
        return items[:20]  # Limita a 20 itens
