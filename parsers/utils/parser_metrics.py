"""Sistema de métricas para monitoramento do parser financeiro"""
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import json


class ParserMetrics:
    """
    Coleta e agrupa métricas de parsing para observabilidade.
    
    Métricas coletadas:
    - Taxa de sucesso por banco
    - Taxa de fallback para parser genérico
    - Confiança média por banco
    - Tempo de processamento
    - Campos extraídos com sucesso
    """
    
    def __init__(self):
        """Inicializa o coletor de métricas"""
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "by_bank": defaultdict(lambda: {
                "count": 0,
                "success": 0,
                "fallback": 0,
                "confidence_sum": 0.0,
                "confidence_count": 0,
                "processing_time_sum": 0.0,
                "fields_extracted": defaultdict(int)
            }),
            "parser_usage": defaultdict(int),
            "cache_stats": {
                "hits": 0,
                "misses": 0
            }
        }
    
    def record_parse_attempt(
        self,
        bank: Optional[str],
        parser_type: str,
        confidence: float,
        processing_time: float,
        success: bool,
        fields_extracted: List[str],
        used_fallback: bool = False
    ):
        """
        Registra uma tentativa de parsing.
        
        Args:
            bank: Nome do banco detectado (ou None)
            parser_type: Tipo de parser usado ('specialized' ou 'generic')
            confidence: Confiança da detecção (0.0 a 1.0)
            processing_time: Tempo de processamento em segundos
            success: Se o parsing foi bem-sucedido
            fields_extracted: Lista de campos extraídos com sucesso
            used_fallback: Se usou fallback para parser genérico
        """
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_parses"] += 1
        else:
            self.metrics["failed_parses"] += 1
        
        # Métricas por banco
        if bank:
            bank_metrics = self.metrics["by_bank"][bank]
            bank_metrics["count"] += 1
            
            if success:
                bank_metrics["success"] += 1
            
            if used_fallback:
                bank_metrics["fallback"] += 1
            
            bank_metrics["confidence_sum"] += confidence
            bank_metrics["confidence_count"] += 1
            bank_metrics["processing_time_sum"] += processing_time
            
            for field in fields_extracted:
                bank_metrics["fields_extracted"][field] += 1
        
        # Uso de parsers
        self.metrics["parser_usage"][parser_type] += 1
    
    def record_cache_hit(self):
        """Registra um hit no cache"""
        self.metrics["cache_stats"]["hits"] += 1
    
    def record_cache_miss(self):
        """Registra um miss no cache"""
        self.metrics["cache_stats"]["misses"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo das métricas coletadas.
        
        Returns:
            Dict com métricas agregadas
        """
        total = self.metrics["total_requests"]
        
        if total == 0:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "cache_stats": self._calculate_cache_stats(),
                "message": "Nenhuma requisição processada ainda"
            }
        
        summary = {
            "total_requests": total,
            "successful_parses": self.metrics["successful_parses"],
            "failed_parses": self.metrics["failed_parses"],
            "success_rate": self.metrics["successful_parses"] / total,
            "by_bank": {},
            "parser_usage": dict(self.metrics["parser_usage"]),
            "cache_stats": self._calculate_cache_stats()
        }
        
        # Agrega métricas por banco
        for bank, metrics in self.metrics["by_bank"].items():
            count = metrics["count"]
            if count > 0:
                summary["by_bank"][bank] = {
                    "total_requests": count,
                    "success_count": metrics["success"],
                    "success_rate": metrics["success"] / count,
                    "fallback_rate": metrics["fallback"] / count,
                    "avg_confidence": metrics["confidence_sum"] / metrics["confidence_count"] if metrics["confidence_count"] > 0 else 0.0,
                    "avg_processing_time": metrics["processing_time_sum"] / count,
                    "most_extracted_fields": self._get_top_fields(metrics["fields_extracted"], 5)
                }
        
        return summary
    
    def _calculate_cache_stats(self) -> Dict[str, Any]:
        """Calcula estatísticas do cache"""
        hits = self.metrics["cache_stats"]["hits"]
        misses = self.metrics["cache_stats"]["misses"]
        total = hits + misses
        
        return {
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "hit_rate": hits / total if total > 0 else 0.0
        }
    
    def _get_top_fields(self, fields_dict: Dict[str, int], top_n: int) -> List[Dict[str, Any]]:
        """Retorna os campos mais extraídos"""
        sorted_fields = sorted(fields_dict.items(), key=lambda x: x[1], reverse=True)
        return [
            {"field": field, "count": count}
            for field, count in sorted_fields[:top_n]
        ]
    
    def export_json(self) -> str:
        """
        Exporta métricas em formato JSON.
        
        Returns:
            String JSON com todas as métricas
        """
        summary = self.get_summary()
        summary["timestamp"] = datetime.now().isoformat()
        return json.dumps(summary, ensure_ascii=False, indent=2)
    
    def reset(self):
        """Reseta todas as métricas"""
        self.__init__()
    
    def log_summary(self):
        """Loga um resumo das métricas em formato estruturado"""
        summary = self.get_summary()
        print(json.dumps({
            "event": "metrics_summary",
            "timestamp": datetime.now().isoformat(),
            **summary
        }, ensure_ascii=False, indent=2))
