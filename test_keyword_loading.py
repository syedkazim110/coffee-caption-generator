#!/usr/bin/env python3
"""
Test script to verify the application loads keywords correctly
"""

from llm_rag_caption_generator import LLMRAGCaptionGenerator
import os

print("\n" + "="*60)
print("TESTING KEYWORD LOADING IN APPLICATION")
print("="*60)

# Set the correct database port for Docker
os.environ['DB_PORT'] = '5433'

try:
    print("\nInitializing caption generator...")
    generator = LLMRAGCaptionGenerator()
    
    print(f"\n✅ RESULTS:")
    print(f"   Total trending keywords loaded: {len(generator.trending_keywords)}")
    print(f"   Total hashtag data loaded: {len(generator.hashtag_data)}")
    
    if len(generator.trending_keywords) >= 178:
        print(f"\n✅ SUCCESS! All keywords loaded correctly")
        print(f"\n   Sample trending keywords (first 10):")
        for i, keyword in enumerate(generator.trending_keywords[:10], 1):
            print(f"      {i}. {keyword}")
    else:
        print(f"\n⚠️  WARNING: Expected 178+ keywords, got {len(generator.trending_keywords)}")
        print(f"\n   Keywords that were loaded:")
        for i, keyword in enumerate(generator.trending_keywords, 1):
            print(f"      {i}. {keyword}")
    
    print("\n" + "="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("="*60)
