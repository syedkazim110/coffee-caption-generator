#!/usr/bin/env python3
"""
Test script to verify scenario enforcement works correctly
"""

from llm_rag_caption_generator import LLMRAGCaptionGenerator
import json

def test_scenario_enforcement():
    """Test that the LLM follows the provided scenario"""
    
    print("🧪 Testing Scenario Enforcement")
    print("=" * 60)
    
    # Initialize generator
    print("\n1️⃣ Initializing caption generator...")
    generator = LLMRAGCaptionGenerator()
    
    # Test scenario from user
    test_scenario = "Sale 10% off for Italian Frogman Espresso"
    keyword = "espresso"
    
    print(f"\n2️⃣ Testing with scenario: '{test_scenario}'")
    print(f"   Keyword: {keyword}")
    
    # Generate post with scenario
    print("\n3️⃣ Generating caption with scenario enforcement...")
    post_data = generator.generate_complete_post(
        keyword=keyword,
        platform='instagram',
        scenario=test_scenario
    )
    
    # Display results
    print("\n📊 RESULTS:")
    print("-" * 60)
    print(f"Caption: {post_data['caption']}")
    print(f"\nHashtags: {' '.join(post_data['hashtags'])}")
    
    # Validation check
    print("\n✅ VALIDATION:")
    caption_lower = post_data['caption'].lower()
    
    checks = {
        "Contains '10%'": '10%' in caption_lower or 'ten percent' in caption_lower,
        "Contains 'sale' or 'off'": 'sale' in caption_lower or 'off' in caption_lower,
        "Contains 'Italian Frogman Espresso'": all(word in caption_lower for word in ['italian', 'frogman', 'espresso'])
    }
    
    print("-" * 60)
    for check, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n🎉 SUCCESS! All scenario keywords are present in the caption!")
    else:
        print("\n⚠️ WARNING: Some scenario keywords are missing. The LLM may need a better model.")
    
    # Save test results
    test_results = {
        'scenario': test_scenario,
        'caption': post_data['caption'],
        'validation': checks,
        'all_passed': all_passed
    }
    
    with open('scenario_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print("\n💾 Test results saved to: scenario_test_results.json")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_scenario_enforcement()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
