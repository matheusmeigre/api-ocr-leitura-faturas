"""Logging module for structured, observability-grade logging"""

from core.logging.structured_logger import (
    get_logger,
    log_request_start,
    log_request_end,
    log_ocr_processing,
    log_ocr_result,
    log_extraction_result,
    log_error,
    configure_logging,
    add_trace_id_to_context,
    get_current_trace_id,
    sanitize_sensitive_data
)

__all__ = [
    'get_logger',
    'log_request_start',
    'log_request_end',
    'log_ocr_processing',
    'log_ocr_result',
    'log_extraction_result',
    'log_error',
    'configure_logging',
    'add_trace_id_to_context',
    'get_current_trace_id',
    'sanitize_sensitive_data'
]
