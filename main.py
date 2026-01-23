from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from typing import Optional

from config import settings
from models import ExtractionResponse, ErrorResponse, DadosFinanceiros
from utils.pdf_detector import detect_pdf_type, is_valid_pdf, get_pdf_metadata
from extractors.text_extractor import TextExtractor
from parsers.financial_parser import FinancialParser

# Importa sistema de logging estruturado
from core.logging.structured_logger import (
    configure_logging,
    get_logger,
    add_trace_id_to_context,
    log_request_start,
    log_request_end,
    log_ocr_processing,
    log_ocr_result,
    log_extraction_result,
    log_error,
    log_validation_error,
)
from core.logging.middleware import setup_logging_middleware

# Configura logging estruturado
configure_logging(
    log_level=settings.log_level,
    json_logs=settings.log_format_json,
    include_timestamp=settings.log_include_timestamp
)

# Logger estruturado para este módulo
logger = get_logger(__name__)

# Inicializa FastAPI
app = FastAPI(
    title="API de OCR e Extração de Dados Financeiros",
    description="API REST para extração de dados financeiros de PDFs (nativos e escaneados)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração CORS para permitir acesso do frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configura middlewares de logging estruturado
setup_logging_middleware(app)

# Inicializa componentes (lazy loading)
text_extractor = TextExtractor()
financial_parser = FinancialParser()

# Flag para indicar se o OCR está pronto
ocr_ready = False


@app.on_event("startup")
async def startup_event():
    """
    Evento executado na inicialização da API.
    Faz warm-up do PaddleOCR para evitar cold start na primeira requisição.
    """
    global ocr_ready
    
    logger.info(
        "API startup initiated",
        event="startup",
        version="1.0.0",
        environment="production" if not settings.api_debug else "development"
    )
    
    try:
        logger.info(
            "Warming up PaddleOCR",
            event="ocr_warmup_start"
        )
        
        # Força inicialização do OCR criando uma imagem pequena de teste
        import numpy as np
        dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        _ = text_extractor.ocr.ocr(dummy_image, cls=False)
        
        ocr_ready = True
        
        logger.info(
            "PaddleOCR warmup completed",
            event="ocr_warmup_complete",
            status="ready"
        )
        
    except Exception as e:
        logger.error(
            "PaddleOCR warmup failed",
            event="ocr_warmup_error",
            error=str(e),
            status="degraded"
        )
        ocr_ready = False


@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "API de OCR e Extração de Dados Financeiros",
        "version": "1.0.0",
        "endpoints": {
            "extract": "/extract (POST)",
            "extract_for_llm": "/extract-for-llm (POST)",
            "health": "/health (GET)",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """Health check da API"""
    return {
        "status": "healthy",
        "service": "api-ocr-leitura-faturas",
        "ocr_ready": ocr_ready
    }


@app.get("/health/ready")
async def health_ready():
    """
    Health check detalhado indicando se a API está pronta para processar OCR.
    Útil para load balancers e monitoring.
    """
    if ocr_ready:
        return {
            "status": "ready",
            "message": "API pronta para processar requisições OCR",
            "ocr_initialized": True
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "message": "PaddleOCR ainda está inicializando. Aguarde alguns segundos.",
                "ocr_initialized": False
            }
        )


@app.post(
    "/extract",
    response_model=ExtractionResponse,
    responses={
        200: {"model": ExtractionResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Extrai dados financeiros de PDF",
    description="""
    Recebe um arquivo PDF (nativo ou escaneado) e extrai dados financeiros estruturados.
    
    **Processo:**
    1. Valida o arquivo PDF
    2. Detecta se é PDF nativo ou escaneado
    3. Extrai texto usando pdfplumber (nativo) ou PaddleOCR (escaneado)
    4. Normaliza o texto
    5. Identifica o tipo de documento
    6. Extrai campos financeiros estruturados
    
    **Tipos de documentos suportados:**
    - Boleto
    - Fatura de cartão de crédito
    - Nota fiscal
    - Extrato bancário
    """
)
async def extract_financial_data(
    file: UploadFile = File(..., description="Arquivo PDF para extração")
):
    """
    Endpoint principal para extração de dados financeiros de PDFs.
    
    Args:
        file: Arquivo PDF enviado via multipart/form-data
        
    Returns:
        ExtractionResponse com dados financeiros estruturados
    """
    # Gera trace_id para rastreamento
    trace_id = add_trace_id_to_context()
    start_time = time.time()
    
    try:
        # Validações básicas
        if not file.filename:
            log_validation_error(
                logger=logger,
                validation_type="filename",
                reason="Nome do arquivo não fornecido"
            )
            raise HTTPException(
                status_code=400,
                detail="Nome do arquivo não fornecido"
            )
        
        # Verifica extensão
        if not file.filename.lower().endswith('.pdf'):
            log_validation_error(
                logger=logger,
                validation_type="format",
                reason="Apenas arquivos PDF são aceitos",
                file_name=file.filename
            )
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Formato de arquivo inválido",
                    detail="Apenas arquivos PDF são aceitos"
                ).model_dump()
            )
        
        # Lê o conteúdo do arquivo
        file_bytes = await file.read()
        file_size_bytes = len(file_bytes)
        
        # Log do início do processamento
        log_request_start(
            logger=logger,
            endpoint="/extract",
            method="POST",
            file_name=file.filename,
            file_size_bytes=file_size_bytes
        )
        
        # Verifica tamanho
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            log_validation_error(
                logger=logger,
                validation_type="size",
                reason=f"Arquivo excede o tamanho máximo de {settings.max_file_size_mb}MB",
                file_name=file.filename,
                file_size_mb=round(file_size_mb, 2)
            )
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Arquivo muito grande",
                    detail=f"Tamanho máximo permitido: {settings.max_file_size_mb}MB"
                ).model_dump()
            )
        
        # Valida se é um PDF válido
        if not is_valid_pdf(file_bytes):
            log_validation_error(
                logger=logger,
                validation_type="content",
                reason="PDF inválido ou corrompido",
                file_name=file.filename
            )
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="PDF inválido",
                    detail="O arquivo não é um PDF válido ou está corrompido"
                ).model_dump()
            )
        
        # Detecta tipo de PDF
        detection_start = time.time()
        pdf_type, pdf_confidence = detect_pdf_type(file_bytes)
        detection_time_ms = int((time.time() - detection_start) * 1000)
        
        logger.info(
            "PDF type detected",
            event="pdf_detection",
            pdf_type=pdf_type,
            confidence=round(pdf_confidence, 3),
            detection_time_ms=detection_time_ms,
            file_name=file.filename
        )
        
        # Extrai metadados
        pdf_metadata = get_pdf_metadata(file_bytes)
        
        # Log do início da extração OCR
        log_ocr_processing(
            logger=logger,
            pdf_type=pdf_type,
            total_pages=pdf_metadata.get("total_pages", 0),
            method="pdfplumber" if pdf_type == "native" else "paddleocr",
            confidence=pdf_confidence,
            file_name=file.filename
        )
        
        # Extrai texto
        ocr_start = time.time()
        try:
            extracted_text, extraction_metadata = text_extractor.extract_text(
                file_bytes,
                pdf_type=pdf_type
            )
            ocr_time_ms = int((time.time() - ocr_start) * 1000)
            
            # Log do resultado do OCR
            log_ocr_result(
                logger=logger,
                success=True,
                text_length=len(extracted_text),
                processing_time_ms=ocr_time_ms,
                pages_processed=extraction_metadata.get("total_pages", 0),
                avg_confidence=extraction_metadata.get("average_confidence"),
                file_name=file.filename
            )
            
        except Exception as e:
            ocr_time_ms = int((time.time() - ocr_start) * 1000)
            
            log_ocr_result(
                logger=logger,
                success=False,
                text_length=0,
                processing_time_ms=ocr_time_ms,
                pages_processed=0,
                error_message=str(e),
                file_name=file.filename
            )
            
            log_error(
                logger=logger,
                error_type="OCRExtractionError",
                error_message=str(e),
                endpoint="/extract",
                file_name=file.filename
            )
            
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="Erro ao extrair texto do PDF",
                    detail=str(e)
                ).model_dump()
            )
        
        # Verifica se conseguiu extrair texto
        if not extracted_text or len(extracted_text.strip()) < 10:
            log_validation_error(
                logger=logger,
                validation_type="content",
                reason="Texto extraído insuficiente",
                file_name=file.filename,
                text_length=len(extracted_text)
            )
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Falha na extração",
                    detail="Não foi possível extrair texto suficiente do documento"
                ).model_dump()
            )
        
        # Detecta tipo de documento
        parsing_start = time.time()
        document_type, doc_confidence = financial_parser.detect_document_type(extracted_text)
        
        logger.info(
            "Document type detected",
            event="document_detection",
            document_type=document_type,
            confidence=round(doc_confidence, 3),
            file_name=file.filename
        )
        
        # Parse dos dados financeiros
        try:
            financial_data = financial_parser.parse_financial_data(
                extracted_text,
                document_type=document_type
            )
            parsing_time_ms = int((time.time() - parsing_start) * 1000)
            
            # Log do resultado da extração
            log_extraction_result(
                logger=logger,
                document_type=document_type,
                fields_extracted=financial_data.model_dump(),
                confidence=doc_confidence,
                bank_detected=getattr(financial_data, 'banco', None),
                parser_used="specialized" if hasattr(financial_parser, 'last_parser_used') else "generic",
                file_name=file.filename,
                parsing_time_ms=parsing_time_ms
            )
            
        except Exception as e:
            log_error(
                logger=logger,
                error_type="ParsingError",
                error_message=str(e),
                endpoint="/extract",
                file_name=file.filename
            )
            # Retorna dados vazios em caso de erro no parse
            financial_data = DadosFinanceiros()
        
        # Calcula confiança geral baseada em múltiplos fatores
        # 1. Confiança da detecção de PDF
        # 2. Confiança da detecção de tipo de documento
        # 3. Confiança da extração de campos
        extraction_confidence = financial_parser.calculate_extraction_confidence(
            financial_data,
            document_type=document_type
        )
        overall_confidence = (
            pdf_confidence * 0.2 +           # 20% - tipo de PDF
            doc_confidence * 0.3 +           # 30% - tipo de documento
            extraction_confidence * 0.5      # 50% - campos extraídos
        )
        
        # Prepara texto para integração futura com LLM
        llm_prepared_data = text_extractor.prepare_text_for_llm(
            extracted_text,
            metadata=extraction_metadata
        )
        
        # Monta metadados
        metadata = {
            "pdf_type": pdf_type,
            "pdf_detection_confidence": round(pdf_confidence, 3),
            "document_detection_confidence": round(doc_confidence, 3),
            "extraction_confidence": round(extraction_confidence, 3),
            "llm_ready": True,  # Indica que o texto está pronto para LLM
            **pdf_metadata,
            **extraction_metadata
        }
        
        # Monta resposta
        response = ExtractionResponse(
            success=True,
            document_type=document_type,
            confidence=round(overall_confidence, 3),
            raw_text=extracted_text,
            data=financial_data,
            metadata=metadata
        )
        
        # Log de conclusão da requisição
        log_request_end(
            logger=logger,
            endpoint="/extract",
            status_code=200,
            start_time=start_time,
            success=True,
            document_type=document_type,
            file_name=file.filename,
            overall_confidence=round(overall_confidence, 3)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            logger=logger,
            error_type="UnexpectedError",
            error_message=str(e),
            endpoint="/extract",
            file_name=file.filename if file else None
        )
        
        log_request_end(
            logger=logger,
            endpoint="/extract",
            status_code=500,
            start_time=start_time,
            success=False
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Erro interno do servidor",
                detail=str(e)
            ).model_dump()
        )


@app.post(
    "/extract-for-llm",
    summary="Extrai e prepara texto para LLM",
    description="""
    Endpoint otimizado para integração com LLMs (GPT, Groq, Claude, etc).
    
    Retorna o texto estruturado e um prompt sugerido para uso com modelos de linguagem,
    além de todos os dados extraídos pela API tradicional.
    """
)
async def extract_for_llm(
    file: UploadFile = File(..., description="Arquivo PDF para extração")
):
    """
    Extrai dados e prepara texto otimizado para consumo por LLMs.
    
    Este endpoint é útil quando você quer usar um LLM para extrair
    informações adicionais ou fazer análises mais sofisticadas do documento.
    """
    trace_id = add_trace_id_to_context()
    start_time = time.time()
    
    try:
        # Validações básicas
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            log_validation_error(
                logger=logger,
                validation_type="format",
                reason="Apenas arquivos PDF são aceitos",
                file_name=file.filename if file.filename else "unknown"
            )
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
        
        file_bytes = await file.read()
        file_size_bytes = len(file_bytes)
        
        log_request_start(
            logger=logger,
            endpoint="/extract-for-llm",
            method="POST",
            file_name=file.filename,
            file_size_bytes=file_size_bytes
        )
        
        # Valida tamanho
        if file_size_bytes / (1024 * 1024) > settings.max_file_size_mb:
            log_validation_error(
                logger=logger,
                validation_type="size",
                reason=f"Arquivo excede o tamanho máximo de {settings.max_file_size_mb}MB",
                file_name=file.filename
            )
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Máximo: {settings.max_file_size_mb}MB"
            )
        
        # Valida PDF
        if not is_valid_pdf(file_bytes):
            log_validation_error(
                logger=logger,
                validation_type="content",
                reason="PDF inválido ou corrompido",
                file_name=file.filename
            )
            raise HTTPException(status_code=400, detail="PDF inválido ou corrompido")
        
        # Detecta tipo e extrai texto
        pdf_type, pdf_confidence = detect_pdf_type(file_bytes)
        
        logger.info(
            "LLM extraction started",
            event="llm_extraction",
            pdf_type=pdf_type,
            file_name=file.filename
        )
        
        extracted_text, extraction_metadata = text_extractor.extract_text(file_bytes, pdf_type)
        
        # Prepara para LLM
        llm_data = text_extractor.prepare_text_for_llm(extracted_text, extraction_metadata)
        
        # Também faz a extração tradicional
        document_type, doc_confidence = financial_parser.detect_document_type(extracted_text)
        financial_data = financial_parser.parse_financial_data(extracted_text, document_type)
        extraction_confidence = financial_parser.calculate_extraction_confidence(
            financial_data, document_type
        )
        
        logger.info(
            "LLM extraction completed",
            event="llm_extraction_complete",
            document_type=document_type,
            text_length=len(extracted_text),
            file_name=file.filename
        )
        
        log_request_end(
            logger=logger,
            endpoint="/extract-for-llm",
            status_code=200,
            start_time=start_time,
            success=True,
            document_type=document_type,
            file_name=file.filename
        )
        
        return {
            "success": True,
            "llm_prompt_data": llm_data,
            "traditional_extraction": {
                "document_type": document_type,
                "confidence": round(extraction_confidence, 3),
                "data": financial_data.model_dump()
            },
            "usage_example": {
                "description": "Use o 'suggested_prompt' com seu LLM favorito",
                "groq_example": "client.chat.completions.create(model='mixtral-8x7b-32768', messages=[{'role': 'system', 'content': llm_prompt_data['system_instruction']}, {'role': 'user', 'content': llm_prompt_data['suggested_prompt']}])",
                "openai_example": "client.chat.completions.create(model='gpt-4', messages=[{'role': 'system', 'content': llm_prompt_data['system_instruction']}, {'role': 'user', 'content': llm_prompt_data['suggested_prompt']}])"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            logger=logger,
            error_type="LLMExtractionError",
            error_message=str(e),
            endpoint="/extract-for-llm",
            file_name=file.filename if file else None
        )
        
        log_request_end(
            logger=logger,
            endpoint="/extract-for-llm",
            status_code=500,
            start_time=start_time,
            success=False
        )
        
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Iniciando servidor na porta {settings.api_port}")
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )
