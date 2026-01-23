import pdfplumber
import io
import re
import time
from typing import Tuple, Optional
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
import numpy as np
from PIL import Image
from config import settings

# Importa logger estruturado
from core.logging.structured_logger import get_logger, log_performance_metric

logger = get_logger(__name__)


class TextExtractor:
    """Classe para extração de texto de PDFs nativos e escaneados"""
    
    def __init__(self):
        """Inicializa os extratores"""
        self._ocr = None
    
    @property
    def ocr(self):
        """Lazy loading do PaddleOCR"""
        if self._ocr is None:
            self._ocr = PaddleOCR(
                lang=settings.paddle_ocr_lang,
                use_gpu=settings.paddle_ocr_use_gpu,
                show_log=False
            )
        return self._ocr
    
    def extract_from_native_pdf(self, pdf_bytes: bytes) -> Tuple[str, dict]:
        """
        Extrai texto de PDF nativo usando pdfplumber.
        
        Args:
            pdf_bytes: Bytes do arquivo PDF
            
        Returns:
            Tuple (texto_extraido, metadados)
        """
        start_time = time.time()
        
        try:
            logger.debug(
                "Starting native PDF extraction",
                event="native_extraction_start",
                method="pdfplumber"
            )
            
            pdf_file = io.BytesIO(pdf_bytes)
            text_parts = []
            tables_found = 0
            
            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                
                logger.debug(
                    "PDF opened successfully",
                    event="pdf_opened",
                    total_pages=total_pages
                )
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_start = time.time()
                    
                    # Extrai texto
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_parts.append(f"--- Página {page_num} ---\n{page_text}")
                    
                    # Tenta extrair tabelas se existirem
                    tables = page.extract_tables()
                    if tables:
                        tables_found += len(tables)
                        for table_idx, table in enumerate(tables, 1):
                            text_parts.append(f"\n[Tabela {table_idx} da página {page_num}]")
                            for row in table:
                                if row:
                                    text_parts.append(" | ".join([str(cell) if cell else "" for cell in row]))
                    
                    page_time_ms = int((time.time() - page_start) * 1000)
                    
                    logger.debug(
                        "Page processed",
                        event="page_processed",
                        page_number=page_num,
                        processing_time_ms=page_time_ms,
                        text_length=len(page_text) if page_text else 0,
                        tables_count=len(tables) if tables else 0
                    )
                
                full_text = "\n".join(text_parts)
                
                metadata = {
                    "total_pages": total_pages,
                    "extraction_method": "pdfplumber",
                    "has_tables": tables_found > 0,
                    "tables_count": tables_found
                }
                
                extraction_time_ms = int((time.time() - start_time) * 1000)
                
                logger.info(
                    "Native PDF extraction completed",
                    event="native_extraction_complete",
                    total_pages=total_pages,
                    text_length=len(full_text),
                    tables_found=tables_found,
                    processing_time_ms=extraction_time_ms
                )
                
                return full_text, metadata
                
        except Exception as e:
            extraction_time_ms = int((time.time() - start_time) * 1000)
            
            logger.error(
                "Native PDF extraction failed",
                event="native_extraction_error",
                error=str(e),
                processing_time_ms=extraction_time_ms
            )
            raise Exception(f"Erro ao extrair texto do PDF nativo: {str(e)}")
    
    def extract_from_scanned_pdf(self, pdf_bytes: bytes, dpi: int = 300) -> Tuple[str, dict]:
        """
        Extrai texto de PDF escaneado usando PaddleOCR.
        
        Args:
            pdf_bytes: Bytes do arquivo PDF
            dpi: DPI para conversão de PDF para imagem
            
        Returns:
            Tuple (texto_extraido, metadados)
        """
        start_time = time.time()
        
        try:
            logger.info(
                "Starting scanned PDF extraction",
                event="scanned_extraction_start",
                method="paddleocr",
                dpi=dpi
            )
            
            # Converte PDF para imagens
            conversion_start = time.time()
            images = convert_from_bytes(pdf_bytes, dpi=dpi)
            conversion_time_ms = int((time.time() - conversion_start) * 1000)
            
            logger.info(
                "PDF converted to images",
                event="pdf_to_images",
                total_pages=len(images),
                conversion_time_ms=conversion_time_ms
            )
            
            text_parts = []
            total_confidence = 0
            total_detections = 0
            
            for page_num, image in enumerate(images, 1):
                page_start = time.time()
                text_parts.append(f"--- Página {page_num} ---")
                
                # Converte PIL Image para numpy array
                img_array = np.array(image)
                
                logger.debug(
                    "Processing page with OCR",
                    event="ocr_page_start",
                    page_number=page_num,
                    image_shape=img_array.shape
                )
                
                # Executa OCR
                ocr_result = self.ocr.ocr(img_array, cls=True)
                
                page_detections = 0
                page_confidence_sum = 0
                
                if ocr_result and ocr_result[0]:
                    page_lines = []
                    
                    for line in ocr_result[0]:
                        if line:
                            text = line[1][0]  # Texto detectado
                            confidence = line[1][1]  # Confiança
                            
                            page_lines.append(text)
                            total_confidence += confidence
                            total_detections += 1
                            page_confidence_sum += confidence
                            page_detections += 1
                    
                    text_parts.append("\n".join(page_lines))
                
                page_time_ms = int((time.time() - page_start) * 1000)
                page_avg_confidence = page_confidence_sum / page_detections if page_detections > 0 else 0.0
                
                logger.debug(
                    "Page OCR completed",
                    event="ocr_page_complete",
                    page_number=page_num,
                    detections=page_detections,
                    avg_confidence=round(page_avg_confidence, 3),
                    processing_time_ms=page_time_ms
                )
            
            full_text = "\n".join(text_parts)
            
            avg_confidence = total_confidence / total_detections if total_detections > 0 else 0.0
            
            metadata = {
                "total_pages": len(images),
                "extraction_method": "paddleocr",
                "average_confidence": round(avg_confidence, 3),
                "total_detections": total_detections
            }
            
            extraction_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "Scanned PDF extraction completed",
                event="scanned_extraction_complete",
                total_pages=len(images),
                text_length=len(full_text),
                total_detections=total_detections,
                avg_confidence=round(avg_confidence, 3),
                processing_time_ms=extraction_time_ms
            )
            
            return full_text, metadata
            
        except Exception as e:
            extraction_time_ms = int((time.time() - start_time) * 1000)
            
            logger.error(
                "Scanned PDF extraction failed",
                event="scanned_extraction_error",
                error=str(e),
                processing_time_ms=extraction_time_ms
            )
            raise Exception(f"Erro ao extrair texto do PDF escaneado: {str(e)}")
    
    def normalize_text(self, text: str) -> str:
        """
        Normaliza o texto extraído removendo ruídos e espaços extras.
        
        Args:
            text: Texto bruto
            
        Returns:
            Texto normalizado
        """
        if not text:
            return ""
        
        # Remove múltiplos espaços
        text = re.sub(r' +', ' ', text)
        
        # Remove múltiplas quebras de linha (mais de 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove espaços no início e fim de cada linha
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove linhas vazias no início e fim
        text = text.strip()
        
        return text
    
    def prepare_text_for_llm(self, text: str, metadata: dict = None) -> dict:
        """
        Prepara o texto extraído para ser consumido por LLMs (como Groq, GPT, etc).
        Estrutura o texto de forma otimizada para prompts de LLM.
        
        Args:
            text: Texto extraído e normalizado
            metadata: Metadados da extração (opcional)
            
        Returns:
            Dicionário com texto estruturado para LLM
        """
        # Conta estatísticas do texto
        lines = text.split('\n')
        words = text.split()
        
        # Identifica seções principais (heurística simples)
        sections = {}
        current_section = "header"
        section_content = []
        
        for line in lines:
            if line.strip():
                # Detecta possíveis títulos/seções
                if line.isupper() and len(line) > 10 and len(line) < 100:
                    if section_content:
                        sections[current_section] = '\n'.join(section_content)
                        section_content = []
                    current_section = line.strip().lower()[:30]
                section_content.append(line)
        
        # Adiciona última seção
        if section_content:
            sections[current_section] = '\n'.join(section_content)
        
        # Prepara estrutura otimizada para LLM
        llm_prompt = {
            "system_instruction": "Você receberá um documento financeiro extraído via OCR. Analise e extraia informações estruturadas.",
            "document_content": text,
            "document_stats": {
                "total_lines": len(lines),
                "total_words": len(words),
                "total_chars": len(text),
                "has_sections": len(sections) > 1
            },
            "extraction_metadata": metadata or {},
            "structured_sections": sections,
            "suggested_prompt": f"""Analise o seguinte documento financeiro e extraia:
1. Tipo do documento (boleto, fatura, nota fiscal, extrato)
2. Nome da empresa emissora
3. CNPJ/CPF
4. Datas importantes (emissão, vencimento)
5. Valores monetários
6. Itens ou transações listadas

Documento:
{text[:1000]}...
""" if len(text) > 1000 else f"""Analise o seguinte documento financeiro e extraia as informações relevantes:

{text}
"""
        }
        
        return llm_prompt
    
    def extract_text(self, pdf_bytes: bytes, pdf_type: str = "native") -> Tuple[str, dict]:
        """
        Extrai texto do PDF baseado no tipo detectado.
        
        Args:
            pdf_bytes: Bytes do arquivo PDF
            pdf_type: Tipo do PDF ('native' ou 'scanned')
            
        Returns:
            Tuple (texto_extraido_normalizado, metadados)
        """
        overall_start = time.time()
        
        try:
            logger.info(
                "Text extraction started",
                event="text_extraction_start",
                pdf_type=pdf_type
            )
            
            if pdf_type == "native":
                raw_text, metadata = self.extract_from_native_pdf(pdf_bytes)
            elif pdf_type == "scanned":
                raw_text, metadata = self.extract_from_scanned_pdf(pdf_bytes)
            else:
                # Tenta nativo primeiro, se falhar tenta escaneado
                logger.debug(
                    "Unknown PDF type, trying native first",
                    event="fallback_extraction"
                )
                try:
                    raw_text, metadata = self.extract_from_native_pdf(pdf_bytes)
                    if len(raw_text.strip()) < 50:  # Pouco texto, tenta OCR
                        logger.debug(
                            "Native extraction insufficient, switching to OCR",
                            event="fallback_to_ocr",
                            text_length=len(raw_text)
                        )
                        raw_text, metadata = self.extract_from_scanned_pdf(pdf_bytes)
                except:
                    logger.debug(
                        "Native extraction failed, using OCR",
                        event="fallback_to_ocr_error"
                    )
                    raw_text, metadata = self.extract_from_scanned_pdf(pdf_bytes)
            
            # Normaliza o texto
            normalization_start = time.time()
            normalized_text = self.normalize_text(raw_text)
            normalization_time_ms = int((time.time() - normalization_start) * 1000)
            
            metadata["raw_text_length"] = len(raw_text)
            metadata["normalized_text_length"] = len(normalized_text)
            
            total_time_ms = int((time.time() - overall_start) * 1000)
            
            logger.info(
                "Text extraction completed",
                event="text_extraction_complete",
                raw_text_length=len(raw_text),
                normalized_text_length=len(normalized_text),
                normalization_time_ms=normalization_time_ms,
                total_processing_time_ms=total_time_ms,
                extraction_method=metadata.get("extraction_method")
            )
            
            return normalized_text, metadata
            
        except Exception as e:
            total_time_ms = int((time.time() - overall_start) * 1000)
            
            logger.error(
                "Text extraction failed",
                event="text_extraction_error",
                error=str(e),
                pdf_type=pdf_type,
                processing_time_ms=total_time_ms
            )
            raise Exception(f"Erro ao extrair texto: {str(e)}")
