"""
Classificador ML para auxiliar detecção de banco.

IMPORTANTE: Este classificador é um ASSISTENTE, não um substituto.
- Usado apenas quando BankDetector tem confiança < 70%
- Não substitui parsers especializados
- Serve para casos ambíguos ou novos bancos
"""
import re
import json
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MLBankClassifier:
    """
    Classificador ML leve para auxiliar detecção de banco.
    
    Usa abordagem baseada em features + scoring (não requer sklearn em produção).
    Modelo é treinado offline e carregado como JSON.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicializa o classificador.
        
        Args:
            model_path: Caminho para arquivo JSON do modelo treinado
        """
        self.model_path = model_path or "parsers/utils/ml_model.json"
        self.model_data = None
        self.enabled = False
        
        # Tenta carregar modelo se existir
        self._load_model()
    
    def _load_model(self):
        """Carrega modelo do disco"""
        try:
            path = Path(self.model_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.model_data = json.load(f)
                self.enabled = True
                logger.info(f"ML model loaded from {self.model_path}")
            else:
                logger.info(f"ML model not found at {self.model_path}, classifier disabled")
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")
            self.enabled = False
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        Extrai features do texto para classificação.
        
        Args:
            text: Texto do documento
            
        Returns:
            Dict com features extraídas
        """
        text_lower = text.lower()
        
        features = {
            # Tamanho do documento
            "doc_length": len(text),
            "num_lines": len(text.split('\n')),
            
            # Keywords de bancos
            "has_nubank": int('nubank' in text_lower),
            "has_inter": int('inter' in text_lower),
            "has_c6": int('c6' in text_lower or 'c6 bank' in text_lower),
            "has_picpay": int('picpay' in text_lower),
            "has_itau": int('itaú' in text_lower or 'itau' in text_lower),
            "has_bradesco": int('bradesco' in text_lower),
            
            # Padrões de layout
            "has_fatura": int('fatura' in text_lower),
            "has_cartao": int('cartão' in text_lower or 'cartao' in text_lower),
            "has_total_pagar": int('total a pagar' in text_lower or 'total:' in text_lower),
            
            # Formato de valores
            "has_currency": len(re.findall(r'R\$', text)),
            "num_values": len(re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', text)),
            
            # Datas
            "num_dates": len(re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)),
            
            # CNPJs
            "has_cnpj": int(bool(re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text))),
            
            # Padrões específicos
            "has_roxinho_greeting": int('olá' in text_lower and 'esta é a sua fatura' in text_lower),
            "has_inter_layout": int('banco inter' in text_lower),
        }
        
        return features
    
    def predict(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Prediz o banco usando ML (apenas se modelo carregado).
        
        Args:
            text: Texto do documento
            
        Returns:
            Tupla (banco, confiança) ou None se não conseguir prever
        """
        if not self.enabled or not self.model_data:
            return None
        
        features = self.extract_features(text)
        
        # Usa modelo de scoring simples (pode ser substituído por sklearn offline)
        scores = {}
        
        for bank, bank_weights in self.model_data.get('weights', {}).items():
            score = 0.0
            for feature, value in features.items():
                weight = bank_weights.get(feature, 0.0)
                score += value * weight
            
            scores[bank] = score
        
        if not scores:
            return None
        
        # Pega banco com maior score
        best_bank = max(scores, key=scores.get)
        max_score = scores[best_bank]
        
        # Normaliza score para confiança (0-1)
        # Usa sigmoid-like normalization
        confidence = 1 / (1 + pow(2.718, -max_score))
        
        # Só retorna se confiança mínima
        if confidence < 0.5:
            return None
        
        return (best_bank, confidence)
    
    def should_assist(self, rule_confidence: float) -> bool:
        """
        Determina se o classificador ML deve assistir.
        
        Args:
            rule_confidence: Confiança do BankDetector baseado em regras
            
        Returns:
            True se ML deve ser consultado
        """
        # ML só atua quando regras têm baixa confiança
        return rule_confidence < 0.70 and self.enabled
    
    def train_from_feedback(self, feedback_data: List[Dict[str, Any]]):
        """
        Retreina modelo baseado em feedback dos usuários.
        
        Args:
            feedback_data: Lista de feedbacks com texto e banco correto
        """
        if not feedback_data:
            logger.warning("No feedback data to train")
            return
        
        # Extrai features de todos os feedbacks
        X = []
        y = []
        
        for feedback in feedback_data:
            text = feedback.get('text', '')
            correct_bank = feedback.get('correct_bank')
            
            if text and correct_bank:
                features = self.extract_features(text)
                X.append(features)
                y.append(correct_bank)
        
        if len(X) < 10:
            logger.warning(f"Not enough training data ({len(X)} samples), minimum 10 required")
            return
        
        # Treina modelo simples baseado em pesos
        # Para cada banco, calcula peso médio de cada feature
        banks = list(set(y))
        weights = {}
        
        for bank in banks:
            bank_indices = [i for i, label in enumerate(y) if label == bank]
            bank_features = [X[i] for i in bank_indices]
            
            # Calcula média de cada feature para este banco
            avg_features = {}
            feature_names = X[0].keys()
            
            for feature in feature_names:
                values = [f[feature] for f in bank_features]
                avg_features[feature] = sum(values) / len(values) if values else 0.0
            
            weights[bank] = avg_features
        
        # Salva modelo
        self.model_data = {
            "version": "1.0",
            "trained_at": "manual_training",
            "num_samples": len(X),
            "banks": banks,
            "weights": weights
        }
        
        self._save_model()
        logger.info(f"Model trained with {len(X)} samples for banks: {banks}")
    
    def _save_model(self):
        """Salva modelo no disco"""
        try:
            path = Path(self.model_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.model_data, f, indent=2, ensure_ascii=False)
            
            self.enabled = True
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo"""
        if not self.enabled or not self.model_data:
            return {
                "enabled": False,
                "message": "Model not loaded"
            }
        
        return {
            "enabled": True,
            "version": self.model_data.get("version"),
            "num_samples": self.model_data.get("num_samples"),
            "banks": self.model_data.get("banks", []),
            "trained_at": self.model_data.get("trained_at")
        }
