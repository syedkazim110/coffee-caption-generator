"""
Anthropic provider implementation.
Handles Anthropic Claude model interactions.
"""
from typing import Dict, Any, Optional
import requests
import logging
import os
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """Provider for Anthropic Claude models"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize Anthropic provider"""
        super().__init__(model_config)
        
        # Get API key from environment
        api_key_env = model_config.get('api_key_env')
        self.api_key = os.getenv(api_key_env) if api_key_env else None
        
        if not self.api_key:
            logger.warning(f"Anthropic API key not found in environment variable: {api_key_env}")
        
        self.api_url = f"{self.api_endpoint}/messages"
        self.anthropic_version = "2023-06-01"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Anthropic Claude
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            raise Exception("Anthropic API key not configured. Set ANTHROPIC_API_KEY in environment.")
        
        try:
            # Merge parameters
            params = self.validate_parameters(kwargs)
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": params.get('max_tokens', 250),
                "temperature": params.get('temperature', 0.7),
                "top_p": params.get('top_p', 0.9)
            }
            
            # Add stop sequences if provided
            if 'stop' in kwargs and kwargs['stop']:
                payload['stop_sequences'] = kwargs['stop']
            
            logger.info(f"Generating with Anthropic model: {self.model_name}")
            
            # Make request to Anthropic
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
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
                generated_text = result['content'][0]['text'].strip()
                logger.info(f"Successfully generated {len(generated_text)} characters")
                return generated_text
            else:
                error_msg = f"Anthropic API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Anthropic request timeout"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Anthropic API"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error generating with Anthropic: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Anthropic connection and API key validity
        
        Returns:
            Connection status and details
        """
        if not self.api_key:
            return {
                'status': 'error',
                'available': False,
                'message': 'Anthropic API key not configured',
                'suggestion': 'Set ANTHROPIC_API_KEY in your .env file'
            }
        
        try:
            # Test with a minimal request
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
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
                    'message': f'Anthropic API is accessible with {self.model_name}'
                }
            elif response.status_code == 401:
                return {
                    'status': 'error',
                    'available': False,
                    'message': 'Invalid Anthropic API key',
                    'suggestion': 'Check your ANTHROPIC_API_KEY in .env'
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
                    'message': f'Anthropic API error: {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'disconnected',
                'available': False,
                'message': 'Cannot connect to Anthropic API',
                'suggestion': 'Check your internet connection'
            }
        except Exception as e:
            return {
                'status': 'error',
                'available': False,
                'message': f'Error testing Anthropic: {str(e)}'
            }
