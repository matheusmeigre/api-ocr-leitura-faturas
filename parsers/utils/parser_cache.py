"""Sistema de cache para detecção de banco e parser"""
import hashlib
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta


class ParserCache:
    """
    Cache em memória para detecção de banco e seleção de parser.
    
    Motivação:
    - Detecção de banco é determinística
    - OCR + parsing é custoso
    - Cache reduz latência e custo computacional
    
    Características:
    - Transparente ao fluxo
    - Opcional e desativável
    - TTL configurável
    - Thread-safe (para uso futuro)
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000, enabled: bool = True):
        """
        Inicializa o cache.
        
        Args:
            ttl_seconds: Tempo de vida das entradas (padrão: 1 hora)
            max_size: Tamanho máximo do cache
            enabled: Se o cache está ativo
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.enabled = enabled
        
        # Cache: hash -> (resultado, timestamp)
        self._bank_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._parser_cache: Dict[str, Tuple[str, datetime]] = {}
        
        # Estatísticas
        self.hits = 0
        self.misses = 0
    
    def _generate_hash(self, text: str) -> str:
        """
        Gera hash SHA256 de texto normalizado.
        
        Args:
            text: Texto do documento
            
        Returns:
            Hash SHA256 em hexadecimal
        """
        # Normaliza texto (remove espaços extras, lowercase)
        normalized = ' '.join(text.lower().split())
        
        # Usa primeiros 500 caracteres para performance
        # (geralmente suficiente para identificar banco)
        sample = normalized[:500]
        
        return hashlib.sha256(sample.encode('utf-8')).hexdigest()
    
    def _is_expired(self, timestamp: datetime) -> bool:
        """Verifica se entrada expirou"""
        return datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds)
    
    def _evict_if_needed(self, cache_dict: Dict) -> None:
        """Remove entradas antigas se cache estiver cheio"""
        if len(cache_dict) >= self.max_size:
            # Remove 10% das entradas mais antigas
            to_remove = int(self.max_size * 0.1)
            sorted_items = sorted(cache_dict.items(), key=lambda x: x[1][1])
            for key, _ in sorted_items[:to_remove]:
                del cache_dict[key]
    
    def get_bank_detection(self, text: str) -> Optional[Tuple]:
        """
        Busca detecção de banco no cache.
        
        Args:
            text: Texto do documento
            
        Returns:
            Tuple (bank_key, bank_name, confidence) ou None
        """
        if not self.enabled:
            return None
        
        text_hash = self._generate_hash(text)
        
        if text_hash in self._bank_cache:
            result, timestamp = self._bank_cache[text_hash]
            
            if not self._is_expired(timestamp):
                self.hits += 1
                return result
            else:
                # Remove entrada expirada
                del self._bank_cache[text_hash]
        
        self.misses += 1
        return None
    
    def set_bank_detection(self, text: str, result: Tuple) -> None:
        """
        Armazena detecção de banco no cache.
        
        Args:
            text: Texto do documento
            result: Tuple (bank_key, bank_name, confidence)
        """
        if not self.enabled:
            return
        
        text_hash = self._generate_hash(text)
        self._evict_if_needed(self._bank_cache)
        self._bank_cache[text_hash] = (result, datetime.now())
    
    def get_parser_choice(self, text: str) -> Optional[str]:
        """
        Busca escolha de parser no cache.
        
        Args:
            text: Texto do documento
            
        Returns:
            Nome do parser ou None
        """
        if not self.enabled:
            return None
        
        text_hash = self._generate_hash(text)
        
        if text_hash in self._parser_cache:
            parser_name, timestamp = self._parser_cache[text_hash]
            
            if not self._is_expired(timestamp):
                self.hits += 1
                return parser_name
            else:
                del self._parser_cache[text_hash]
        
        self.misses += 1
        return None
    
    def set_parser_choice(self, text: str, parser_name: str) -> None:
        """
        Armazena escolha de parser no cache.
        
        Args:
            text: Texto do documento
            parser_name: Nome do parser utilizado
        """
        if not self.enabled:
            return
        
        text_hash = self._generate_hash(text)
        self._evict_if_needed(self._parser_cache)
        self._parser_cache[text_hash] = (parser_name, datetime.now())
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        self._bank_cache.clear()
        self._parser_cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dict com estatísticas
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.2f}%",
            "bank_cache_size": len(self._bank_cache),
            "parser_cache_size": len(self._parser_cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }
