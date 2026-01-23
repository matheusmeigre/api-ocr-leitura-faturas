"""
Middleware FastAPI para logging estruturado e rastreamento de requisições.

Este middleware intercepta todas as requisições HTTP e adiciona:
- trace_id único para rastreamento end-to-end
- Logs automáticos de início e fim de requisição
- Medição de tempo de processamento
- Contexto rico para debugging
- Tratamento automático de exceções

Autor: API OCR Leitura Faturas
Data: 2026-01-23
"""

import time
import traceback
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.logging.structured_logger import (
    get_logger,
    add_trace_id_to_context,
    log_error,
)

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging estruturado de requisições HTTP.
    
    Adiciona trace_id a cada requisição e loga:
    - Início da requisição (método, path, headers relevantes)
    - Fim da requisição (status, tempo de processamento)
    - Erros e exceções (com stacktrace sanitizado)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] = None
    ):
        """
        Inicializa o middleware.
        
        Args:
            app: Aplicação ASGI
            exclude_paths: Paths a serem excluídos do logging (ex: /health)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Processa a requisição e adiciona logging estruturado.
        
        Args:
            request: Requisição HTTP
            call_next: Próximo handler na cadeia
            
        Returns:
            Response HTTP
        """
        # Pula paths excluídos (health checks, etc)
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Gera trace_id único para esta requisição
        trace_id = request.headers.get("X-Trace-Id")
        trace_id = add_trace_id_to_context(trace_id)
        
        # Marca início do processamento
        start_time = time.time()
        
        # Extrai informações da requisição
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log de início da requisição
        logger.info(
            event="request_started",
            message="Request started",
            method=method,
            path=path,
            client_host=client_host,
            user_agent=user_agent,
            trace_id=trace_id
        )
        
        # Variáveis para capturar informações da resposta
        status_code = 500
        error_occurred = False
        error_detail = None
        
        try:
            # Processa a requisição
            response = await call_next(request)
            status_code = response.status_code
            
            # Adiciona trace_id ao header da resposta
            response.headers["X-Trace-Id"] = trace_id
            
        except Exception as e:
            # Captura exceções não tratadas
            error_occurred = True
            error_detail = str(e)
            error_type = type(e).__name__
            
            # Log detalhado do erro
            log_error(
                logger=logger,
                error_type=error_type,
                error_message=error_detail,
                endpoint=path,
                stacktrace=traceback.format_exc()
            )
            
            # Re-lança a exceção para o handler do FastAPI
            raise
        
        finally:
            # Calcula tempo de processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log de fim da requisição
            log_data = {
                "event": "request_completed",
                "method": method,
                "path": path,
                "status_code": status_code,
                "processing_time_ms": processing_time_ms,
                "trace_id": trace_id
            }
            
            if error_occurred:
                log_data["error"] = True
                log_data["error_detail"] = error_detail
                logger.error(**log_data)
            else:
                logger.info(**log_data)
        
        return response


class FileUploadLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware específico para logging de uploads de arquivos.
    
    Adiciona informações sobre:
    - Nome e tamanho do arquivo
    - Content-Type
    - Validações de upload
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Processa requisições de upload e adiciona logging específico.
        
        Args:
            request: Requisição HTTP
            call_next: Próximo handler na cadeia
            
        Returns:
            Response HTTP
        """
        # Verifica se é uma requisição de upload
        content_type = request.headers.get("content-type", "")
        
        if "multipart/form-data" in content_type:
            # Log específico de upload
            logger.debug(
                event="file_upload_started",
                message="File upload detected",
                path=request.url.path,
                content_type=content_type
            )
        
        # Continua o processamento normal
        response = await call_next(request)
        return response


def setup_logging_middleware(app):
    """
    Configura todos os middlewares de logging na aplicação FastAPI.
    
    Args:
        app: Instância do FastAPI
    """
    # Adiciona middleware de logging de requisições
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=["/health", "/health/ready", "/metrics", "/docs", "/redoc", "/openapi.json"]
    )
    
    # Adiciona middleware de logging de uploads
    app.add_middleware(FileUploadLoggingMiddleware)
    
    logger.info(
        event="middleware_setup",
        message="Logging middleware configured",
        middlewares=["RequestLoggingMiddleware", "FileUploadLoggingMiddleware"]
    )
