"""
Test script for AI Service and providers.
Tests connection and generation for all configured AI models.
"""
import logging
from ai_service import AIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ai_service():
    """Test AI Service functionality"""
    print("=" * 70)
    print("AI SERVICE TEST SUITE")
    print("=" * 70)
    
    # Initialize AI Service
    print("\n1. Initializing AI Service...")
    try:
        ai_service = AIService()
        print(f"✅ AI Service initialized successfully")
        print(f"   Default model: {ai_service.default_model_id}")
        print(f"   Fallback model: {ai_service.fallback_model_id}")
    except Exception as e:
        print(f"❌ Error initializing AI Service: {e}")
        return
    
    # List all models
    print("\n2. Listing available models...")
    try:
        models_info = ai_service.list_models()
        print(f"✅ Found {models_info['total']} models:")
        for model_id, model_data in models_info['models'].items():
            print(f"   - {model_id}: {model_data['display_name']}")
            print(f"     Provider: {model_data['provider']}, Local: {model_data['is_local']}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
    
    # Test each model's connection
    print("\n3. Testing model connections...")
    test_results = {}
    
    for model_id in models_info['models'].keys():
        print(f"\n   Testing {model_id}...")
        try:
            result = ai_service.test_model(model_id)
            test_results[model_id] = result
            
            if result['available']:
                print(f"   ✅ {model_id}: {result['message']}")
            else:
                print(f"   ⚠️  {model_id}: {result['message']}")
                if 'suggestion' in result:
                    print(f"      Suggestion: {result['suggestion']}")
        except Exception as e:
            print(f"   ❌ {model_id}: Error - {e}")
            test_results[model_id] = {'available': False, 'error': str(e)}
    
    # Test generation with available models
    print("\n4. Testing text generation...")
    test_prompt = "Generate a short, engaging caption for an espresso coffee."
    
    available_models = [
        model_id for model_id, result in test_results.items() 
        if result.get('available', False)
    ]
    
    if available_models:
        print(f"\n   Testing generation with {len(available_models)} available models:")
        
        for model_id in available_models[:2]:  # Test first 2 available models
            print(f"\n   Generating with {model_id}...")
            try:
                result = ai_service.generate(
                    prompt=test_prompt,
                    model_id=model_id
                )
                
                if result['success']:
                    print(f"   ✅ Generated successfully:")
                    print(f"      Model: {result['model_name']}")
                    print(f"      Provider: {result['provider']}")
                    print(f"      Text: {result['text'][:100]}...")
                else:
                    print(f"   ❌ Generation failed")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    else:
        print("   ⚠️  No models available for testing generation")
    
    # Test provider summary
    print("\n5. Provider Summary...")
    try:
        summary = ai_service.get_provider_summary()
        print("✅ Providers:")
        for provider_type, info in summary.items():
            print(f"   - {info['name']}: {info['model_count']} models")
            print(f"     Requires API Key: {info['requires_api_key']}")
            print(f"     Cost Model: {info['cost_model']}")
    except Exception as e:
        print(f"❌ Error getting provider summary: {e}")
    
    # Test cost estimation
    print("\n6. Cost Estimation...")
    try:
        cost_est = ai_service.estimate_cost(
            input_text=test_prompt,
            output_length=250,
            model_id=ai_service.default_model_id
        )
        print(f"✅ Cost estimate for {cost_est['model_id']}:")
        print(f"   Input tokens: {cost_est['input_tokens']}")
        print(f"   Output tokens: {cost_est['output_tokens']}")
        print(f"   Estimated cost: ${cost_est['estimated_cost_usd']:.4f}")
        print(f"   Free model: {cost_est['is_free']}")
    except Exception as e:
        print(f"❌ Error estimating cost: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    total_models = len(test_results)
    available_models = sum(1 for r in test_results.values() if r.get('available', False))
    
    print(f"Total models tested: {total_models}")
    print(f"Available models: {available_models}")
    print(f"Unavailable models: {total_models - available_models}")
    
    print("\nModel Status:")
    for model_id, result in test_results.items():
        status = "✅ Available" if result.get('available', False) else "❌ Unavailable"
        print(f"  {model_id}: {status}")
    
    print("\nRecommendation:")
    if available_models > 0:
        print("✅ AI Service is ready to use!")
        print(f"   Default model ({ai_service.default_model_id}) is {'available' if test_results[ai_service.default_model_id].get('available', False) else 'unavailable'}")
    else:
        print("⚠️  No models are currently available.")
        print("   Please configure at least one provider (Ollama recommended for local use)")
    
    print("=" * 70)


if __name__ == "__main__":
    test_ai_service()
