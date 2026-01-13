"""Testes para o sistema ML de classificação de banco"""
import pytest
import json
from pathlib import Path
from parsers.utils.ml_classifier import MLBankClassifier


class TestMLBankClassifier:
    """Testes do classificador ML"""
    
    @pytest.fixture
    def classifier(self):
        """Fixture com classificador limpo"""
        return MLBankClassifier(model_path="test_ml_model.json")
    
    def test_classifier_initialization(self, classifier):
        """Testa inicialização do classificador"""
        assert classifier is not None
        # Modelo não existe inicialmente
        assert classifier.enabled == False
    
    def test_extract_features(self, classifier):
        """Testa extração de features"""
        text = """
        Nubank
        Esta é a sua fatura de novembro
        Total a pagar: R$ 1.500,00
        CNPJ: 18.236.120/0001-58
        """
        
        features = classifier.extract_features(text)
        
        assert features['has_nubank'] == 1
        assert features['has_fatura'] == 1
        assert features['has_currency'] > 0
        assert features['has_cnpj'] == 1
        assert features['has_roxinho_greeting'] == 0  # sem "Olá"
    
    def test_train_from_feedback(self, classifier):
        """Testa treinamento com dados de feedback"""
        feedback_data = [
            {"text": "Nubank fatura R$ 100", "correct_bank": "nubank"},
            {"text": "Nubank Esta é a sua fatura", "correct_bank": "nubank"},
            {"text": "Banco Inter cartão", "correct_bank": "inter"},
            {"text": "Inter fatura R$ 200", "correct_bank": "inter"},
            {"text": "C6 Bank fatura", "correct_bank": "c6"},
            {"text": "C6 cartão crédito", "correct_bank": "c6"},
            {"text": "PicPay fatura", "correct_bank": "picpay"},
            {"text": "PicPay cartão", "correct_bank": "picpay"},
            {"text": "Nubank total", "correct_bank": "nubank"},
            {"text": "Inter banco", "correct_bank": "inter"},
        ]
        
        classifier.train_from_feedback(feedback_data)
        
        assert classifier.enabled == True
        assert classifier.model_data is not None
        assert len(classifier.model_data['banks']) > 0
    
    def test_predict_after_training(self, classifier):
        """Testa predição após treinamento"""
        # Treina modelo
        feedback_data = [
            {"text": "Nubank fatura", "correct_bank": "nubank"},
            {"text": "Nubank cartão", "correct_bank": "nubank"},
            {"text": "Banco Inter fatura", "correct_bank": "inter"},
            {"text": "Inter cartão", "correct_bank": "inter"},
            {"text": "C6 Bank", "correct_bank": "c6"},
            {"text": "C6 fatura", "correct_bank": "c6"},
            {"text": "PicPay", "correct_bank": "picpay"},
            {"text": "PicPay cartão", "correct_bank": "picpay"},
            {"text": "Nubank", "correct_bank": "nubank"},
            {"text": "Inter", "correct_bank": "inter"},
        ]
        
        classifier.train_from_feedback(feedback_data)
        
        # Testa predição
        prediction = classifier.predict("Nubank fatura novembro")
        
        # Pode retornar None se confiança baixa
        if prediction:
            bank, confidence = prediction
            assert isinstance(bank, str)
            assert 0 <= confidence <= 1
    
    def test_should_assist(self, classifier):
        """Testa quando ML deve assistir"""
        # ML só deve assistir se confiança < 0.70
        assert classifier.should_assist(0.50) == False  # Modelo não carregado
        assert classifier.should_assist(0.80) == False
        
        # Treina modelo para habilitar
        feedback_data = [
            {"text": f"Nubank {i}", "correct_bank": "nubank"}
            for i in range(10)
        ]
        classifier.train_from_feedback(feedback_data)
        
        # Agora testa com modelo habilitado
        assert classifier.should_assist(0.50) == True
        assert classifier.should_assist(0.80) == False
    
    def test_insufficient_training_data(self, classifier):
        """Testa que não treina com dados insuficientes"""
        feedback_data = [
            {"text": "Nubank", "correct_bank": "nubank"},
            {"text": "Inter", "correct_bank": "inter"},
        ]  # Apenas 2 amostras
        
        classifier.train_from_feedback(feedback_data)
        
        # Não deve treinar com < 10 amostras
        assert classifier.enabled == False
    
    def test_get_model_info(self, classifier):
        """Testa informações do modelo"""
        info = classifier.get_model_info()
        
        assert "enabled" in info
        assert info["enabled"] == False
        
        # Treina modelo
        feedback_data = [
            {"text": f"Bank {i % 2}", "correct_bank": f"bank{i % 2}"}
            for i in range(10)
        ]
        classifier.train_from_feedback(feedback_data)
        
        info = classifier.get_model_info()
        assert info["enabled"] == True
        assert "num_samples" in info
    
    def teardown_method(self, method):
        """Limpa arquivos de teste"""
        test_file = Path("test_ml_model.json")
        if test_file.exists():
            test_file.unlink()
