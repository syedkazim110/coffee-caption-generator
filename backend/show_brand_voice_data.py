#!/usr/bin/env python3
"""
Direct script to show all brand voice data that gets passed to LLM
"""

from llm_rag_caption_generator import LLMRAGCaptionGenerator

def main():
    print("\n" + "="*70)
    print("📋 BRAND VOICE DATA INSPECTION")
    print("="*70 + "\n")
    
    # Initialize generator
    print("Loading brand profile...\n")
    generator = LLMRAGCaptionGenerator()
    
    # Display all brand voice data
    print("\n" + "="*70)
    print("🎨 BRAND VOICE DATA LOADED:")
    print("="*70)
    
    print(f"\n📛 Brand Name: {generator.brand_name}")
    print(f"\n🎭 Voice Adjectives: {generator.brand_voice_adjectives}")
    print(f"\n✅ Lexicon - Always Use: {generator.brand_lexicon_always}")
    print(f"\n❌ Lexicon - Never Use: {generator.brand_lexicon_never}")
    print(f"\n🎯 Target Audience: '{generator.target_audience}' {' (NOT SET)' if not generator.target_audience else ''}")
    print(f"\n🏭 Industry: '{generator.industry}' {' (NOT SET)' if not generator.industry else ''}")
    print(f"\n🖼️  Image Style: {generator.brand_image_style[:80]}...")
    
    print("\n" + "="*70)
    print("📝 THIS IS WHAT GETS PASSED TO THE LLM")
    print("="*70)
    
    # Show what gets sent to platform strategy
    brand_voice_dict = {
        'core_adjectives': generator.brand_voice_adjectives,
        'lexicon_always_use': generator.brand_lexicon_always,
        'lexicon_never_use': generator.brand_lexicon_never
    }
    
    print(f"\nBrand Voice Dict: {brand_voice_dict}")
    print(f"Target Audience: {generator.target_audience if generator.target_audience else 'None'}")
    print(f"Industry: {generator.industry if generator.industry else 'None'}")
    
    print("\n" + "="*70)
    print("💡 NOTE: These values are passed to the LLM in the prompt")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
