#!/usr/bin/env python3
"""
Verify that the application loads hashtags from database
"""

from llm_rag_caption_generator import LLMRAGCaptionGenerator

print("\n" + "="*60)
print("VERIFYING APPLICATION HASHTAG LOADING")
print("="*60)

try:
    print("\nInitializing caption generator...")
    gen = LLMRAGCaptionGenerator()
    
    print(f"\nResults:")
    print(f"  - Hashtags loaded: {len(gen.hashtag_data)}")
    print(f"  - Hashtag documents: {len(gen.hashtag_documents)}")
    print(f"  - Hashtag metadata: {len(gen.hashtag_metadata)}")
    
    if len(gen.hashtag_data) > 0:
        print(f"\nSample hashtags:")
        for i, hashtag in enumerate(gen.hashtag_data[:5], 1):
            print(f"  {i}. {hashtag['hashtag']} (category: {hashtag['metadata']['keyword']})")
        
        print("\n" + "="*60)
        print("SUCCESS: Application is fetching hashtags from database")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("WARNING: No hashtags loaded - check database connection")
        print("="*60)
        
except Exception as e:
    print(f"\nERROR: {e}")
    print("="*60)
