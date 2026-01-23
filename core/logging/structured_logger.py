"""
Módulo de logging estruturado para observabilidade de alta qualidade.

Este módulo fornece logging JSON estruturado com suporte a:
- Rastreamento de requisições com trace_id
- Sanitização automática de dados sensíveis
- Contexto rico para debugging
- Métricas de performance
- Integração com ELK Stack, Datadog, Loki, etc.

Autor: API OCR Leitura Faturas
Data: 2026-01-23
"""

import logging
import structlog
import sys
import uuid
import re
import time
from typing import Any, Dict, Optional, List
from datetime import datetime
from contextvars import ContextVar

# ContextVar para armazenar trace_id por requisição
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    include_timestamp: bool = True
) -> None:
    """
    Configura o sistema de logging estruturado.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Se True, emite logs em formato JSON estruturado
        include_timestamp: Se True, inclui timestamp ISO8601 em cada log
    """
    # Configura logging padrão do Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Processadores do structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True) if include_timestamp else None,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Remove None entries
    processors = [p for p in processors if p is not None]
    
    # Adiciona processador JSON ou desenvolvimento
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configura structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Obtém um logger estruturado.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        
    Returns:
        Logger estruturado do structlog
    """
    return structlog.get_logger(name)


def add_trace_id_to_context(trace_id: Optional[str] = None) -> str:
    """
    Adiciona ou gera um trace_id para contexto da requisição.
    
    Args:
        trace_id: ID de rastreamento (se None, gera automaticamente)
        
    Returns:
        O trace_id usado
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    trace_id_var.set(trace_id)
    structlog.contextvars.bind_contextvars(trace_id=trace_id)
    return trace_id


def get_current_trace_id() -> Optional[str]:
    """
    Obtém o trace_id atual do contexto.
    
    Returns:
        trace_id ou None se não estiver definido
    """
    return trace_id_var.get()


def sanitize_sensitive_data(data: Any, fields_to_mask: Optional[List[str]] = None) -> Any:
    """
    Sanitiza dados sensíveis para logging seguro.
    
    Remove ou mascara informações sensíveis como:
    - CPF/CNPJ (parcialmente mascarado)
    - Números de conta bancária
    - Valores monetários muito altos
    - Chaves de API/tokens
    
    Args:
        data: Dados a serem sanitizados (dict, str, list, etc)
        fields_to_mask: Lista adicional de campos a mascarar
        
    Returns:
        Dados sanitizados
    """
    if fields_to_mask is None:
        fields_to_mask = []
    
    # Campos padrão para mascarar
    sensitive_fields = {
        'cpf', 'cnpj', 'conta', 'agencia', 'numero_conta',
        'password', 'senha', 'token', 'api_key', 'secret',
        'authorization', 'auth', 'credit_card', 'cartao'
    }
    sensitive_fields.update(fields_to_mask)
    
    def _mask_string(value: str) -> str:
        """Mascara parcialmente uma string."""
        if len(value) <= 4:
            return "***"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    def _sanitize_recursive(obj: Any) -> Any:
        """Sanitiza recursivamente estruturas de dados."""
        if isinstance(obj, dict):
            sanitized = {}
            for key, value in obj.items():
                key_lower = key.lower()
                
                # Verifica se o campo é sensível
                if any(sensitive_field in key_lower for sensitive_field in sensitive_fields):
                    # Mascara o valor
                    if isinstance(value, str):
                        sanitized[key] = _mask_string(value)
                    else:
                        sanitized[key] = "***MASKED***"
                else:
                    # Sanitiza recursivamente
                    sanitized[key] = _sanitize_recursive(value)
            return sanitized
        
        elif isinstance(obj, list):
            return [_sanitize_recursive(item) for item in obj]
        
        elif isinstance(obj, str):
            # Mascara padrões de CPF/CNPJ no texto
            obj = re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', 'CPF:***.**.***.XX', obj)
            obj = re.sub(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', 'CNPJ:**.***.***/****.XX', obj)
            return obj
        
        return obj
    
    return _sanitize_recursive(data)


def log_request_start(
    logger: structlog.BoundLogger,
    endpoint: str,
    method: str = "POST",
    file_name: Optional[str] = None,
    file_size_bytes: Optional[int] = None,
    user_id: Optional[str] = None,
    **extra_context
) -> Dict[str, Any]:
    """
    Loga o início de uma requisição HTTP.
    
    Args:
        logger: Logger estruturado
        endpoint: Endpoint da API
        method: Método HTTP
        file_name: Nome do arquivo (se aplicável)
        file_size_bytes: Tamanho do arquivo em bytes
        user_id: ID do usuário (se autenticado)
        **extra_context: Contexto adicional
        
    Returns:
        Dicionário com dados da requisição para referência
    """
    trace_id = get_current_trace_id()
    
    log_data = {
        "event": "request_start",
        "endpoint": endpoint,
        "method": method,
        "trace_id": trace_id,
    }
    
    if file_name:
        log_data["file_name"] = file_name
    if file_size_bytes is not None:
        log_data["file_size_mb"] = round(file_size_bytes / (1024 * 1024), 2)
    if user_id:
        log_data["user_id"] = user_id
    
    log_data.update(extra_context)
    
    logger.info("Request received", **log_data)
    
    return {
        "trace_id": trace_id,
        "start_time": time.time()
    }


def log_request_end(
    logger: structlog.BoundLogger,
    endpoint: str,
    status_code: int,
    start_time: float,
    success: bool = True,
    document_type: Optional[str] = None,
    **extra_context
) -> None:
    """
    Loga o fim de uma requisição HTTP.
    
    Args:
        logger: Logger estruturado
        endpoint: Endpoint da API
        status_code: Código de status HTTP
        start_time: Timestamp do início da requisição
        success: Se a requisição foi bem-sucedida
        document_type: Tipo de documento detectado
        **extra_context: Contexto adicional
    """
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    log_data = {
        "event": "request_end",
        "endpoint": endpoint,
        "status_code": status_code,
        "success": success,
        "processing_time_ms": processing_time_ms,
    }
    
    if document_type:
        log_data["document_type"] = document_type
    
    log_data.update(extra_context)
    
    if success:
        logger.info("Request completed successfully", **log_data)
    else:
        logger.warning("Request completed with errors", **log_data)


def log_ocr_processing(
    logger: structlog.BoundLogger,
    pdf_type: str,
    total_pages: int,
    method: str,
    confidence: Optional[float] = None,
    **extra_context
) -> None:
    """
    Loga o processamento OCR.
    
    Args:
        logger: Logger estruturado
        pdf_type: Tipo de PDF (native, scanned, hybrid)
        total_pages: Número total de páginas
        method: Método de extração (pdfplumber, paddleocr)
        confidence: Confiança da detecção (0-1)
        **extra_context: Contexto adicional
    """
    log_data = {
        "event": "ocr_processing",
        "pdf_type": pdf_type,
        "total_pages": total_pages,
        "extraction_method": method,
    }
    
    if confidence is not None:
        log_data["detection_confidence"] = round(confidence, 3)
    
    log_data.update(extra_context)
    
    logger.info("OCR processing started", **log_data)


def log_ocr_result(
    logger: structlog.BoundLogger,
    success: bool,
    text_length: int,
    processing_time_ms: int,
    pages_processed: int,
    avg_confidence: Optional[float] = None,
    error_message: Optional[str] = None,
    **extra_context
) -> None:
    """
    Loga o resultado do processamento OCR.
    
    Args:
        logger: Logger estruturado
        success: Se o OCR foi bem-sucedido
        text_length: Comprimento do texto extraído
        processing_time_ms: Tempo de processamento em ms
        pages_processed: Número de páginas processadas
        avg_confidence: Confiança média das detecções
        error_message: Mensagem de erro (se houver)
        **extra_context: Contexto adicional
    """
    log_data = {
        "event": "ocr_result",
        "success": success,
        "text_length": text_length,
        "processing_time_ms": processing_time_ms,
        "pages_processed": pages_processed,
    }
    
    if avg_confidence is not None:
        log_data["avg_confidence"] = round(avg_confidence, 3)
    
    if error_message:
        log_data["error_message"] = error_message
    
    log_data.update(extra_context)
    
    if success:
        logger.info("OCR completed successfully", **log_data)
    else:
        logger.error("OCR failed", **log_data)


def log_extraction_result(
    logger: structlog.BoundLogger,
    document_type: str,
    fields_extracted: Dict[str, Any],
    confidence: float,
    bank_detected: Optional[str] = None,
    parser_used: Optional[str] = None,
    **extra_context
) -> None:
    """
    Loga o resultado da extração de dados estruturados.
    
    Args:
        logger: Logger estruturado
        document_type: Tipo de documento detectado
        fields_extracted: Campos extraídos (serão sanitizados)
        confidence: Confiança da extração (0-1)
        bank_detected: Banco detectado (se aplicável)
        parser_used: Parser utilizado
        **extra_context: Contexto adicional
    """
    # Sanitiza dados sensíveis
    sanitized_fields = sanitize_sensitive_data(fields_extracted)
    
    log_data = {
        "event": "extraction_result",
        "document_type": document_type,
        "confidence": round(confidence, 3),
        "fields_count": len(fields_extracted),
        "extracted_fields": sanitized_fields,
    }
    
    if bank_detected:
        log_data["bank_detected"] = bank_detected
    if parser_used:
        log_data["parser_used"] = parser_used
    
    log_data.update(extra_context)
    
    logger.info("Data extraction completed", **log_data)


def log_error(
    logger: structlog.BoundLogger,
    error_type: str,
    error_message: str,
    endpoint: Optional[str] = None,
    file_name: Optional[str] = None,
    stacktrace: Optional[str] = None,
    **extra_context
) -> None:
    """
    Loga um erro ocorrido durante o processamento.
    
    Args:
        logger: Logger estruturado
        error_type: Tipo/categoria do erro
        error_message: Mensagem de erro
        endpoint: Endpoint onde ocorreu o erro
        file_name: Nome do arquivo sendo processado
        stacktrace: Stack trace (será sanitizado)
        **extra_context: Contexto adicional
    """
    log_data = {
        "event": "error",
        "error_type": error_type,
        "error_message": sanitize_sensitive_data(error_message),
    }
    
    if endpoint:
        log_data["endpoint"] = endpoint
    if file_name:
        log_data["file_name"] = file_name
    if stacktrace:
        log_data["stacktrace"] = sanitize_sensitive_data(stacktrace)
    
    log_data.update(extra_context)
    
    logger.error("Error occurred", **log_data)


def log_validation_error(
    logger: structlog.BoundLogger,
    validation_type: str,
    reason: str,
    file_name: Optional[str] = None,
    **extra_context
) -> None:
    """
    Loga um erro de validação.
    
    Args:
        logger: Logger estruturado
        validation_type: Tipo de validação (size, format, content)
        reason: Motivo da falha
        file_name: Nome do arquivo
        **extra_context: Contexto adicional
    """
    log_data = {
        "event": "validation_error",
        "validation_type": validation_type,
        "reason": reason,
    }
    
    if file_name:
        log_data["file_name"] = file_name
    
    log_data.update(extra_context)
    
    logger.warning("Validation failed", **log_data)


def log_performance_metric(
    logger: structlog.BoundLogger,
    operation: str,
    duration_ms: int,
    success: bool = True,
    **extra_context
) -> None:
    """
    Loga uma métrica de performance.
    
    Args:
        logger: Logger estruturado
        operation: Nome da operação
        duration_ms: Duração em milissegundos
        success: Se a operação foi bem-sucedida
        **extra_context: Contexto adicional
    """
    log_data = {
        "event": "performance_metric",
        "operation": operation,
        "duration_ms": duration_ms,
        "success": success,
    }
    
    log_data.update(extra_context)
    
    logger.debug("Performance metric recorded", **log_data)
