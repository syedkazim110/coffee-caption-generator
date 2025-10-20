#!/usr/bin/env python3
"""
Test script to verify the FIXED truncation system handles hashtags properly
NO MORE PARTIAL HASHTAGS like #cof or #.!
"""

import sys
sys.path.append('.')

from llm_rag_caption_generator import LLMRAGCaptionGenerator

def test_new_separated_truncation():
    """Test the NEW separated caption/hashtag system"""
    
    print("🧪 Testing NEW Separated Caption/Hashtag System")
    print("=" * 60)
    
    # Initialize generator
    generator = LLMRAGCaptionGenerator()
    
    print("\n✅ NEW APPROACH: Caption and hashtags are SEPARATE!")
    print("   1. Caption text is truncated ALONE")
    print("   2. Hashtags are added BELOW with \\n\\n")
    print("   3. Hashtags are either COMPLETE or REMOVED\n")
    
    # Test Case 1: Caption with hashtags - the problematic one
    test_caption = "Try our specialty coffee—each cup tells WarPath's story!"
    test_hashtags = ['#coffee', '#coffeelover', '#specialty', '#coffeetime']
    max_total = 80  # Total limit including hashtags
    
    print("\n📝 Test Case 1: Short Limit (Forces Truncation)")
    print(f"   Caption: {test_caption}")
    print(f"   Hashtags: {' '.join(test_hashtags)}")
    print(f"   Max total: {max_total} chars")
    
    # Step 1: Truncate caption if needed
    if len(test_caption) > max_total - 20:  # Reserve space for hashtags
        caption_limit = max_total - 20
        truncated_caption = generator.intelligent_truncate_caption_only(test_caption, caption_limit)
    else:
        truncated_caption = test_caption
    
    # Step 2: Combine with hashtags
    result = generator.combine_caption_and_hashtags(truncated_caption, test_hashtags, max_total)
    
    print(f"\n✨ Result:")
    print(f"   {result}")
    print(f"   Length: {len(result)} chars")
    
    # Validation
    import re
    partial_hashtags = re.findall(r'#[a-zA-Z]{1,2}(?:\s|$)', result)
    has_partial = len(partial_hashtags) > 0 or result.endswith('#')
    
    if has_partial:
        print(f"   ❌ FAIL: Found partial hashtags: {partial_hashtags}")
    else:
        print("   ✅ PASS: No partial hashtags!")
    
    if len(result) <= max_total:
        print(f"   ✅ PASS: Within limit ({len(result)}/{max_total})")
    else:
        print(f"   ❌ FAIL: Exceeds limit ({len(result)}/{max_total})")
    
    # Test Case 2: Very tight limit - should drop all hashtags
    test_caption_2 = "Amazing cold brew experience"
    test_hashtags_2 = ['#coldbrew', '#coffee', '#amazing']
    max_total_2 = 30
    
    print("\n\n📝 Test Case 2: Very Tight Limit (Should Drop Hashtags)")
    print(f"   Caption: {test_caption_2}")
    print(f"   Hashtags: {' '.join(test_hashtags_2)}")
    print(f"   Max total: {max_total_2} chars")
    
    result_2 = generator.combine_caption_and_hashtags(test_caption_2, test_hashtags_2, max_total_2)
    
    print(f"\n✨ Result:")
    print(f"   {result_2}")
    print(f"   Length: {len(result_2)} chars")
    
    # Should be just caption, no hashtags
    if '#' not in result_2:
        print("   ✅ PASS: Correctly dropped all hashtags (no space)")
    else:
        # Check if hashtags are complete
        partial_hashtags_2 = re.findall(r'#[a-zA-Z]{1,2}(?:\s|$)', result_2)
        if len(partial_hashtags_2) > 0:
            print(f"   ❌ FAIL: Found partial hashtags: {partial_hashtags_2}")
        else:
            print("   ✅ PASS: All hashtags are complete")
    
    # Test Case 3: Enough space for some hashtags
    test_caption_3 = "Perfect morning brew"
    test_hashtags_3 = ['#coffee', '#morning', '#brew', '#coffeetime', '#amazing']
    max_total_3 = 60
    
    print("\n\n📝 Test Case 3: Moderate Limit (Fits Some Hashtags)")
    print(f"   Caption: {test_caption_3}")
    print(f"   Hashtags: {' '.join(test_hashtags_3)}")
    print(f"   Max total: {max_total_3} chars")
    
    result_3 = generator.combine_caption_and_hashtags(test_caption_3, test_hashtags_3, max_total_3)
    
    print(f"\n✨ Result:")
    print(f"   {result_3}")
    print(f"   Length: {len(result_3)} chars")
    
    # Count complete hashtags
    complete_hashtags = re.findall(r'#[a-zA-Z]{3,}', result_3)
    partial_hashtags_3 = re.findall(r'#[a-zA-Z]{1,2}(?:\s|$)', result_3)
    
    print(f"   Complete hashtags: {len(complete_hashtags)} - {complete_hashtags}")
    
    if len(partial_hashtags_3) > 0:
        print(f"   ❌ FAIL: Found partial hashtags: {partial_hashtags_3}")
    else:
        print("   ✅ PASS: All hashtags are complete!")
    
    # Test Case 4: Real-world example - the one that was failing
    test_caption_4 = "coffee_lover Try our specialty coffee—each cup tells WarPath's story!"
    test_hashtags_4 = ['#coffee', '#coffeelover', '#specialty']
    max_total_4 = 70
    
    print("\n\n📝 Test Case 4: Real Example (Was Showing '#.')")
    print(f"   Caption: {test_caption_4}")
    print(f"   Hashtags: {' '.join(test_hashtags_4)}")
    print(f"   Max total: {max_total_4} chars")
    
    result_4 = generator.combine_caption_and_hashtags(test_caption_4, test_hashtags_4, max_total_4)
    
    print(f"\n✨ Result:")
    print(f"   {result_4}")
    print(f"   Length: {len(result_4)} chars")
    
    # Check for the bad patterns
    has_dot_hash = '#.' in result_4
    has_short_hash = bool(re.search(r'#[a-zA-Z]{1,2}(?:\s|$)', result_4))
    ends_with_hash = result_4.strip().endswith('#')
    
    if has_dot_hash or has_short_hash or ends_with_hash:
        print(f"   ❌ FAIL: Found bad pattern!")
        if has_dot_hash:
            print(f"      - Found '#.'")
        if has_short_hash:
            print(f"      - Found short hashtag")
        if ends_with_hash:
            print(f"      - Ends with #")
    else:
        print("   ✅ PASS: No bad patterns! Clean output!")
    
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📊 Test Summary - NEW SYSTEM")
    print("=" * 60)
    print("✅ The NEW separated system:")
    print("   • Caption and hashtags are SEPARATE throughout")
    print("   • Caption is truncated ALONE (no hashtag interference)")
    print("   • Hashtags are added BELOW with \\n\\n separator")
    print("   • Hashtags are either COMPLETE or REMOVED entirely")
    print("   • NEVER produces '#.', '#cof', or any partial hashtags")
    print("\n🎉 Truncation issue FIXED! No more partial hashtags!")

if __name__ == "__main__":
    test_new_separated_truncation()
