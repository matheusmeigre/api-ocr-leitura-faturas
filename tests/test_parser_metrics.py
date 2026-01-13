"""Testes para o sistema de métricas do parser"""
import pytest
from parsers.financial_parser import FinancialParser
from parsers.utils.parser_metrics import ParserMetrics


class TestParserMetrics:
    """Testes do sistema de métricas"""
    
    @pytest.fixture
    def metrics(self):
        """Fixture com sistema de métricas limpo"""
        return ParserMetrics()
    
    @pytest.fixture
    def parser(self):
        """Fixture do parser financeiro"""
        return FinancialParser()
    
    def test_metrics_initialization(self, metrics):
        """Testa inicialização do sistema de métricas"""
        summary = metrics.get_summary()
        assert summary["total_requests"] == 0
        assert summary["success_rate"] == 0.0
    
    def test_record_successful_parse(self, metrics):
        """Testa registro de parsing bem-sucedido"""
        metrics.record_parse_attempt(
            bank="nubank",
            parser_type="specialized",
            confidence=0.95,
            processing_time=0.123,
            success=True,
            fields_extracted=["empresa", "cnpj", "valor_total"],
            used_fallback=False
        )
        
        summary = metrics.get_summary()
        assert summary["total_requests"] == 1
        assert summary["successful_parses"] == 1
        assert summary["success_rate"] == 1.0
        assert "nubank" in summary["by_bank"]
        assert summary["by_bank"]["nubank"]["success_rate"] == 1.0
    
    def test_record_fallback_usage(self, metrics):
        """Testa registro de uso de fallback"""
        metrics.record_parse_attempt(
            bank="unknown",
            parser_type="generic",
            confidence=0.0,
            processing_time=0.150,
            success=True,
            fields_extracted=["empresa", "valor_total"],
            used_fallback=True
        )
        
        summary = metrics.get_summary()
        assert summary["parser_usage"]["generic"] == 1
    
    def test_cache_stats(self, metrics):
        """Testa estatísticas de cache"""
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        
        summary = metrics.get_summary()
        cache_stats = summary["cache_stats"]
        assert cache_stats["hits"] == 2
        assert cache_stats["misses"] == 1
        assert cache_stats["hit_rate"] == 2/3
    
    def test_metrics_aggregation(self, metrics):
        """Testa agregação de múltiplas requisições"""
        # Simula 10 requisições do Nubank
        for i in range(10):
            metrics.record_parse_attempt(
                bank="nubank",
                parser_type="specialized",
                confidence=0.9 + (i * 0.01),
                processing_time=0.1 + (i * 0.01),
                success=True,
                fields_extracted=["empresa", "cnpj", "valor_total"],
                used_fallback=False
            )
        
        summary = metrics.get_summary()
        assert summary["total_requests"] == 10
        assert summary["by_bank"]["nubank"]["total_requests"] == 10
        assert summary["by_bank"]["nubank"]["avg_confidence"] > 0.9
    
    def test_metrics_export_json(self, metrics):
        """Testa exportação de métricas em JSON"""
        metrics.record_parse_attempt(
            bank="inter",
            parser_type="specialized",
            confidence=0.85,
            processing_time=0.100,
            success=True,
            fields_extracted=["empresa", "cnpj"],
            used_fallback=False
        )
        
        json_str = metrics.export_json()
        assert json_str is not None
        assert "total_requests" in json_str
        assert "inter" in json_str
    
    def test_parser_has_metrics(self, parser):
        """Testa que o parser tem sistema de métricas"""
        if parser.metrics:
            assert hasattr(parser, 'get_metrics_summary')
            assert hasattr(parser, 'export_metrics_json')
            assert hasattr(parser, 'reset_metrics')
    
    def test_metrics_collection_in_parsing(self, parser):
        """Testa que métricas são coletadas durante parsing"""
        if parser.metrics:
            # Reseta métricas
            parser.reset_metrics()
            
            # Faz parsing
            text = """
            Nubank
            Esta é a sua fatura
            Total: R$ 1.000,00
            """
            parser.parse_financial_data(text)
            
            # Verifica métricas
            summary = parser.get_metrics_summary()
            assert summary is not None
            assert summary["total_requests"] == 1
