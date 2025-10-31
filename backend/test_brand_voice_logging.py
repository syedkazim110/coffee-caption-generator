#!/usr/bin/env python3
"""
Test script to demonstrate brand voice data logging
Run this to see what values are passed to the LLM
"""

from llm_rag_caption_generator import LLMRAGCaptionGenerator
import logging

# Set up logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def main():
    print("\n" + "="*70)
    print("🧪 TESTING BRAND VOICE DATA LOGGING")
    print("="*70 + "\n")
    
    # Initialize the generator (this will load brand profile)
    print("Initializing generator and loading brand profile...\n")
    generator = LLMRAGCaptionGenerator()
    
    print("\n" + "="*70)
    print("🎯 NOW GENERATING A CAPTION TO SEE BRAND VOICE DATA...")
    print("="*70 + "\n")
    
    # Generate a single post (this will trigger the logging)
    try:
        post = generator.generate_complete_post(
            keyword="cold brew",
            platform="instagram"
        )
        
        print("\n" + "="*70)
        print("✅ CAPTION GENERATED SUCCESSFULLY!")
        print("="*70)
        print(f"\nGenerated Caption:\n{post['caption']}")
        print(f"\nHashtags: {' '.join(post['hashtags'])}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: This might happen if:")
        print("  - Database is not connected")
        print("  - No brand profile is set as active")
        print("  - Ollama is not running")

if __name__ == "__main__":
    main()
