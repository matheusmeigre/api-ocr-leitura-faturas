import pdfplumber
import io
from typing import Tuple


def detect_pdf_type(pdf_bytes: bytes) -> Tuple[str, float]:
    """
    Detecta se um PDF é nativo (com texto) ou escaneado (somente imagens).
    
    Args:
        pdf_bytes: Bytes do arquivo PDF
        
    Returns:
        Tuple (tipo, confiança) onde:
            tipo: 'native' ou 'scanned'
            confiança: valor de 0.0 a 1.0 indicando a confiança da detecção
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            
            if total_pages == 0:
                return "unknown", 0.0
            
            # Verifica as primeiras páginas para determinar o tipo
            pages_to_check = min(3, total_pages)
            text_chars_total = 0
            
            for i in range(pages_to_check):
                page = pdf.pages[i]
                text = page.extract_text()
                
                if text:
                    # Remove espaços e quebras de linha para contar caracteres reais
                    clean_text = text.replace(" ", "").replace("\n", "").replace("\t", "")
                    text_chars_total += len(clean_text)
            
            # Define limiar: se tem mais de 100 caracteres, provavelmente é nativo
            avg_chars_per_page = text_chars_total / pages_to_check
            
            if avg_chars_per_page > 100:
                # PDF nativo (com texto)
                confidence = min(1.0, avg_chars_per_page / 500)  # Normaliza até 500 chars
                return "native", confidence
            else:
                # PDF escaneado (pouco ou nenhum texto)
                confidence = 1.0 - min(1.0, avg_chars_per_page / 100)
                return "scanned", confidence
                
    except Exception as e:
        print(f"Erro ao detectar tipo de PDF: {str(e)}")
        return "unknown", 0.0


def is_valid_pdf(pdf_bytes: bytes) -> bool:
    """
    Valida se os bytes representam um arquivo PDF válido.
    
    Args:
        pdf_bytes: Bytes do arquivo
        
    Returns:
        True se é um PDF válido, False caso contrário
    """
    try:
        # Verifica assinatura do PDF
        if not pdf_bytes.startswith(b'%PDF'):
            return False
            
        # Tenta abrir com pdfplumber
        pdf_file = io.BytesIO(pdf_bytes)
        with pdfplumber.open(pdf_file) as pdf:
            # Verifica se tem ao menos uma página
            return len(pdf.pages) > 0
            
    except Exception:
        return False


def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """
    Extrai metadados do PDF.
    
    Args:
        pdf_bytes: Bytes do arquivo PDF
        
    Returns:
        Dicionário com metadados
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        
        with pdfplumber.open(pdf_file) as pdf:
            metadata = pdf.metadata or {}
            
            return {
                "pages": len(pdf.pages),
                "creator": metadata.get("Creator", ""),
                "producer": metadata.get("Producer", ""),
                "creation_date": metadata.get("CreationDate", ""),
                "title": metadata.get("Title", "")
            }
            
    except Exception as e:
        return {"error": str(e)}
