"""
OpenAI provider implementation.
Handles OpenAI GPT model interactions.
"""
from typing import Dict, Any, Optional
import requests
import logging
import os
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """Provider for OpenAI models (GPT-4, GPT-3.5, etc.)"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize OpenAI provider"""
        super().__init__(model_config)
        
        # Get API key from environment
        api_key_env = model_config.get('api_key_env')
        self.api_key = os.getenv(api_key_env) if api_key_env else None
        
        if not self.api_key:
            logger.warning(f"OpenAI API key not found in environment variable: {api_key_env}")
        
        self.api_url = f"{self.api_endpoint}/chat/completions"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            raise Exception("OpenAI API key not configured. Set OPENAI_API_KEY in environment.")
        
        try:
            # Merge parameters
            params = self.validate_parameters(kwargs)
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": params.get('temperature', 0.7),
                "max_tokens": params.get('max_tokens', 250),
                "top_p": params.get('top_p', 0.9)
            }
            
            # Add stop sequences if provided
            if 'stop' in kwargs:
                payload['stop'] = kwargs['stop']
            
            logger.info(f"Generating with OpenAI model: {self.model_name}")
            
            # Make request to OpenAI
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['message']['content'].strip()
                logger.info(f"Successfully generated {len(generated_text)} characters")
                return generated_text
            else:
                error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "OpenAI request timeout"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to OpenAI API"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test OpenAI connection and API key validity
        
        Returns:
            Connection status and details
        """
        if not self.api_key:
            return {
                'status': 'error',
                'available': False,
                'message': 'OpenAI API key not configured',
                'suggestion': 'Set OPENAI_API_KEY in your .env file'
            }
        
        try:
            # Test with a minimal request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'available': True,
                    'message': f'OpenAI API is accessible with {self.model_name}'
                }
            elif response.status_code == 401:
                return {
                    'status': 'error',
                    'available': False,
                    'message': 'Invalid OpenAI API key',
                    'suggestion': 'Check your OPENAI_API_KEY in .env'
                }
            elif response.status_code == 404:
                return {
                    'status': 'error',
                    'available': False,
                    'message': f'Model {self.model_name} not found or not accessible',
                    'suggestion': 'Check if you have access to this model'
                }
            else:
                return {
                    'status': 'error',
                    'available': False,
                    'message': f'OpenAI API error: {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'disconnected',
                'available': False,
                'message': 'Cannot connect to OpenAI API',
                'suggestion': 'Check your internet connection'
            }
        except Exception as e:
            return {
                'status': 'error',
                'available': False,
                'message': f'Error testing OpenAI: {str(e)}'
            }
