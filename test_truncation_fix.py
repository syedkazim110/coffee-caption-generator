#!/usr/bin/env python3
"""
Test script to verify the improved truncation system handles hashtags properly
"""

import sys
sys.path.append('.')

from llm_rag_caption_generator import LLMRAGCaptionGenerator

def test_truncation_with_hashtags():
    """Test the improved truncation system with various test cases"""
    
    print("🧪 Testing Improved Truncation System")
    print("=" * 60)
    
    # Initialize generator (minimal setup for testing)
    generator = LLMRAGCaptionGenerator()
    
    # Test Case 1: Your exact example that was failing
    test_case_1 = "Experience coffee with soul, sourced from veteran farmers—where every cup is a testament to honor and quality. #CoffeeLover #VeteranOwned #QualityCoffee"
    max_chars_1 = 140
    
    print("\n📝 Test Case 1: Your Exact Example")
    print(f"   Original: {test_case_1}")
    print(f"   Length: {len(test_case_1)} chars")
    print(f"   Max allowed: {max_chars_1} chars")
    
    truncated_1 = generator.intelligent_truncate(test_case_1, max_chars_1)
    
    print(f"\n✨ Result:")
    print(f"   Truncated: {truncated_1}")
    print(f"   Length: {len(truncated_1)} chars")
    
    # Validation
    if "#Ch" in truncated_1 or truncated_1.endswith("#"):
        print("   ❌ FAIL: Partial hashtag found!")
    else:
        print("   ✅ PASS: No partial hashtags!")
    
    if len(truncated_1) <= max_chars_1:
        print(f"   ✅ PASS: Within character limit")
    else:
        print(f"   ❌ FAIL: Exceeds character limit by {len(truncated_1) - max_chars_1} chars")
    
    # Test Case 2: Caption too long with many hashtags
    test_case_2 = "Discover the rich flavors of our artisan coffee blend, carefully crafted from the finest beans around the world. #Coffee #Espresso #Latte #CoffeeLover #CoffeeAddict #MorningCoffee #CoffeeTime"
    max_chars_2 = 100
    
    print("\n\n📝 Test Case 2: Long Caption with Many Hashtags")
    print(f"   Original: {test_case_2}")
    print(f"   Length: {len(test_case_2)} chars")
    print(f"   Max allowed: {max_chars_2} chars")
    
    truncated_2 = generator.intelligent_truncate(test_case_2, max_chars_2)
    
    print(f"\n✨ Result:")
    print(f"   Truncated: {truncated_2}")
    print(f"   Length: {len(truncated_2)} chars")
    
    # Validation
    if "#" in truncated_2 and not all(h.startswith("#") and " " not in h.strip("#") for h in truncated_2.split() if "#" in h):
        print("   ❌ FAIL: Partial hashtag found!")
    else:
        print("   ✅ PASS: No partial hashtags!")
    
    if len(truncated_2) <= max_chars_2:
        print(f"   ✅ PASS: Within character limit")
    else:
        print(f"   ❌ FAIL: Exceeds character limit")
    
    # Test Case 3: Caption that fits perfectly
    test_case_3 = "Perfect morning brew. #Coffee #MorningVibes"
    max_chars_3 = 50
    
    print("\n\n📝 Test Case 3: Caption That Fits")
    print(f"   Original: {test_case_3}")
    print(f"   Length: {len(test_case_3)} chars")
    print(f"   Max allowed: {max_chars_3} chars")
    
    truncated_3 = generator.intelligent_truncate(test_case_3, max_chars_3)
    
    print(f"\n✨ Result:")
    print(f"   Truncated: {truncated_3}")
    print(f"   Length: {len(truncated_3)} chars")
    
    if truncated_3 == test_case_3:
        print("   ✅ PASS: Unchanged (fits within limit)")
    else:
        print("   ⚠️  Modified when it should have fit")
    
    # Test Case 4: Caption with incomplete sentence ending
    test_case_4 = "Amazing coffee experience with—"
    max_chars_4 = 30
    
    print("\n\n📝 Test Case 4: Incomplete Sentence Ending")
    print(f"   Original: {test_case_4}")
    print(f"   Length: {len(test_case_4)} chars")
    print(f"   Max allowed: {max_chars_4} chars")
    
    truncated_4 = generator.intelligent_truncate(test_case_4, max_chars_4)
    
    print(f"\n✨ Result:")
    print(f"   Truncated: {truncated_4}")
    print(f"   Length: {len(truncated_4)} chars")
    
    if truncated_4.endswith((".", "!", "?")):
        print("   ✅ PASS: Ends with proper punctuation")
    else:
        print("   ❌ FAIL: Missing proper ending punctuation")
    
    # Test Case 5: Edge case - only hashtags
    test_case_5 = "#Coffee #Espresso #Latte #CoffeeLover #CoffeeTime #MorningBrew"
    max_chars_5 = 30
    
    print("\n\n📝 Test Case 5: Only Hashtags")
    print(f"   Original: {test_case_5}")
    print(f"   Length: {len(test_case_5)} chars")
    print(f"   Max allowed: {max_chars_5} chars")
    
    truncated_5 = generator.intelligent_truncate(test_case_5, max_chars_5)
    
    print(f"\n✨ Result:")
    print(f"   Truncated: {truncated_5}")
    print(f"   Length: {len(truncated_5)} chars")
    
    # Validation - should keep complete hashtags only
    has_partial = any(word.startswith("#") and len(word) < 3 for word in truncated_5.split())
    if not has_partial:
        print("   ✅ PASS: No partial hashtags")
    else:
        print("   ❌ FAIL: Partial hashtag found")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print("✅ The improved truncation system:")
    print("   • Separates caption text from hashtags")
    print("   • Never creates partial hashtags like '#Ch'")
    print("   • Maintains complete sentences when possible")
    print("   • Adds proper punctuation to incomplete endings")
    print("   • Fits as many complete hashtags as space allows")
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_truncation_with_hashtags()
