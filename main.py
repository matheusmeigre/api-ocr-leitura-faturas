from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Optional

from config import settings
from models import ExtractionResponse, ErrorResponse, DadosFinanceiros
from utils.pdf_detector import detect_pdf_type, is_valid_pdf, get_pdf_metadata
from extractors.text_extractor import TextExtractor
from parsers.financial_parser import FinancialParser

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Inicializa componentes (lazy loading)
text_extractor = TextExtractor()
financial_parser = FinancialParser()


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
        "service": "api-ocr-leitura-faturas"
    }


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
    try:
        # Validações básicas
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Nome do arquivo não fornecido"
            )
        
        # Verifica extensão
        if not file.filename.lower().endswith('.pdf'):
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Formato de arquivo inválido",
                    detail="Apenas arquivos PDF são aceitos"
                ).model_dump()
            )
        
        # Lê o conteúdo do arquivo
        logger.info(f"Processando arquivo: {file.filename}")
        file_bytes = await file.read()
        
        # Verifica tamanho
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Arquivo muito grande",
                    detail=f"Tamanho máximo permitido: {settings.max_file_size_mb}MB"
                ).model_dump()
            )
        
        # Valida se é um PDF válido
        if not is_valid_pdf(file_bytes):
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="PDF inválido",
                    detail="O arquivo não é um PDF válido ou está corrompido"
                ).model_dump()
            )
        
        logger.info("Detectando tipo de PDF...")
        # Detecta tipo de PDF
        pdf_type, pdf_confidence = detect_pdf_type(file_bytes)
        logger.info(f"Tipo detectado: {pdf_type} (confiança: {pdf_confidence:.2f})")
        
        # Extrai metadados
        pdf_metadata = get_pdf_metadata(file_bytes)
        
        logger.info(f"Extraindo texto usando método: {pdf_type}")
        # Extrai texto
        try:
            extracted_text, extraction_metadata = text_extractor.extract_text(
                file_bytes,
                pdf_type=pdf_type
            )
        except Exception as e:
            logger.error(f"Erro na extração de texto: {str(e)}")
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="Erro ao extrair texto do PDF",
                    detail=str(e)
                ).model_dump()
            )
        
        # Verifica se conseguiu extrair texto
        if not extracted_text or len(extracted_text.strip()) < 10:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Falha na extração",
                    detail="Não foi possível extrair texto suficiente do documento"
                ).model_dump()
            )
        
        logger.info("Identificando tipo de documento...")
        # Detecta tipo de documento
        document_type, doc_confidence = financial_parser.detect_document_type(extracted_text)
        logger.info(f"Tipo de documento: {document_type} (confiança: {doc_confidence:.2f})")
        
        logger.info("Extraindo dados financeiros...")
        # Parse dos dados financeiros
        try:
            financial_data = financial_parser.parse_financial_data(
                extracted_text,
                document_type=document_type
            )
        except Exception as e:
            logger.error(f"Erro ao parsear dados financeiros: {str(e)}")
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
        
        logger.info(f"Extração concluída com sucesso: {file.filename}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
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
    try:
        # Reutiliza a lógica do endpoint principal
        # Validações básicas
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
        
        file_bytes = await file.read()
        
        # Valida tamanho
        if len(file_bytes) / (1024 * 1024) > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Máximo: {settings.max_file_size_mb}MB"
            )
        
        # Valida PDF
        if not is_valid_pdf(file_bytes):
            raise HTTPException(status_code=400, detail="PDF inválido ou corrompido")
        
        # Detecta tipo e extrai texto
        pdf_type, _ = detect_pdf_type(file_bytes)
        extracted_text, extraction_metadata = text_extractor.extract_text(file_bytes, pdf_type)
        
        # Prepara para LLM
        llm_data = text_extractor.prepare_text_for_llm(extracted_text, extraction_metadata)
        
        # Também faz a extração tradicional
        document_type, doc_confidence = financial_parser.detect_document_type(extracted_text)
        financial_data = financial_parser.parse_financial_data(extracted_text, document_type)
        extraction_confidence = financial_parser.calculate_extraction_confidence(
            financial_data, document_type
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
        logger.error(f"Erro no endpoint LLM: {str(e)}", exc_info=True)
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
