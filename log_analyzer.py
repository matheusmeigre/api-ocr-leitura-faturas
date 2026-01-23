#!/usr/bin/env python3
"""
Utilitários para análise de logs estruturados JSON da API OCR.

Este script fornece funções úteis para:
- Análise de performance
- Detecção de problemas
- Geração de relatórios
- Visualização de métricas

Uso:
    python log_analyzer.py analyze logs/api-ocr.json
    python log_analyzer.py metrics logs/api-ocr.json
    python log_analyzer.py errors logs/api-ocr.json
    python log_analyzer.py trace <trace_id> logs/api-ocr.json
"""

import json
import sys
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any
import statistics


class LogAnalyzer:
    """Analisador de logs JSON estruturados"""
    
    def __init__(self, log_file: str):
        """
        Inicializa o analisador.
        
        Args:
            log_file: Caminho para o arquivo de logs JSON
        """
        self.log_file = log_file
        self.logs = self._load_logs()
    
    def _load_logs(self) -> List[Dict[str, Any]]:
        """Carrega e parseia o arquivo de logs"""
        logs = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log = json.loads(line.strip())
                        logs.append(log)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {self.log_file}")
            sys.exit(1)
        
        return logs
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analisa métricas de performance"""
        print("\n📊 ANÁLISE DE PERFORMANCE")
        print("=" * 60)
        
        # Coleta tempos de processamento
        processing_times = [
            log['processing_time_ms']
            for log in self.logs
            if 'processing_time_ms' in log and log.get('event') == 'request_completed'
        ]
        
        if not processing_times:
            print("⚠️  Nenhum dado de performance encontrado")
            return {}
        
        metrics = {
            'total_requests': len(processing_times),
            'avg_time_ms': round(statistics.mean(processing_times), 2),
            'median_time_ms': round(statistics.median(processing_times), 2),
            'min_time_ms': min(processing_times),
            'max_time_ms': max(processing_times),
            'p95_time_ms': round(statistics.quantiles(processing_times, n=20)[18], 2),
            'p99_time_ms': round(statistics.quantiles(processing_times, n=100)[98], 2)
        }
        
        print(f"📈 Total de Requisições: {metrics['total_requests']}")
        print(f"⏱️  Tempo Médio: {metrics['avg_time_ms']}ms")
        print(f"⏱️  Mediana: {metrics['median_time_ms']}ms")
        print(f"⚡ Mais Rápido: {metrics['min_time_ms']}ms")
        print(f"🐌 Mais Lento: {metrics['max_time_ms']}ms")
        print(f"📊 P95: {metrics['p95_time_ms']}ms")
        print(f"📊 P99: {metrics['p99_time_ms']}ms")
        
        # Requisições lentas (> 3s)
        slow_requests = [t for t in processing_times if t > 3000]
        if slow_requests:
            print(f"\n⚠️  Requisições Lentas (>3s): {len(slow_requests)}")
            print(f"   {(len(slow_requests) / len(processing_times) * 100):.1f}% do total")
        
        return metrics
    
    def analyze_success_rate(self) -> Dict[str, Any]:
        """Analisa taxa de sucesso"""
        print("\n✅ TAXA DE SUCESSO")
        print("=" * 60)
        
        completed = [
            log for log in self.logs
            if log.get('event') == 'request_completed'
        ]
        
        if not completed:
            print("⚠️  Nenhuma requisição concluída encontrada")
            return {}
        
        successful = [log for log in completed if log.get('success') == True]
        
        success_rate = len(successful) / len(completed) * 100
        
        print(f"📊 Total de Requisições: {len(completed)}")
        print(f"✅ Bem-sucedidas: {len(successful)}")
        print(f"❌ Falhas: {len(completed) - len(successful)}")
        print(f"📈 Taxa de Sucesso: {success_rate:.2f}%")
        
        return {
            'total': len(completed),
            'successful': len(successful),
            'failed': len(completed) - len(successful),
            'success_rate': round(success_rate, 2)
        }
    
    def analyze_errors(self) -> Dict[str, Any]:
        """Analisa erros"""
        print("\n❌ ANÁLISE DE ERROS")
        print("=" * 60)
        
        errors = [log for log in self.logs if log.get('level') == 'error']
        
        if not errors:
            print("✅ Nenhum erro encontrado!")
            return {}
        
        # Agrupa por tipo de erro
        error_types = Counter([log.get('error_type', 'Unknown') for log in errors])
        
        print(f"🔴 Total de Erros: {len(errors)}")
        print("\n📊 Por Tipo:")
        for error_type, count in error_types.most_common():
            print(f"   • {error_type}: {count}")
        
        # Erros por arquivo
        file_errors = defaultdict(int)
        for log in errors:
            if 'file_name' in log:
                file_errors[log['file_name']] += 1
        
        if file_errors:
            print("\n📁 Arquivos com Mais Erros:")
            for file_name, count in sorted(file_errors.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {file_name}: {count} erro(s)")
        
        return {
            'total_errors': len(errors),
            'by_type': dict(error_types),
            'by_file': dict(file_errors)
        }
    
    def analyze_document_types(self) -> Dict[str, Any]:
        """Analisa tipos de documentos processados"""
        print("\n📄 TIPOS DE DOCUMENTOS")
        print("=" * 60)
        
        documents = [
            log for log in self.logs
            if log.get('event') == 'extraction_result'
        ]
        
        if not documents:
            print("⚠️  Nenhum documento processado encontrado")
            return {}
        
        doc_types = Counter([log.get('document_type', 'Unknown') for log in documents])
        
        print(f"📊 Total Processados: {len(documents)}")
        print("\n📈 Distribuição:")
        for doc_type, count in doc_types.most_common():
            percentage = count / len(documents) * 100
            print(f"   • {doc_type}: {count} ({percentage:.1f}%)")
        
        return {
            'total': len(documents),
            'by_type': dict(doc_types)
        }
    
    def analyze_banks(self) -> Dict[str, Any]:
        """Analisa bancos detectados"""
        print("\n🏦 BANCOS DETECTADOS")
        print("=" * 60)
        
        banks = [
            log for log in self.logs
            if log.get('event') == 'bank_detection' and log.get('bank')
        ]
        
        if not banks:
            print("⚠️  Nenhum banco detectado")
            return {}
        
        bank_counts = Counter([log['bank'] for log in banks])
        
        print(f"📊 Total de Detecções: {len(banks)}")
        print("\n🏆 Top Bancos:")
        for bank, count in bank_counts.most_common():
            percentage = count / len(banks) * 100
            print(f"   • {bank}: {count} ({percentage:.1f}%)")
        
        # Confiança média por banco
        bank_confidence = defaultdict(list)
        for log in banks:
            bank_confidence[log['bank']].append(log.get('confidence', 0))
        
        print("\n📊 Confiança Média por Banco:")
        for bank, confidences in bank_confidence.items():
            avg_conf = statistics.mean(confidences) if confidences else 0
            print(f"   • {bank}: {avg_conf:.3f}")
        
        return {
            'total': len(banks),
            'by_bank': dict(bank_counts),
            'avg_confidence': {
                bank: round(statistics.mean(confs), 3)
                for bank, confs in bank_confidence.items()
            }
        }
    
    def analyze_ocr_performance(self) -> Dict[str, Any]:
        """Analisa performance do OCR"""
        print("\n🔍 PERFORMANCE OCR")
        print("=" * 60)
        
        ocr_results = [
            log for log in self.logs
            if log.get('event') == 'ocr_result' and log.get('success')
        ]
        
        if not ocr_results:
            print("⚠️  Nenhum resultado OCR encontrado")
            return {}
        
        confidences = [log.get('avg_confidence', 0) for log in ocr_results]
        times = [log.get('processing_time_ms', 0) for log in ocr_results]
        
        print(f"📊 Total de OCRs: {len(ocr_results)}")
        print(f"📈 Confiança Média: {statistics.mean(confidences):.3f}")
        print(f"⏱️  Tempo Médio: {statistics.mean(times):.0f}ms")
        
        # Por tipo de PDF
        by_type = defaultdict(list)
        for log in self.logs:
            if log.get('event') == 'ocr_processing':
                pdf_type = log.get('pdf_type')
                if pdf_type:
                    by_type[pdf_type].append(log)
        
        if by_type:
            print("\n📄 Por Tipo de PDF:")
            for pdf_type, logs in by_type.items():
                print(f"   • {pdf_type}: {len(logs)} processamento(s)")
        
        return {
            'total_ocrs': len(ocr_results),
            'avg_confidence': round(statistics.mean(confidences), 3),
            'avg_time_ms': round(statistics.mean(times), 0),
            'by_pdf_type': {k: len(v) for k, v in by_type.items()}
        }
    
    def trace_request(self, trace_id: str):
        """Rastreia uma requisição específica por trace_id"""
        print(f"\n🔎 RASTREAMENTO: {trace_id}")
        print("=" * 60)
        
        request_logs = [
            log for log in self.logs
            if log.get('trace_id') == trace_id
        ]
        
        if not request_logs:
            print(f"❌ Nenhum log encontrado para trace_id: {trace_id}")
            return
        
        # Ordena por timestamp
        request_logs.sort(key=lambda x: x.get('timestamp', ''))
        
        print(f"📊 Total de Logs: {len(request_logs)}")
        print("\n📝 Timeline:\n")
        
        for i, log in enumerate(request_logs, 1):
            timestamp = log.get('timestamp', 'N/A')
            event = log.get('event', 'N/A')
            level = log.get('level', 'info')
            
            icon = {
                'info': '📘',
                'debug': '🔍',
                'warning': '⚠️',
                'error': '❌'
            }.get(level, '📄')
            
            print(f"{i:2d}. {icon} [{timestamp}] {event}")
            
            # Detalhes importantes
            if 'processing_time_ms' in log:
                print(f"    ⏱️  {log['processing_time_ms']}ms")
            if 'confidence' in log:
                print(f"    📊 Confiança: {log['confidence']}")
            if 'error' in log or 'error_message' in log:
                error = log.get('error') or log.get('error_message')
                print(f"    ❌ {error}")
            if 'file_name' in log:
                print(f"    📁 {log['file_name']}")
            if 'bank' in log:
                print(f"    🏦 {log['bank']}")
            print()
    
    def generate_report(self):
        """Gera relatório completo"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO COMPLETO DE LOGS")
        print("=" * 60)
        print(f"📁 Arquivo: {self.log_file}")
        print(f"📝 Total de Logs: {len(self.logs)}")
        
        self.analyze_performance()
        self.analyze_success_rate()
        self.analyze_errors()
        self.analyze_document_types()
        self.analyze_banks()
        self.analyze_ocr_performance()
        
        print("\n" + "=" * 60)
        print("✅ Análise concluída!")
        print("=" * 60 + "\n")


def main():
    """Função principal"""
    if len(sys.argv) < 3:
        print("Uso:")
        print("  python log_analyzer.py analyze <arquivo.json>")
        print("  python log_analyzer.py metrics <arquivo.json>")
        print("  python log_analyzer.py errors <arquivo.json>")
        print("  python log_analyzer.py trace <trace_id> <arquivo.json>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'trace':
        if len(sys.argv) < 4:
            print("❌ Trace ID não fornecido")
            sys.exit(1)
        trace_id = sys.argv[2]
        log_file = sys.argv[3]
        analyzer = LogAnalyzer(log_file)
        analyzer.trace_request(trace_id)
    else:
        log_file = sys.argv[2]
        analyzer = LogAnalyzer(log_file)
        
        if command == 'analyze':
            analyzer.generate_report()
        elif command == 'metrics':
            analyzer.analyze_performance()
            analyzer.analyze_ocr_performance()
        elif command == 'errors':
            analyzer.analyze_errors()
        else:
            print(f"❌ Comando desconhecido: {command}")
            sys.exit(1)


if __name__ == '__main__':
    main()
