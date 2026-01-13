"""Testes para o sistema de feedback"""
import pytest
import sqlite3
from pathlib import Path
from parsers.utils.feedback_system import FeedbackSystem


class TestFeedbackSystem:
    """Testes do sistema de feedback"""
    
    @pytest.fixture
    def feedback_system(self):
        """Fixture com sistema de feedback de teste"""
        db_path = "test_feedback.db"
        fs = FeedbackSystem(db_path=db_path)
        yield fs
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_initialization(self, feedback_system):
        """Testa inicialização do banco de dados"""
        assert Path(feedback_system.db_path).exists()
        
        # Verifica tabelas
        conn = sqlite3.connect(feedback_system.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert 'feedback' in tables
    
    def test_submit_feedback(self, feedback_system):
        """Testa submissão de feedback"""
        feedback_id = feedback_system.submit_feedback(
            document_text="Nubank fatura R$ 100",
            detected_bank="inter",
            correct_bank="nubank",
            detection_confidence=0.45,
            feedback_type="correction",
            user_comment="Banco detectado incorretamente"
        )
        
        assert feedback_id > 0
    
    def test_get_unprocessed_feedback(self, feedback_system):
        """Testa obtenção de feedbacks não processados"""
        # Submete alguns feedbacks
        for i in range(3):
            feedback_system.submit_feedback(
                document_text=f"Document {i}",
                correct_bank="nubank"
            )
        
        feedbacks = feedback_system.get_unprocessed_feedback()
        
        assert len(feedbacks) == 3
        assert all(fb['processed'] == 0 for fb in feedbacks)
    
    def test_mark_as_processed(self, feedback_system):
        """Testa marcação de feedbacks como processados"""
        # Submete feedback
        fb_id = feedback_system.submit_feedback(
            document_text="Test document",
            correct_bank="nubank"
        )
        
        # Marca como processado
        feedback_system.mark_as_processed([fb_id])
        
        # Verifica que não aparece mais em unprocessed
        feedbacks = feedback_system.get_unprocessed_feedback()
        assert len(feedbacks) == 0
    
    def test_get_feedback_stats(self, feedback_system):
        """Testa estatísticas de feedback"""
        # Submete vários feedbacks
        for i in range(5):
            feedback_system.submit_feedback(
                document_text=f"Doc {i}",
                correct_bank="nubank" if i % 2 == 0 else "inter",
                feedback_type="correction"
            )
        
        stats = feedback_system.get_feedback_stats()
        
        assert stats['total_feedback'] == 5
        assert stats['unprocessed'] == 5
        assert 'by_type' in stats
        assert 'top_banks' in stats
    
    def test_export_training_data(self, feedback_system):
        """Testa exportação de dados de treinamento"""
        # Submete feedbacks
        for i in range(10):
            feedback_system.submit_feedback(
                document_text=f"Document {i}",
                detected_bank="inter",
                correct_bank="nubank",
                detection_confidence=0.5
            )
        
        output_path = "test_training_data.json"
        success = feedback_system.export_training_data(output_path)
        
        assert success == True
        assert Path(output_path).exists()
        
        # Cleanup
        Path(output_path).unlink()
    
    def test_get_problematic_cases(self, feedback_system):
        """Testa obtenção de casos problemáticos"""
        # Submete feedbacks com baixa confiança
        feedback_system.submit_feedback(
            document_text="Ambiguous document",
            detected_bank="inter",
            correct_bank="nubank",
            detection_confidence=0.30
        )
        
        feedback_system.submit_feedback(
            document_text="Another ambiguous",
            detected_bank="c6",
            correct_bank="picpay",
            detection_confidence=0.40
        )
        
        cases = feedback_system.get_problematic_cases(min_confidence=0.5)
        
        assert len(cases) == 2
        assert all(case['detection_confidence'] < 0.5 for case in cases)
    
    def test_feedback_with_extracted_data(self, feedback_system):
        """Testa feedback com dados extraídos"""
        extracted = {
            "empresa": "Banco Inter",
            "valor_total": 100.50
        }
        
        correct = {
            "empresa": "Nubank",
            "valor_total": 150.75
        }
        
        feedback_id = feedback_system.submit_feedback(
            document_text="Test doc",
            extracted_data=extracted,
            correct_data=correct,
            correct_bank="nubank"
        )
        
        assert feedback_id > 0
        
        # Verifica que foi salvo corretamente
        feedbacks = feedback_system.get_unprocessed_feedback()
        assert len(feedbacks) == 1
        assert feedbacks[0]['extracted_data'] == extracted
        assert feedbacks[0]['correct_data'] == correct
