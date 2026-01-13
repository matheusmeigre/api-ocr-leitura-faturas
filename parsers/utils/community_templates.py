"""
Sistema de templates comunitários para novos bancos.

SEGURANÇA: Templates são apenas configurações JSON, NUNCA código executável.
"""
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)


class CommunityTemplateSystem:
    """
    Sistema de templates comunitários para novos bancos.
    
    Templates são apenas configurações declarativas (JSON):
    - Padrões de detecção (regex)
    - Padrões de extração (regex)
    - Mapeamento de campos
    
    NUNCA executa código arbitrário.
    """
    
    def __init__(self, templates_dir: str = "community_templates"):
        """
        Inicializa sistema de templates.
        
        Args:
            templates_dir: Diretório para armazenar templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache de templates aprovados
        self.approved_templates: Dict[str, Dict[str, Any]] = {}
        self._load_approved_templates()
    
    def _load_approved_templates(self):
        """Carrega templates aprovados do disco"""
        try:
            approved_dir = self.templates_dir / "approved"
            if not approved_dir.exists():
                return
            
            for template_file in approved_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                    
                    bank_key = template.get('bank_key')
                    if bank_key:
                        self.approved_templates[bank_key] = template
                        logger.info(f"Loaded approved template for {bank_key}")
                        
                except Exception as e:
                    logger.warning(f"Failed to load template {template_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load approved templates: {e}")
    
    def submit_template(
        self,
        bank_key: str,
        bank_name: str,
        cnpj: str,
        detection_patterns: List[str],
        extraction_patterns: Dict[str, str],
        author: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submete novo template para revisão.
        
        Args:
            bank_key: Identificador único do banco (ex: 'santander')
            bank_name: Nome completo do banco
            cnpj: CNPJ do banco
            detection_patterns: Lista de regex patterns para detectar banco
            extraction_patterns: Dict de regex patterns para extrair campos
            author: Nome/email do autor
            description: Descrição opcional do template
            
        Returns:
            Dict com resultado da submissão
        """
        # Validação de segurança
        validation = self._validate_template(
            bank_key, bank_name, cnpj,
            detection_patterns, extraction_patterns
        )
        
        if not validation['valid']:
            return {
                "success": False,
                "error": validation['error']
            }
        
        # Cria template
        template = {
            "version": "1.0",
            "bank_key": bank_key,
            "bank_name": bank_name,
            "cnpj": cnpj,
            "detection_patterns": detection_patterns,
            "extraction_patterns": extraction_patterns,
            "author": author,
            "description": description or "",
            "submitted_at": datetime.now().isoformat(),
            "status": "pending",
            "template_hash": self._generate_hash(bank_key, detection_patterns)
        }
        
        # Salva em diretório de pendentes
        pending_dir = self.templates_dir / "pending"
        pending_dir.mkdir(exist_ok=True)
        
        filename = f"{bank_key}_{template['template_hash'][:8]}.json"
        filepath = pending_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Template submitted: {bank_key} by {author}")
            
            return {
                "success": True,
                "template_id": template['template_hash'],
                "status": "pending",
                "message": f"Template submitted for review: {filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return {
                "success": False,
                "error": f"Failed to save template: {str(e)}"
            }
    
    def _validate_template(
        self,
        bank_key: str,
        bank_name: str,
        cnpj: str,
        detection_patterns: List[str],
        extraction_patterns: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Valida template para segurança e qualidade.
        
        Returns:
            Dict com valid=True/False e error se inválido
        """
        # Validação básica
        if not bank_key or not isinstance(bank_key, str):
            return {"valid": False, "error": "Invalid bank_key"}
        
        if not re.match(r'^[a-z0-9_]+$', bank_key):
            return {"valid": False, "error": "bank_key must be lowercase alphanumeric"}
        
        if not bank_name or not isinstance(bank_name, str):
            return {"valid": False, "error": "Invalid bank_name"}
        
        # Valida CNPJ
        if not cnpj or not re.match(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', cnpj):
            return {"valid": False, "error": "Invalid CNPJ format"}
        
        # Valida detection patterns
        if not detection_patterns or not isinstance(detection_patterns, list):
            return {"valid": False, "error": "detection_patterns must be a list"}
        
        for pattern in detection_patterns:
            if not isinstance(pattern, str):
                return {"valid": False, "error": "All detection patterns must be strings"}
            
            # Valida regex (segurança)
            try:
                re.compile(pattern)
            except re.error as e:
                return {"valid": False, "error": f"Invalid regex pattern: {e}"}
            
            # Proíbe patterns perigosos
            dangerous_keywords = ['exec', 'eval', 'import', '__', 'system', 'subprocess']
            if any(keyword in pattern.lower() for keyword in dangerous_keywords):
                return {"valid": False, "error": "Pattern contains dangerous keywords"}
        
        # Valida extraction patterns
        if not isinstance(extraction_patterns, dict):
            return {"valid": False, "error": "extraction_patterns must be a dict"}
        
        allowed_fields = [
            'empresa', 'cnpj', 'cpf', 'data_emissao', 'data_vencimento',
            'valor_total', 'numero_documento', 'items'
        ]
        
        for field, pattern in extraction_patterns.items():
            if field not in allowed_fields:
                return {"valid": False, "error": f"Unknown field: {field}"}
            
            if not isinstance(pattern, str):
                return {"valid": False, "error": f"Pattern for {field} must be string"}
            
            try:
                re.compile(pattern)
            except re.error as e:
                return {"valid": False, "error": f"Invalid regex for {field}: {e}"}
        
        return {"valid": True}
    
    def _generate_hash(self, bank_key: str, patterns: List[str]) -> str:
        """Gera hash único para template"""
        content = f"{bank_key}{''.join(patterns)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def approve_template(self, template_hash: str, reviewer: str) -> bool:
        """
        Aprova template pendente (requer privilégios de admin).
        
        Args:
            template_hash: Hash do template a aprovar
            reviewer: Nome do revisor
            
        Returns:
            True se aprovado com sucesso
        """
        try:
            pending_dir = self.templates_dir / "pending"
            
            # Busca template pendente
            template_file = None
            for f in pending_dir.glob("*.json"):
                with open(f, 'r', encoding='utf-8') as file:
                    template = json.load(file)
                    if template.get('template_hash') == template_hash:
                        template_file = f
                        break
            
            if not template_file:
                logger.warning(f"Template not found: {template_hash}")
                return False
            
            # Carrega template
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # Atualiza status
            template['status'] = 'approved'
            template['approved_at'] = datetime.now().isoformat()
            template['approved_by'] = reviewer
            
            # Move para diretório aprovado
            approved_dir = self.templates_dir / "approved"
            approved_dir.mkdir(exist_ok=True)
            
            bank_key = template['bank_key']
            approved_file = approved_dir / f"{bank_key}.json"
            
            with open(approved_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            # Remove do pendente
            template_file.unlink()
            
            # Adiciona ao cache
            self.approved_templates[bank_key] = template
            
            logger.info(f"Template approved: {bank_key} by {reviewer}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve template: {e}")
            return False
    
    def get_template(self, bank_key: str) -> Optional[Dict[str, Any]]:
        """
        Retorna template aprovado para um banco.
        
        Args:
            bank_key: Identificador do banco
            
        Returns:
            Template ou None se não encontrado
        """
        return self.approved_templates.get(bank_key)
    
    def list_approved_templates(self) -> List[Dict[str, Any]]:
        """
        Lista todos os templates aprovados.
        
        Returns:
            Lista de templates
        """
        return [
            {
                "bank_key": key,
                "bank_name": template.get('bank_name'),
                "author": template.get('author'),
                "approved_at": template.get('approved_at')
            }
            for key, template in self.approved_templates.items()
        ]
    
    def list_pending_templates(self) -> List[Dict[str, Any]]:
        """
        Lista templates pendentes de aprovação.
        
        Returns:
            Lista de templates pendentes
        """
        pending_dir = self.templates_dir / "pending"
        if not pending_dir.exists():
            return []
        
        pending = []
        for template_file in pending_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                
                pending.append({
                    "template_hash": template.get('template_hash'),
                    "bank_key": template.get('bank_key'),
                    "bank_name": template.get('bank_name'),
                    "author": template.get('author'),
                    "submitted_at": template.get('submitted_at'),
                    "filename": template_file.name
                })
            except Exception as e:
                logger.warning(f"Failed to load pending template {template_file}: {e}")
        
        return pending
    
    def apply_template(self, bank_key: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Aplica template comunitário para extrair dados.
        
        Args:
            bank_key: Identificador do banco
            text: Texto do documento
            
        Returns:
            Dados extraídos ou None se falhar
        """
        template = self.get_template(bank_key)
        if not template:
            return None
        
        try:
            extracted = {
                "empresa": template.get('bank_name'),
                "cnpj": template.get('cnpj')
            }
            
            # Aplica patterns de extração
            for field, pattern in template.get('extraction_patterns', {}).items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.groups() else match.group()
                    extracted[field] = value
            
            return extracted
            
        except Exception as e:
            logger.error(f"Failed to apply template {bank_key}: {e}")
            return None
