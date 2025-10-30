#!/usr/bin/env python3
"""
Test script to verify brand-aware image prompt generation
This will test if the WarPath army-themed brand style is properly applied
"""

from llm_rag_caption_generator import LLMRAGCaptionGenerator
import json

def test_warpath_brand_generation():
    """Test image generation with WarPath brand"""
    
    print("🧪 Testing Brand-Aware Image Generation")
    print("=" * 60)
    
    # Initialize generator - it will automatically load the active brand (WarPath)
    print("\n📋 Initializing generator with active brand profile...")
    generator = LLMRAGCaptionGenerator()
    
    # Display loaded brand info
    print(f"\n✅ Brand Profile Loaded:")
    print(f"   Brand Name: {generator.brand_name}")
    print(f"   Voice Adjectives: {', '.join(generator.brand_voice_adjectives[:5])}")
    print(f"   Image Style: {generator.brand_image_style}")
    
    # Test with a coffee keyword
    test_keyword = "decaf"
    
    print(f"\n🎯 Generating complete post for keyword: '{test_keyword}'")
    print("-" * 60)
    
    # Generate complete post
    post = generator.generate_complete_post(keyword=test_keyword)
    
    # Display results
    print(f"\n📱 Generated Post:")
    print(f"\n   Keyword: {post['keyword']}")
    print(f"\n   Caption:")
    print(f"   {post['caption']}")
    print(f"\n   Hashtags:")
    print(f"   {' '.join(post['hashtags'])}")
    print(f"\n   Image Prompt:")
    print(f"   {post['image_prompt']}")
    
    # Verify brand style is in the image prompt
    brand_style_keywords = ["warpath", "army", "gear", "pouch", "military", "tactical"]
    image_prompt_lower = post['image_prompt'].lower()
    
    found_keywords = [kw for kw in brand_style_keywords if kw in image_prompt_lower]
    
    print(f"\n🔍 Brand Style Verification:")
    if found_keywords:
        print(f"   ✅ PASS: Found brand-specific keywords: {', '.join(found_keywords)}")
    else:
        print(f"   ⚠️  WARNING: No brand-specific keywords found in image prompt")
        print(f"   Expected keywords: {', '.join(brand_style_keywords)}")
        print(f"   This might indicate the LLM isn't following the brand style guidelines")
    
    # Check if generic coffee terms are present (which would be wrong for WarPath)
    generic_terms = ["cup", "mug", "cafe", "latte art"]
    found_generic = [term for term in generic_terms if term in image_prompt_lower]
    
    if found_generic:
        print(f"   ⚠️  WARNING: Found generic coffee terms: {', '.join(found_generic)}")
        print(f"   These should be avoided for WarPath's army-themed brand")
    
    # Save results
    output_filename = 'brand_test_results.json'
    with open(output_filename, 'w') as f:
        json.dump({
            'brand_name': generator.brand_name,
            'brand_image_style': generator.brand_image_style,
            'test_keyword': test_keyword,
            'generated_post': post,
            'verification': {
                'brand_keywords_found': found_keywords,
                'generic_terms_found': found_generic
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_filename}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")

if __name__ == "__main__":
    test_warpath_brand_generation()
