"""
Ollama provider implementation.
Handles local Ollama model interactions.
"""
from typing import Dict, Any, Optional
import requests
import logging
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Provider for Ollama local models"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize Ollama provider"""
        super().__init__(model_config)
        self.api_url = f"{self.api_endpoint}/api/generate"
        self.tags_url = f"{self.api_endpoint}/api/tags"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        try:
            # Merge parameters
            params = self.validate_parameters(kwargs)
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": params.get('temperature', 0.7),
                    "top_p": params.get('top_p', 0.9),
                    "num_predict": params.get('num_predict', 250),
                    "num_ctx": params.get('num_ctx', 2048),
                    "repeat_penalty": params.get('repeat_penalty', 1.1),
                    "stop": kwargs.get('stop', [])
                }
            }
            
            logger.info(f"Generating with Ollama model: {self.model_name}")
            
            # Make request to Ollama
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                logger.info(f"Successfully generated {len(generated_text)} characters")
                return generated_text
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Ollama request timeout"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama. Is it running?"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Ollama connection and model availability
        
        Returns:
            Connection status and details
        """
        try:
            # Check if Ollama is running
            response = requests.get(self.tags_url, timeout=5)
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                # Check if our specific model is available
                model_available = any(
                    self.model_name in model_name 
                    for model_name in available_models
                )
                
                if model_available:
                    return {
                        'status': 'connected',
                        'available': True,
                        'message': f'Ollama is running with {self.model_name}',
                        'available_models': available_models,
                        'latency_ms': None
                    }
                else:
                    return {
                        'status': 'connected',
                        'available': False,
                        'message': f'Ollama is running but {self.model_name} not found',
                        'available_models': available_models,
                        'suggestion': f'Run: ollama pull {self.model_name}'
                    }
            else:
                return {
                    'status': 'error',
                    'available': False,
                    'message': f'Ollama returned status {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'disconnected',
                'available': False,
                'message': 'Cannot connect to Ollama. Is it running?',
                'suggestion': 'Install Ollama from https://ollama.ai'
            }
        except Exception as e:
            return {
                'status': 'error',
                'available': False,
                'message': f'Error testing Ollama: {str(e)}'
            }
    
    def list_available_models(self) -> list:
        """
        List all models available in Ollama
        
        Returns:
            List of available model names
        """
        try:
            response = requests.get(self.tags_url, timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []
