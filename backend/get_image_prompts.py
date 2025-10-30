#!/usr/bin/env python3
"""Generate 5 coffee image prompts"""

from llm_rag_caption_generator import LLMRAGCaptionGenerator

# Initialize caption generator
generator = LLMRAGCaptionGenerator()

# Test keywords
keywords = ["latte", "espresso", "cold brew", "cappuccino", "mocha"]

print("\n" + "=" * 80)
print("COFFEE IMAGE PROMPTS")
print("=" * 80)

for i, keyword in enumerate(keywords, 1):
    print(f"\n{i}. {keyword.upper()}")
    print("-" * 80)
    
    # Generate post data
    post_data = generator.generate_complete_post(keyword=keyword)
    
    # Display image prompt
    print(f"{post_data['image_prompt']}")

print("\n" + "=" * 80 + "\n")
