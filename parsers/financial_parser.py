import re
import logging
import json
import time
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from models import DadosFinanceiros, ItemFinanceiro

# Importa logger estruturado
from core.logging.structured_logger import get_logger

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
    from parsers.utils.parser_metrics import ParserMetrics
    from parsers.utils.ml_classifier import MLBankClassifier
    from parsers.utils.feedback_system import FeedbackSystem
    from parsers.utils.community_templates import CommunityTemplateSystem
    from config import settings
    SPECIALIZED_PARSERS_AVAILABLE = True
except ImportError as e:
    SPECIALIZED_PARSERS_AVAILABLE = False
    print(f"Aviso: Parsers especializados não disponíveis. Erro: {e}")

# Logger estruturado para rastreamento
logger = get_logger(__name__)


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
            
            # Inicializa sistema de métricas
            self.metrics = ParserMetrics()
            
            # ONDA 3: Inteligência e Comunidade
            self.ml_classifier = MLBankClassifier()
            self.feedback_system = FeedbackSystem()
            self.template_system = CommunityTemplateSystem()
        else:
            self.date_parser = None
            self.bank_detector = None
            self.cnpj_db = None
            self.cache = None
            self.metrics = None
            self.ml_classifier = None
            self.feedback_system = None
            self.template_system = None
    
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
    
    def get_metrics_summary(self) -> Optional[Dict[str, Any]]:
        """
        Retorna resumo das métricas coletadas.
        
        Returns:
            Dict com métricas agregadas ou None se não disponível
        """
        if self.metrics:
            return self.metrics.get_summary()
        return None
    
    def export_metrics_json(self) -> Optional[str]:
        """
        Exporta métricas em formato JSON.
        
        Returns:
            String JSON ou None se métricas não disponíveis
        """
        if self.metrics:
            return self.metrics.export_json()
        return None
    
    def log_metrics_summary(self):
        """Loga resumo das métricas (se disponível)"""
        if self.metrics:
            self.metrics.log_summary()
    
    def reset_metrics(self):
        """Reseta as métricas coletadas"""
        if self.metrics:
            self.metrics.reset()
    
    def detect_document_type(self, text: str) -> Tuple[str, float]:
        """
        Detecta o tipo de documento baseado em palavras-chave.
        
        Args:
            text: Texto do documento
            
        Returns:
            Tuple (tipo, confiança)
        """
        start_time = time.time()
        text_lower = text.lower()
        scores = {}
        
        logger.debug(
            "Document type detection started",
            event="document_detection_start",
            text_length=len(text)
        )
        
        for doc_type, keywords in self.DOCUMENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[doc_type] = score
        
        if not scores or max(scores.values()) == 0:
            logger.info(
                "Document type unknown",
                event="document_detection_unknown",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            return "desconhecido", 0.0
        
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        confidence = min(1.0, max_score / 3)  # Normaliza até 3 palavras-chave
        
        logger.info(
            "Document type detected",
            event="document_detection_complete",
            document_type=best_type,
            confidence=round(confidence, 3),
            scores=scores,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
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
        # Inicia medição de tempo
        start_time = time.time()
        
        logger.info(
            "Financial data parsing started",
            event="parsing_start",
            document_type=document_type,
            text_length=len(text)
        )
        
        # Variáveis para métricas
        bank_key = None
        confidence = 0.0
        parser_type = "generic"
        used_fallback = False
        success = False
        dados = None
        
        # Tenta usar parser especializado se disponível
        if SPECIALIZED_PARSERS_AVAILABLE and self.specialized_parsers:
            # Tenta obter detecção do cache
            bank_detection = None
            if self.cache:
                bank_detection = self.cache.get_bank_detection(text)
                if bank_detection and self.metrics:
                    self.metrics.record_cache_hit()
                    logger.debug(
                        "Bank detection cache hit",
                        event="cache_hit",
                        bank=bank_detection[0]
                    )
            
            # Se não está no cache, detecta o banco
            if bank_detection is None:
                if self.metrics:
                    self.metrics.record_cache_miss()
                    
                detection_start = time.time()
                bank_detection = self.bank_detector.detect_bank(text)
                detection_time_ms = int((time.time() - detection_start) * 1000)
                
                logger.info(
                    "Bank detected",
                    event="bank_detection",
                    bank=bank_detection[0] if bank_detection else None,
                    confidence=round(bank_detection[2], 3) if bank_detection else 0,
                    detection_time_ms=detection_time_ms
                )
                
                # ONDA 3 - Sistema 7: ML como assistente (apenas se confiança baixa)
                if bank_detection and self.ml_classifier:
                    _, _, rule_confidence = bank_detection
                    if self.ml_classifier.should_assist(rule_confidence):
                        ml_prediction = self.ml_classifier.predict(text)
                        if ml_prediction:
                            ml_bank, ml_confidence = ml_prediction
                            # Se ML tem maior confiança, usa predição do ML
                            if ml_confidence > rule_confidence:
                                logger.info(
                                    "ML classifier override",
                                    event="ml_override",
                                    ml_bank=ml_bank,
                                    ml_confidence=round(ml_confidence, 3),
                                    rule_bank=bank_detection[0],
                                    rule_confidence=round(rule_confidence, 3)
                                )
                                bank_detection = (ml_bank, f"ML: {ml_bank}", ml_confidence)
                
                # Armazena no cache
                if bank_detection and self.cache:
                    self.cache.set_bank_detection(text, bank_detection)
            
            if bank_detection:
                bank_key, bank_name, confidence = bank_detection
                
                # Verifica se temos parser especializado para este banco
                if bank_key in self.specialized_parsers:
                    parser = self.specialized_parsers[bank_key]
                    parser_name = parser.__class__.__name__
                    
                    logger.info(
                        "Using specialized parser",
                        event="parser_selection",
                        bank=bank_key,
                        parser=parser_name,
                        confidence=round(confidence, 3)
                    )
                    
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
                            parser_type = "specialized"
                            parsing_start = time.time()
                            dados = parser.parse(text)
                            parsing_time_ms = int((time.time() - parsing_start) * 1000)
                            success = True
                            
                            logger.info(
                                "Specialized parser completed",
                                event="specialized_parsing_complete",
                                bank=bank_key,
                                parser=parser_name,
                                parsing_time_ms=parsing_time_ms
                            )
                            
                            # Se CNPJ não foi encontrado, tenta buscar do banco de dados
                            if not dados.cnpj and bank_key:
                                dados.cnpj = self.bank_detector.get_cnpj(bank_key)
                            
                            # Registra métricas
                            if self.metrics:
                                processing_time = time.time() - start_time
                                fields_extracted = self._get_extracted_fields(dados)
                                self.metrics.record_parse_attempt(
                                    bank=bank_key,
                                    parser_type=parser_type,
                                    confidence=confidence,
                                    processing_time=processing_time,
                                    success=success,
                                    fields_extracted=fields_extracted,
                                    used_fallback=False
                                )
                            
                            return dados
                        except Exception as e:
                            # Log: fallback por erro
                            logger.warning(
                                "Specialized parser failed, falling back to generic",
                                event="parser_fallback",
                                bank=bank_key,
                                parser=parser_name,
                                error=str(e)
                            )
                            
                            self._log_parser_selection({
                                "bank": bank_key,
                                "bank_name": bank_name,
                                "parser": "GenericParser",
                                "confidence": round(confidence, 3),
                                "fallback": True,
                                "reason": f"specialized_parser_error: {str(e)}"
                            })
                            used_fallback = True
                else:
                    # Log: banco detectado mas sem parser especializado
                    logger.info(
                        "No specialized parser available, using generic",
                        event="no_specialized_parser",
                        bank=bank_key
                    )
                    
                    self._log_parser_selection({
                        "bank": bank_key,
                        "bank_name": bank_name,
                        "parser": "GenericParser",
                        "confidence": round(confidence, 3),
                        "fallback": True,
                        "reason": "no_specialized_parser_available"
                    })
                    used_fallback = True
            else:
                # Log: banco não detectado
                logger.info(
                    "Bank not detected, using generic parser",
                    event="bank_not_detected"
                )
                
                self._log_parser_selection({
                    "bank": "unknown",
                    "bank_name": "Unknown",
                    "parser": "GenericParser",
                    "confidence": 0.0,
                    "fallback": True,
                    "reason": "bank_not_detected"
                })
                used_fallback = True
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
            used_fallback = True
        
        # Fallback: usa parser genérico
        dados = DadosFinanceiros()
        success = True  # Parser genérico sempre retorna algo
        
        # Tenta detectar banco e adicionar CNPJ conhecido
        if SPECIALIZED_PARSERS_AVAILABLE and self.bank_detector:
            bank_info = self.bank_detector.detect_bank(text)
            if bank_info:
                detected_bank_key, bank_name, confidence = bank_info
                if bank_key is None:
                    bank_key = detected_bank_key
                dados.empresa = bank_name
                dados.cnpj = self.bank_detector.get_cnpj(detected_bank_key)
        
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
        
        # Registra métricas do parser genérico
        if self.metrics:
            processing_time = time.time() - start_time
            fields_extracted = self._get_extracted_fields(dados)
            self.metrics.record_parse_attempt(
                bank=bank_key,
                parser_type=parser_type,
                confidence=confidence,
                processing_time=processing_time,
                success=success,
                fields_extracted=fields_extracted,
                used_fallback=used_fallback
            )
        
        return dados
    
    def _get_extracted_fields(self, dados: DadosFinanceiros) -> List[str]:
        """
        Identifica quais campos foram extraídos com sucesso.
        
        Args:
            dados: DadosFinanceiros extraídos
            
        Returns:
            Lista de nomes de campos preenchidos
        """
        fields = []
        if dados.empresa:
            fields.append("empresa")
        if dados.cnpj:
            fields.append("cnpj")
        if dados.cpf:
            fields.append("cpf")
        if dados.data_emissao:
            fields.append("data_emissao")
        if dados.data_vencimento:
            fields.append("data_vencimento")
        if dados.valor_total:
            fields.append("valor_total")
        if dados.numero_documento:
            fields.append("numero_documento")
        if dados.codigo_barras:
            fields.append("codigo_barras")
        if dados.linha_digitavel:
            fields.append("linha_digitavel")
        if dados.itens:
            fields.append("itens")
        return fields
    
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
    
    # ========== ONDA 3: Inteligência e Comunidade ==========
    
    def submit_feedback(
        self,
        document_text: str,
        detected_bank: Optional[str] = None,
        correct_bank: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
        correct_data: Optional[Dict[str, Any]] = None,
        user_comment: Optional[str] = None
    ) -> int:
        """
        Submete feedback de correção do usuário (Sistema 8).
        
        Args:
            document_text: Texto original do documento
            detected_bank: Banco detectado pelo sistema
            correct_bank: Banco correto segundo usuário
            extracted_data: Dados extraídos pelo sistema
            correct_data: Dados corretos segundo usuário
            user_comment: Comentário adicional
            
        Returns:
            ID do feedback ou -1 se falhar
        """
        if not self.feedback_system:
            return -1
        
        return self.feedback_system.submit_feedback(
            document_text=document_text,
            detected_bank=detected_bank,
            correct_bank=correct_bank,
            extracted_data=extracted_data,
            correct_data=correct_data,
            user_comment=user_comment
        )
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de feedback"""
        if not self.feedback_system:
            return {}
        return self.feedback_system.get_feedback_stats()
    
    def retrain_ml_from_feedback(self) -> bool:
        """
        Retreina modelo ML com feedbacks não processados (Sistema 7).
        
        Returns:
            True se retreinou com sucesso
        """
        if not self.ml_classifier or not self.feedback_system:
            return False
        
        try:
            # Obtém feedbacks não processados
            feedbacks = self.feedback_system.get_unprocessed_feedback(limit=1000)
            
            if not feedbacks:
                logger.info("No unprocessed feedback to retrain")
                return False
            
            # Prepara dados para treinamento
            training_data = []
            for fb in feedbacks:
                if fb.get('correct_bank'):
                    training_data.append({
                        'text': fb['document_text'],
                        'correct_bank': fb['correct_bank']
                    })
            
            # Treina modelo
            self.ml_classifier.train_from_feedback(training_data)
            
            # Marca feedbacks como processados
            feedback_ids = [fb['id'] for fb in feedbacks]
            self.feedback_system.mark_as_processed(feedback_ids)
            
            logger.info(f"ML model retrained with {len(training_data)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retrain ML: {e}")
            return False
    
    def submit_community_template(
        self,
        bank_key: str,
        bank_name: str,
        cnpj: str,
        detection_patterns: List[str],
        extraction_patterns: Dict[str, str],
        author: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submete template comunitário para novo banco (Sistema 9).
        
        Args:
            bank_key: Identificador único (ex: 'santander')
            bank_name: Nome completo do banco
            cnpj: CNPJ do banco
            detection_patterns: Lista de regex para detecção
            extraction_patterns: Dict de regex para extração
            author: Nome/email do autor
            description: Descrição opcional
            
        Returns:
            Dict com resultado da submissão
        """
        if not self.template_system:
            return {
                "success": False,
                "error": "Template system not available"
            }
        
        return self.template_system.submit_template(
            bank_key=bank_key,
            bank_name=bank_name,
            cnpj=cnpj,
            detection_patterns=detection_patterns,
            extraction_patterns=extraction_patterns,
            author=author,
            description=description
        )
    
    def list_community_templates(self) -> Dict[str, Any]:
        """
        Lista templates comunitários disponíveis.
        
        Returns:
            Dict com templates aprovados e pendentes
        """
        if not self.template_system:
            return {"approved": [], "pending": []}
        
        return {
            "approved": self.template_system.list_approved_templates(),
            "pending": self.template_system.list_pending_templates()
        }
    
    def approve_community_template(self, template_hash: str, reviewer: str) -> bool:
        """
        Aprova template comunitário (requer privilégios de admin).
        
        Args:
            template_hash: Hash do template
            reviewer: Nome do revisor
            
        Returns:
            True se aprovado
        """
        if not self.template_system:
            return False
        
        return self.template_system.approve_template(template_hash, reviewer)
    
    def get_ml_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo ML"""
        if not self.ml_classifier:
            return {"enabled": False}
        return self.ml_classifier.get_model_info()
