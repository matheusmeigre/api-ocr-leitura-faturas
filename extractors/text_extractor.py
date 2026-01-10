import pdfplumber
import io
import re
from typing import Tuple, Optional
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
import numpy as np
from PIL import Image
from config import settings


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
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            text_parts = []
            
            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extrai texto
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_parts.append(f"--- Página {page_num} ---\n{page_text}")
                    
                    # Tenta extrair tabelas se existirem
                    tables = page.extract_tables()
                    if tables:
                        for table_idx, table in enumerate(tables, 1):
                            text_parts.append(f"\n[Tabela {table_idx} da página {page_num}]")
                            for row in table:
                                if row:
                                    text_parts.append(" | ".join([str(cell) if cell else "" for cell in row]))
                
                full_text = "\n".join(text_parts)
                
                metadata = {
                    "total_pages": total_pages,
                    "extraction_method": "pdfplumber",
                    "has_tables": any(page.extract_tables() for page in pdf.pages)
                }
                
                return full_text, metadata
                
        except Exception as e:
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
        try:
            # Converte PDF para imagens
            images = convert_from_bytes(pdf_bytes, dpi=dpi)
            
            text_parts = []
            total_confidence = 0
            total_detections = 0
            
            for page_num, image in enumerate(images, 1):
                text_parts.append(f"--- Página {page_num} ---")
                
                # Converte PIL Image para numpy array
                img_array = np.array(image)
                
                # Executa OCR
                ocr_result = self.ocr.ocr(img_array, cls=True)
                
                if ocr_result and ocr_result[0]:
                    page_lines = []
                    
                    for line in ocr_result[0]:
                        if line:
                            text = line[1][0]  # Texto detectado
                            confidence = line[1][1]  # Confiança
                            
                            page_lines.append(text)
                            total_confidence += confidence
                            total_detections += 1
                    
                    text_parts.append("\n".join(page_lines))
            
            full_text = "\n".join(text_parts)
            
            avg_confidence = total_confidence / total_detections if total_detections > 0 else 0.0
            
            metadata = {
                "total_pages": len(images),
                "extraction_method": "paddleocr",
                "average_confidence": round(avg_confidence, 3),
                "total_detections": total_detections
            }
            
            return full_text, metadata
            
        except Exception as e:
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
        try:
            if pdf_type == "native":
                raw_text, metadata = self.extract_from_native_pdf(pdf_bytes)
            elif pdf_type == "scanned":
                raw_text, metadata = self.extract_from_scanned_pdf(pdf_bytes)
            else:
                # Tenta nativo primeiro, se falhar tenta escaneado
                try:
                    raw_text, metadata = self.extract_from_native_pdf(pdf_bytes)
                    if len(raw_text.strip()) < 50:  # Pouco texto, tenta OCR
                        raw_text, metadata = self.extract_from_scanned_pdf(pdf_bytes)
                except:
                    raw_text, metadata = self.extract_from_scanned_pdf(pdf_bytes)
            
            # Normaliza o texto
            normalized_text = self.normalize_text(raw_text)
            
            metadata["raw_text_length"] = len(raw_text)
            metadata["normalized_text_length"] = len(normalized_text)
            
            return normalized_text, metadata
            
        except Exception as e:
            raise Exception(f"Erro ao extrair texto: {str(e)}")
