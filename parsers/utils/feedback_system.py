"""
Sistema de feedback do usuário para melhorar parsers.

Coleta correções dos usuários e armazena para retreinamento.
"""
import json
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FeedbackSystem:
    """
    Sistema de feedback para coletar correções de usuários.
    
    Armazena:
    - Texto original do documento
    - Banco detectado vs correto
    - Campos extraídos vs corretos
    - Timestamp e metadados
    """
    
    def __init__(self, db_path: str = "feedback.db"):
        """
        Inicializa o sistema de feedback.
        
        Args:
            db_path: Caminho para arquivo SQLite de feedback
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de feedback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    document_text TEXT NOT NULL,
                    detected_bank TEXT,
                    correct_bank TEXT,
                    detection_confidence REAL,
                    extracted_data TEXT,
                    correct_data TEXT,
                    feedback_type TEXT,
                    user_comment TEXT,
                    processed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para consultas rápidas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_correct_bank 
                ON feedback(correct_bank)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed 
                ON feedback(processed)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON feedback(timestamp)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Feedback database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize feedback database: {e}")
    
    def submit_feedback(
        self,
        document_text: str,
        detected_bank: Optional[str] = None,
        correct_bank: Optional[str] = None,
        detection_confidence: Optional[float] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
        correct_data: Optional[Dict[str, Any]] = None,
        feedback_type: str = "correction",
        user_comment: Optional[str] = None
    ) -> int:
        """
        Registra feedback do usuário.
        
        Args:
            document_text: Texto original do documento
            detected_bank: Banco detectado pelo sistema
            correct_bank: Banco correto segundo usuário
            detection_confidence: Confiança da detecção original
            extracted_data: Dados extraídos pelo sistema
            correct_data: Dados corretos segundo usuário
            feedback_type: Tipo de feedback (correction, suggestion, bug)
            user_comment: Comentário adicional do usuário
            
        Returns:
            ID do feedback criado
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO feedback (
                    timestamp, document_text, detected_bank, correct_bank,
                    detection_confidence, extracted_data, correct_data,
                    feedback_type, user_comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                document_text,
                detected_bank,
                correct_bank,
                detection_confidence,
                json.dumps(extracted_data, ensure_ascii=False) if extracted_data else None,
                json.dumps(correct_data, ensure_ascii=False) if correct_data else None,
                feedback_type,
                user_comment
            ))
            
            feedback_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Feedback submitted: ID={feedback_id}, type={feedback_type}")
            return feedback_id
            
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            return -1
    
    def get_unprocessed_feedback(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retorna feedbacks não processados para retreinamento.
        
        Args:
            limit: Número máximo de feedbacks a retornar
            
        Returns:
            Lista de feedbacks
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM feedback 
                WHERE processed = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            feedbacks = []
            for row in cursor.fetchall():
                feedback = dict(row)
                
                # Parse JSON fields
                if feedback['extracted_data']:
                    feedback['extracted_data'] = json.loads(feedback['extracted_data'])
                if feedback['correct_data']:
                    feedback['correct_data'] = json.loads(feedback['correct_data'])
                
                feedbacks.append(feedback)
            
            conn.close()
            return feedbacks
            
        except Exception as e:
            logger.error(f"Failed to get unprocessed feedback: {e}")
            return []
    
    def mark_as_processed(self, feedback_ids: List[int]):
        """
        Marca feedbacks como processados.
        
        Args:
            feedback_ids: Lista de IDs de feedback
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(feedback_ids))
            cursor.execute(f"""
                UPDATE feedback 
                SET processed = 1
                WHERE id IN ({placeholders})
            """, feedback_ids)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Marked {len(feedback_ids)} feedbacks as processed")
            
        except Exception as e:
            logger.error(f"Failed to mark feedback as processed: {e}")
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de feedback.
        
        Returns:
            Dict com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de feedbacks
            cursor.execute("SELECT COUNT(*) FROM feedback")
            total = cursor.fetchone()[0]
            
            # Feedbacks não processados
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE processed = 0")
            unprocessed = cursor.fetchone()[0]
            
            # Por tipo
            cursor.execute("""
                SELECT feedback_type, COUNT(*) as count
                FROM feedback
                GROUP BY feedback_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Por banco correto
            cursor.execute("""
                SELECT correct_bank, COUNT(*) as count
                FROM feedback
                WHERE correct_bank IS NOT NULL
                GROUP BY correct_bank
                ORDER BY count DESC
                LIMIT 10
            """)
            by_bank = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "total_feedback": total,
                "unprocessed": unprocessed,
                "processed": total - unprocessed,
                "by_type": by_type,
                "top_banks": by_bank
            }
            
        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}")
            return {}
    
    def export_training_data(self, output_path: str) -> bool:
        """
        Exporta feedbacks para arquivo JSON (para treinar ML).
        
        Args:
            output_path: Caminho para arquivo JSON de saída
            
        Returns:
            True se sucesso
        """
        try:
            feedbacks = self.get_unprocessed_feedback(limit=10000)
            
            training_data = []
            for fb in feedbacks:
                if fb['correct_bank']:  # Só inclui se tem banco correto
                    training_data.append({
                        "text": fb['document_text'],
                        "correct_bank": fb['correct_bank'],
                        "detected_bank": fb['detected_bank'],
                        "confidence": fb['detection_confidence']
                    })
            
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(training_data)} training samples to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export training data: {e}")
            return False
    
    def get_problematic_cases(self, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """
        Retorna casos problemáticos (baixa confiança + feedback negativo).
        
        Args:
            min_confidence: Confiança mínima para considerar problema
            
        Returns:
            Lista de casos problemáticos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM feedback 
                WHERE detection_confidence < ?
                AND detected_bank != correct_bank
                ORDER BY detection_confidence ASC
                LIMIT 50
            """, (min_confidence,))
            
            cases = []
            for row in cursor.fetchall():
                case = dict(row)
                if case['extracted_data']:
                    case['extracted_data'] = json.loads(case['extracted_data'])
                if case['correct_data']:
                    case['correct_data'] = json.loads(case['correct_data'])
                cases.append(case)
            
            conn.close()
            return cases
            
        except Exception as e:
            logger.error(f"Failed to get problematic cases: {e}")
            return []
