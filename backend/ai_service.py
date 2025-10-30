"""
Unified AI Service for managing multiple AI model providers.
Handles model selection, provider initialization, and fallback mechanisms.
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

from ai_providers import (
    BaseAIProvider,
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider
)

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}


class AIService:
    """
    Unified service for managing multiple AI model providers.
    Provides a single interface for text generation across different providers.
    """
    
    # Provider class mapping
    PROVIDER_CLASSES = {
        'ollama': OllamaProvider,
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'google': GeminiProvider
    }
    
    def __init__(self, config_path: str = 'ai_model_config.json'):
        """
        Initialize AI Service
        
        Args:
            config_path: Path to model configuration JSON file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.providers = {}  # Cache of initialized providers
        self.default_model_id = self.config.get('default_model', 'ollama_phi3')
        self.fallback_model_id = self.config.get('fallback_model', 'ollama_phi3')
        
        logger.info(f"AIService initialized with default model: {self.default_model_id}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration with {len(config.get('ai_models', {}))} models")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def get_provider(self, model_id: str) -> BaseAIProvider:
        """
        Get or create a provider instance for the specified model
        
        Args:
            model_id: Model identifier from configuration
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If model not found or provider not supported
        """
        # Check cache first
        if model_id in self.providers:
            return self.providers[model_id]
        
        # Get model config
        model_config = self.config.get('ai_models', {}).get(model_id)
        if not model_config:
            raise ValueError(f"Model '{model_id}' not found in configuration")
        
        # Get provider class
        provider_type = model_config.get('provider')
        provider_class = self.PROVIDER_CLASSES.get(provider_type)
        
        if not provider_class:
            raise ValueError(f"Provider '{provider_type}' not supported")
        
        # Create and cache provider
        try:
            provider = provider_class(model_config)
            self.providers[model_id] = provider
            logger.info(f"Initialized provider for model: {model_id}")
            return provider
        except Exception as e:
            logger.error(f"Error initializing provider for {model_id}: {e}")
            raise
    
    def generate(
        self, 
        prompt: str, 
        model_id: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using specified model or default
        
        Args:
            prompt: The input prompt
            model_id: Optional model identifier. Uses default if not specified
            use_fallback: Whether to use fallback model on failure
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary with generated text and metadata
        """
        # Use default model if not specified
        if not model_id:
            model_id = self.default_model_id
        
        try:
            # Get provider with API key from database
            provider = self.get_provider_with_api_key(model_id)
            generated_text = provider.generate(prompt, **kwargs)
            
            return {
                'text': generated_text,
                'model_id': model_id,
                'model_name': provider.model_name,
                'provider': provider.provider_name,
                'success': True,
                'fallback_used': False
            }
            
        except Exception as e:
            logger.error(f"Error generating with {model_id}: {e}")
            
            # Try fallback if enabled and different from current model
            if use_fallback and self.fallback_model_id != model_id:
                logger.info(f"Attempting fallback to {self.fallback_model_id}")
                try:
                    fallback_provider = self.get_provider(self.fallback_model_id)
                    generated_text = fallback_provider.generate(prompt, **kwargs)
                    
                    return {
                        'text': generated_text,
                        'model_id': self.fallback_model_id,
                        'model_name': fallback_provider.model_name,
                        'provider': fallback_provider.provider_name,
                        'success': True,
                        'fallback_used': True,
                        'original_error': str(e)
                    }
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise Exception(f"Both primary and fallback generation failed: {e}")
            else:
                raise
    
    def test_model(self, model_id: str) -> Dict[str, Any]:
        """
        Test if a model is accessible and working
        
        Args:
            model_id: Model identifier to test
            
        Returns:
            Dictionary with test results
        """
        try:
            # Check if model is local or requires API key
            model_config = self.config.get('ai_models', {}).get(model_id)
            if not model_config:
                return {
                    'model_id': model_id,
                    'status': 'error',
                    'available': False,
                    'message': f'Model {model_id} not found in configuration'
                }
            
            # For local models, use standard provider
            if model_config.get('is_local'):
                provider = self.get_provider(model_id)
            else:
                # For cloud models, try to get provider with database API key
                try:
                    provider = self.get_provider_with_api_key(model_id)
                except ValueError as e:
                    # No API key configured - return unavailable
                    return {
                        'model_id': model_id,
                        'status': 'error',
                        'available': False,
                        'message': 'API key not configured',
                        'suggestion': 'Configure API key in AI Model Settings'
                    }
            
            result = provider.test_connection()
            result['model_id'] = model_id
            return result
        except Exception as e:
            logger.error(f"Error testing model {model_id}: {e}")
            return {
                'model_id': model_id,
                'status': 'error',
                'available': False,
                'message': f'Error testing model: {str(e)}'
            }
    
    def list_models(self) -> Dict[str, Any]:
        """
        List all available models with their configurations
        
        Returns:
            Dictionary with model information
        """
        models = {}
        for model_id, model_config in self.config.get('ai_models', {}).items():
            models[model_id] = {
                'id': model_id,
                'display_name': model_config.get('display_name'),
                'description': model_config.get('description'),
                'provider': model_config.get('provider'),
                'capabilities': model_config.get('capabilities', {}),
                'is_local': model_config.get('is_local', False),
                'requires_setup': model_config.get('requires_setup', False),
                'status': model_config.get('status', 'available')
            }
        
        return {
            'default_model': self.default_model_id,
            'fallback_model': self.fallback_model_id,
            'models': models,
            'total': len(models)
        }
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model
        
        Args:
            model_id: Model identifier
            
        Returns:
            Detailed model information
        """
        model_config = self.config.get('ai_models', {}).get(model_id)
        if not model_config:
            raise ValueError(f"Model '{model_id}' not found")
        
        # Add provider information
        provider_type = model_config.get('provider')
        provider_info = self.config.get('provider_info', {}).get(provider_type, {})
        
        return {
            'id': model_id,
            'config': model_config,
            'provider_info': provider_info,
            'is_default': model_id == self.default_model_id,
            'is_fallback': model_id == self.fallback_model_id
        }
    
    def set_default_model(self, model_id: str) -> bool:
        """
        Set the default model for generation
        
        Args:
            model_id: Model identifier to set as default
            
        Returns:
            True if successful
        """
        if model_id not in self.config.get('ai_models', {}):
            raise ValueError(f"Model '{model_id}' not found")
        
        self.default_model_id = model_id
        logger.info(f"Default model changed to: {model_id}")
        return True
    
    def get_provider_summary(self) -> Dict[str, Any]:
        """
        Get summary of all providers and their status
        
        Returns:
            Provider status summary
        """
        summary = {}
        
        for provider_type, provider_info in self.config.get('provider_info', {}).items():
            # Count models for this provider
            model_count = sum(
                1 for m in self.config.get('ai_models', {}).values()
                if m.get('provider') == provider_type
            )
            
            summary[provider_type] = {
                'name': provider_info.get('name'),
                'description': provider_info.get('description'),
                'model_count': model_count,
                'requires_api_key': provider_info.get('requires_api_key', False),
                'cost_model': provider_info.get('cost_model', 'unknown')
            }
        
        return summary
    
    def estimate_cost(
        self, 
        input_text: str, 
        output_length: int = 250,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate the cost of a generation
        
        Args:
            input_text: Input prompt text
            output_length: Expected output length in tokens
            model_id: Model to estimate for (uses default if not specified)
            
        Returns:
            Cost estimation details
        """
        if not model_id:
            model_id = self.default_model_id
        
        # Rough estimation: 1 token ≈ 4 characters
        input_tokens = len(input_text) // 4
        output_tokens = output_length
        
        try:
            provider = self.get_provider(model_id)
            cost = provider.estimate_cost(input_tokens, output_tokens)
            
            return {
                'model_id': model_id,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'estimated_cost_usd': cost,
                'is_free': cost == 0.0
            }
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            return {
                'model_id': model_id,
                'error': str(e)
            }
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def save_api_key(self, model_id: str, api_key: str) -> Dict[str, Any]:
        """
        Save API key for a model to database
        
        Args:
            model_id: Model identifier
            api_key: API key to save
            
        Returns:
            Dictionary with save result and validation status
        """
        try:
            # Get model config to extract provider info
            model_config = self.config.get('ai_models', {}).get(model_id)
            if not model_config:
                raise ValueError(f"Model '{model_id}' not found")
            
            provider = model_config.get('provider')
            api_endpoint = model_config.get('api_endpoint')
            
            # Validate API key by testing connection
            validation_result = self._validate_api_key(model_id, api_key)
            
            # Save to database
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO api_credentials (model_id, provider, api_key, api_endpoint, 
                                            validation_status, validation_message, last_validated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (model_id) 
                DO UPDATE SET 
                    api_key = EXCLUDED.api_key,
                    validation_status = EXCLUDED.validation_status,
                    validation_message = EXCLUDED.validation_message,
                    last_validated_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (model_id, provider, api_key, api_endpoint, 
                  validation_result['status'], validation_result['message']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Clear cached provider to force reload with new key
            if model_id in self.providers:
                del self.providers[model_id]
            
            logger.info(f"API key saved for model: {model_id}")
            
            return {
                'success': True,
                'model_id': model_id,
                'validation': validation_result
            }
            
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_api_key(self, model_id: str, api_key: str) -> Dict[str, Any]:
        """
        Validate API key by testing connection
        
        Args:
            model_id: Model identifier
            api_key: API key to validate
            
        Returns:
            Validation result with status and message
        """
        try:
            # Get model config
            model_config = self.config.get('ai_models', {}).get(model_id)
            if not model_config:
                logger.error(f"Model '{model_id}' not found in configuration")
                return {
                    'status': 'invalid',
                    'message': f"Model '{model_id}' not found",
                    'available': False
                }
            
            # Make a copy to avoid modifying original config
            model_config = model_config.copy()
            
            # For local models, no validation needed
            if model_config.get('is_local'):
                return {
                    'status': 'valid',
                    'message': 'Local model - no API key required',
                    'available': True
                }
            
            # Temporarily set API key in config for testing
            model_config['api_key'] = api_key
            
            # Get provider class and test connection
            provider_type = model_config.get('provider')
            provider_class = self.PROVIDER_CLASSES.get(provider_type)
            
            if not provider_class:
                logger.error(f"Provider '{provider_type}' not supported")
                return {
                    'status': 'invalid',
                    'message': f"Provider '{provider_type}' not supported",
                    'available': False
                }
            
            # Create temporary provider instance and test
            logger.info(f"Testing API key for {model_id} with provider {provider_type}")
            temp_provider = provider_class(model_config)
            test_result = temp_provider.test_connection()
            
            logger.info(f"API key test result: {test_result}")
            
            if test_result.get('available'):
                return {
                    'status': 'valid',
                    'message': 'API key validated successfully',
                    'available': True
                }
            else:
                return {
                    'status': 'invalid',
                    'message': test_result.get('message', 'API key validation failed'),
                    'available': False
                }
                
        except Exception as e:
            logger.error(f"API key validation error for {model_id}: {e}", exc_info=True)
            return {
                'status': 'invalid',
                'message': f"Validation error: {str(e)}",
                'available': False
            }
    
    def get_api_key(self, model_id: str) -> Optional[str]:
        """
        Get API key for a model from database
        
        Args:
            model_id: Model identifier
            
        Returns:
            API key if found, None otherwise
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT api_key FROM api_credentials 
                WHERE model_id = %s AND is_configured = TRUE
            """, (model_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return result['api_key']
            
            # Fallback to environment variable
            model_config = self.config.get('ai_models', {}).get(model_id)
            if model_config:
                api_key_env = model_config.get('api_key_env')
                if api_key_env:
                    return os.getenv(api_key_env)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None
    
    def is_model_configured(self, model_id: str) -> bool:
        """
        Check if model is configured with valid API key
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if configured, False otherwise
        """
        try:
            # Local models don't need configuration
            model_config = self.config.get('ai_models', {}).get(model_id)
            if model_config and model_config.get('is_local'):
                return True
            
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT is_configured FROM api_credentials 
                WHERE model_id = %s AND validation_status = 'valid'
            """, (model_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                return True
            
            # Check environment variable as fallback
            if model_config:
                api_key_env = model_config.get('api_key_env')
                if api_key_env and os.getenv(api_key_env):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking model configuration: {e}")
            return False
    
    def get_provider_with_api_key(self, model_id: str) -> BaseAIProvider:
        """
        Get provider with API key loaded from database
        
        Args:
            model_id: Model identifier
            
        Returns:
            Provider instance with API key configured
        """
        # Get model config
        model_config = self.config.get('ai_models', {}).get(model_id)
        if not model_config:
            raise ValueError(f"Model '{model_id}' not found")
        
        # For local models, use standard get_provider
        if model_config.get('is_local'):
            return self.get_provider(model_id)
        
        # Load API key from database
        api_key = self.get_api_key(model_id)
        if not api_key:
            raise ValueError(f"No API key configured for model '{model_id}'")
        
        # Create config with API key
        model_config_with_key = model_config.copy()
        model_config_with_key['api_key'] = api_key
        
        # Get provider class
        provider_type = model_config.get('provider')
        provider_class = self.PROVIDER_CLASSES.get(provider_type)
        
        if not provider_class:
            raise ValueError(f"Provider '{provider_type}' not supported")
        
        # Create and return provider (don't cache to avoid stale API keys)
        provider = provider_class(model_config_with_key)
        logger.info(f"Created provider for {model_id} with database API key")
        
        return provider
