"""Testes para o sistema de templates comunitários"""
import pytest
from pathlib import Path
import shutil
from parsers.utils.community_templates import CommunityTemplateSystem


class TestCommunityTemplateSystem:
    """Testes do sistema de templates comunitários"""
    
    @pytest.fixture
    def template_system(self):
        """Fixture com sistema de templates de teste"""
        templates_dir = "test_community_templates"
        ts = CommunityTemplateSystem(templates_dir=templates_dir)
        yield ts
        # Cleanup
        if Path(templates_dir).exists():
            shutil.rmtree(templates_dir)
    
    def test_initialization(self, template_system):
        """Testa inicialização do sistema"""
        assert Path(template_system.templates_dir).exists()
        assert isinstance(template_system.approved_templates, dict)
    
    def test_submit_valid_template(self, template_system):
        """Testa submissão de template válido"""
        result = template_system.submit_template(
            bank_key="santander",
            bank_name="Banco Santander",
            cnpj="90.400.888/0001-42",
            detection_patterns=[
                r'santander',
                r'banco santander'
            ],
            extraction_patterns={
                'valor_total': r'total[:\s]*R?\$?\s*([\d.,]+)',
                'data_vencimento': r'vencimento[:\s]*(\d{2}/\d{2}/\d{4})'
            },
            author="test@example.com",
            description="Template para Santander"
        )
        
        assert result['success'] == True
        assert result['status'] == 'pending'
        assert 'template_id' in result
    
    def test_submit_invalid_bank_key(self, template_system):
        """Testa rejeição de bank_key inválido"""
        result = template_system.submit_template(
            bank_key="INVALID-KEY!",  # Caracteres não permitidos
            bank_name="Test Bank",
            cnpj="12.345.678/0001-90",
            detection_patterns=["test"],
            extraction_patterns={},
            author="test@example.com"
        )
        
        assert result['success'] == False
        assert 'error' in result
    
    def test_submit_invalid_cnpj(self, template_system):
        """Testa rejeição de CNPJ inválido"""
        result = template_system.submit_template(
            bank_key="testbank",
            bank_name="Test Bank",
            cnpj="invalid-cnpj",
            detection_patterns=["test"],
            extraction_patterns={},
            author="test@example.com"
        )
        
        assert result['success'] == False
        assert 'CNPJ' in result['error']
    
    def test_submit_invalid_regex(self, template_system):
        """Testa rejeição de regex inválido"""
        result = template_system.submit_template(
            bank_key="testbank",
            bank_name="Test Bank",
            cnpj="12.345.678/0001-90",
            detection_patterns=["[invalid(regex"],  # Regex mal formado
            extraction_patterns={},
            author="test@example.com"
        )
        
        assert result['success'] == False
        assert 'regex' in result['error'].lower()
    
    def test_submit_dangerous_pattern(self, template_system):
        """Testa rejeição de padrão perigoso"""
        result = template_system.submit_template(
            bank_key="testbank",
            bank_name="Test Bank",
            cnpj="12.345.678/0001-90",
            detection_patterns=["exec('malicious code')"],  # Perigoso
            extraction_patterns={},
            author="test@example.com"
        )
        
        assert result['success'] == False
        assert 'dangerous' in result['error'].lower()
    
    def test_submit_invalid_field(self, template_system):
        """Testa rejeição de campo desconhecido"""
        result = template_system.submit_template(
            bank_key="testbank",
            bank_name="Test Bank",
            cnpj="12.345.678/0001-90",
            detection_patterns=["test"],
            extraction_patterns={
                'unknown_field': r'pattern'  # Campo não permitido
            },
            author="test@example.com"
        )
        
        assert result['success'] == False
        assert 'Unknown field' in result['error']
    
    def test_approve_template(self, template_system):
        """Testa aprovação de template"""
        # Submete template
        result = template_system.submit_template(
            bank_key="bradesco",
            bank_name="Banco Bradesco",
            cnpj="60.746.948/0001-12",
            detection_patterns=["bradesco"],
            extraction_patterns={
                'valor_total': r'total[:\s]*R?\$?\s*([\d.,]+)'
            },
            author="test@example.com"
        )
        
        template_hash = result['template_id']
        
        # Aprova template
        success = template_system.approve_template(template_hash, "admin@example.com")
        
        assert success == True
        
        # Verifica que foi aprovado
        template = template_system.get_template("bradesco")
        assert template is not None
        assert template['status'] == 'approved'
    
    def test_list_approved_templates(self, template_system):
        """Testa listagem de templates aprovados"""
        # Submete e aprova template
        result = template_system.submit_template(
            bank_key="itau",
            bank_name="Itaú Unibanco",
            cnpj="60.701.190/0001-04",
            detection_patterns=["itau"],
            extraction_patterns={},
            author="test@example.com"
        )
        
        if not result['success']:
            print(f"Submit failed: {result.get('error')}")
        assert result['success'] is True
        template_system.approve_template(result['template_id'], "admin")
        
        # Lista aprovados
        approved = template_system.list_approved_templates()
        
        assert len(approved) == 1
        assert approved[0]['bank_key'] == 'itau'
    
    def test_list_pending_templates(self, template_system):
        """Testa listagem de templates pendentes"""
        # Submete template (não aprovado)
        result = template_system.submit_template(
            bank_key="caixa",
            bank_name="Caixa Econômica Federal",
            cnpj="00.360.305/0001-04",
            detection_patterns=["caixa"],
            extraction_patterns={},
            author="test@example.com"
        )
        
        assert result['success'] is True
        
        # Lista pendentes
        pending = template_system.list_pending_templates()
        
        assert len(pending) == 1
        assert pending[0]['bank_key'] == 'caixa'
    
    def test_apply_template(self, template_system):
        """Testa aplicação de template aprovado"""
        # Submete e aprova template
        result = template_system.submit_template(
            bank_key="bb",
            bank_name="Banco do Brasil",
            cnpj="00.000.000/0001-91",
            detection_patterns=["banco do brasil"],
            extraction_patterns={
                'valor_total': r'total[:\s]*R?\$?\s*([\d.,]+)'
            },
            author="test@example.com"
        )
        
        template_system.approve_template(result['template_id'], "admin")
        
        # Aplica template
        text = "Banco do Brasil\nTotal: R$ 1.500,00"
        extracted = template_system.apply_template("bb", text)
        
        assert extracted is not None
        assert extracted['empresa'] == 'Banco do Brasil'
        assert extracted['cnpj'] == '00.000.000/0001-91'
        assert 'valor_total' in extracted
