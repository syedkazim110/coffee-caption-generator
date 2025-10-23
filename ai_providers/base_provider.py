"""
Base class for AI model providers.
All provider implementations must inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Abstract base class for AI model providers"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the AI provider
        
        Args:
            model_config: Configuration dictionary for the model
        """
        self.model_config = model_config
        self.provider_name = model_config.get('provider')
        self.model_name = model_config.get('model_name')
        self.display_name = model_config.get('display_name')
        self.api_endpoint = model_config.get('api_endpoint')
        self.parameters = model_config.get('parameters', {})
        self.capabilities = model_config.get('capabilities', {})
        self.is_local = model_config.get('is_local', False)
        
        logger.info(f"Initialized {self.provider_name} provider with model: {self.model_name}")
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the AI model
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for generation
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test if the provider is accessible and working
        
        Returns:
            Dictionary with connection status and details
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model
        
        Returns:
            Dictionary with model information
        """
        return {
            'provider': self.provider_name,
            'model_name': self.model_name,
            'display_name': self.display_name,
            'capabilities': self.capabilities,
            'is_local': self.is_local
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and merge parameters with defaults
        
        Args:
            params: Parameters to validate
            
        Returns:
            Validated parameters merged with defaults
        """
        # Start with default parameters
        validated = self.parameters.copy()
        
        # Override with provided parameters
        if params:
            validated.update(params)
        
        return validated
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate the cost of a generation
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        cost_per_1m = self.capabilities.get('cost_per_1m_tokens', 0.0)
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1_000_000) * cost_per_1m
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self.provider_name})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.model_name}>"
