from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date


class ItemFinanceiro(BaseModel):
    """Item financeiro (linha de fatura, produto, etc.)"""
    descricao: str = Field(..., description="Descrição do item")
    valor: Optional[float] = Field(None, description="Valor do item")
    quantidade: Optional[float] = Field(None, description="Quantidade")
    data: Optional[str] = Field(None, description="Data do item")


class DadosFinanceiros(BaseModel):
    """Dados financeiros extraídos do documento"""
    empresa: Optional[str] = Field(None, description="Nome da empresa emissora")
    cnpj: Optional[str] = Field(None, description="CNPJ da empresa")
    cpf: Optional[str] = Field(None, description="CPF quando aplicável")
    data_emissao: Optional[str] = Field(None, description="Data de emissão do documento")
    data_vencimento: Optional[str] = Field(None, description="Data de vencimento")
    valor_total: Optional[float] = Field(None, description="Valor total do documento")
    moeda: str = Field(default="BRL", description="Moeda (padrão BRL)")
    itens: Optional[List[ItemFinanceiro]] = Field(default_factory=list, description="Lista de itens")
    numero_documento: Optional[str] = Field(None, description="Número do documento/fatura")
    codigo_barras: Optional[str] = Field(None, description="Código de barras (para boletos)")
    linha_digitavel: Optional[str] = Field(None, description="Linha digitável (para boletos)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "empresa": "Empresa Exemplo LTDA",
                "cnpj": "12.345.678/0001-90",
                "data_emissao": "2026-01-01",
                "data_vencimento": "2026-01-15",
                "valor_total": 1500.00,
                "moeda": "BRL",
                "numero_documento": "123456",
                "itens": [
                    {
                        "descricao": "Serviço A",
                        "valor": 500.00
                    }
                ]
            }
        }


class ExtractionResponse(BaseModel):
    """Resposta da API de extração"""
    success: bool = Field(..., description="Indica se a extração foi bem sucedida")
    document_type: Optional[str] = Field(None, description="Tipo do documento detectado")
    confidence: float = Field(default=0.0, description="Confiança da extração (0.0 a 1.0)")
    raw_text: str = Field(..., description="Texto bruto extraído do documento")
    data: DadosFinanceiros = Field(..., description="Dados financeiros estruturados")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "document_type": "fatura_cartao",
                "confidence": 0.85,
                "raw_text": "FATURA CARTÃO DE CRÉDITO...",
                "data": {
                    "empresa": "Banco Exemplo S.A.",
                    "cnpj": "12.345.678/0001-90",
                    "data_emissao": "2026-01-01",
                    "data_vencimento": "2026-01-15",
                    "valor_total": 1500.00,
                    "moeda": "BRL"
                },
                "metadata": {
                    "pdf_type": "native",
                    "pages": 2
                }
            }
        }


class ErrorResponse(BaseModel):
    """Resposta de erro"""
    success: bool = Field(default=False)
    error: str = Field(..., description="Mensagem de erro")
    detail: Optional[str] = Field(None, description="Detalhes adicionais do erro")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Falha ao processar arquivo",
                "detail": "Arquivo corrompido ou formato inválido"
            }
        }
