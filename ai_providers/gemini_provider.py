"""
Google Gemini provider implementation.
Handles Google Gemini model interactions.
"""
from typing import Dict, Any, Optional
import requests
import logging
import os
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Provider for Google Gemini models"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize Gemini provider"""
        super().__init__(model_config)
        
        # Get API key from config first, then fall back to environment
        self.api_key = model_config.get('api_key')
        
        if not self.api_key:
            # Fall back to environment variable
            api_key_env = model_config.get('api_key_env')
            self.api_key = os.getenv(api_key_env) if api_key_env else None
            
            if not self.api_key:
                logger.warning(f"Gemini API key not found in config or environment variable: {api_key_env}")
        else:
            logger.info(f"Gemini API key loaded from config")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Google Gemini
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            raise Exception("Gemini API key not configured. Set GEMINI_API_KEY in environment.")
        
        try:
            # Merge parameters
            params = self.validate_parameters(kwargs)
            
            # Construct API URL with model and key
            api_url = f"{self.api_endpoint}/models/{self.model_name}:generateContent?key={self.api_key}"
            
            # Prepare request payload
            # Use max_tokens if provided (from AI Service), otherwise use max_output_tokens or default
            max_tokens = kwargs.get('max_tokens', params.get('max_output_tokens', 800))
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": params.get('temperature', 0.7),
                    "maxOutputTokens": max_tokens,
                    "topP": params.get('top_p', 0.9),
                    "thinkingConfig": {
                        "thinkingBudget": 0  # Disable thinking to prevent token consumption
                    }
                }
            }
            
            # Add stop sequences if provided
            if 'stop' in kwargs and kwargs['stop']:
                payload['generationConfig']['stopSequences'] = kwargs['stop']
            
            logger.info(f"Generating with Gemini model: {self.model_name}")
            
            # Make request to Gemini
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Log the actual response structure for debugging
                logger.info(f"Gemini response keys: {result.keys()}")
                
                # Extract text from Gemini response structure
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    logger.info(f"Candidate keys: {candidate.keys()}")
                    
                    # Check for finish reason
                    finish_reason = candidate.get('finishReason', 'UNKNOWN')
                    
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if parts and len(parts) > 0 and 'text' in parts[0]:
                            generated_text = parts[0]['text'].strip()
                            logger.info(f"Successfully generated {len(generated_text)} characters (finishReason: {finish_reason})")
                            return generated_text
                    
                    # Check if hit token limit without generating text
                    if finish_reason == 'MAX_TOKENS':
                        # Gemini 2.5 Flash may use "thinking" tokens, leaving no room for output
                        logger.warning(f"Hit MAX_TOKENS with no text output. Increase maxOutputTokens (current: {max_tokens})")
                        raise Exception(f"Gemini hit MAX_TOKENS limit without generating text. Try increasing token limit from {max_tokens}.")
                    
                    # Alternative structure: check if text is directly in candidate
                    if 'text' in candidate:
                        generated_text = candidate['text'].strip()
                        logger.info(f"Successfully generated {len(generated_text)} characters (alternative structure)")
                        return generated_text
                
                # Log the full response for debugging
                logger.error(f"Unexpected Gemini response structure. Full response: {result}")
                raise Exception(f"Unexpected Gemini response structure. Response: {result}")
            else:
                error_msg = f"Gemini API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Gemini request timeout"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Gemini API"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Gemini connection and API key validity
        
        Returns:
            Connection status and details
        """
        if not self.api_key:
            return {
                'status': 'error',
                'available': False,
                'message': 'Gemini API key not configured',
                'suggestion': 'Set GEMINI_API_KEY in your .env file'
            }
        
        try:
            # Test with a minimal request
            api_url = f"{self.api_endpoint}/models/{self.model_name}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": "Hi"
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 5
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'available': True,
                    'message': f'Gemini API is accessible with {self.model_name}'
                }
            elif response.status_code == 400:
                # Check if it's an API key issue
                error_text = response.text.lower()
                if 'api key' in error_text or 'invalid' in error_text:
                    return {
                        'status': 'error',
                        'available': False,
                        'message': 'Invalid Gemini API key',
                        'suggestion': 'Check your GEMINI_API_KEY in .env'
                    }
                else:
                    return {
                        'status': 'error',
                        'available': False,
                        'message': f'Gemini API error: {response.text}'
                    }
            elif response.status_code == 404:
                return {
                    'status': 'error',
                    'available': False,
                    'message': f'Model {self.model_name} not found',
                    'suggestion': 'Check if you have access to this model'
                }
            else:
                return {
                    'status': 'error',
                    'available': False,
                    'message': f'Gemini API error: {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'disconnected',
                'available': False,
                'message': 'Cannot connect to Gemini API',
                'suggestion': 'Check your internet connection'
            }
        except Exception as e:
            return {
                'status': 'error',
                'available': False,
                'message': f'Error testing Gemini: {str(e)}'
            }
