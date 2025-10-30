#!/usr/bin/env python3
"""
Catchy Coffee Caption Generator CLI
Generate viral-style coffee captions using RAG and trending keywords
"""

import json
from rag_caption_generator import RAGCaptionGenerator
import argparse
import random

def main():
    print("☕ Catchy Coffee Caption Generator")
    print("=" * 50)
    
    # Initialize the generator
    try:
        generator = RAGCaptionGenerator()
        print(f"✅ Loaded {len(generator.trending_keywords)} trending keywords")
        print(f"✅ Loaded {len(generator.documents)} coffee articles for RAG")
    except Exception as e:
        print(f"❌ Error initializing generator: {e}")
        return
    
    while True:
        print("\n🎯 What would you like to do?")
        print("1. Generate captions for a specific keyword")
        print("2. Generate random captions from trending keywords")
        print("3. Generate captions for a specific style")
        print("4. Show available trending keywords")
        print("5. Show available caption styles")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            generate_for_keyword(generator)
        elif choice == '2':
            generate_random_captions(generator)
        elif choice == '3':
            generate_for_style(generator)
        elif choice == '4':
            show_trending_keywords(generator)
        elif choice == '5':
            show_caption_styles(generator)
        elif choice == '6':
            print("👋 Thanks for using the Caption Generator!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def generate_for_keyword(generator):
    """Generate captions for a specific keyword"""
    print("\n🔍 Enter a keyword (or press Enter to see trending options):")
    keyword = input().strip()
    
    if not keyword:
        print("\n📈 Here are some trending keywords:")
        sample_keywords = random.sample(generator.trending_keywords, min(10, len(generator.trending_keywords)))
        for i, kw in enumerate(sample_keywords, 1):
            print(f"{i}. {kw}")
        
        keyword = input("\nEnter a keyword from above or type your own: ").strip()
    
    if not keyword:
        print("❌ No keyword provided.")
        return
    
    count = input("How many captions? (default: 5): ").strip()
    try:
        count = int(count) if count else 5
    except ValueError:
        count = 5
    
    print(f"\n🎨 Generating {count} captions for '{keyword}'...")
    captions = generator.generate_multiple_rag_captions(count, keyword)
    
    display_captions(captions)
    
    save = input("\n💾 Save these captions? (y/n): ").strip().lower()
    if save == 'y':
        filename = f"captions_{keyword.replace(' ', '_')}.json"
        generator.save_generated_captions(captions, filename)

def generate_random_captions(generator):
    """Generate random captions from trending keywords"""
    count = input("How many random captions? (default: 10): ").strip()
    try:
        count = int(count) if count else 10
    except ValueError:
        count = 10
    
    print(f"\n🎲 Generating {count} random captions from trending keywords...")
    captions = generator.generate_multiple_rag_captions(count)
    
    display_captions(captions)
    
    save = input("\n💾 Save these captions? (y/n): ").strip().lower()
    if save == 'y':
        generator.save_generated_captions(captions, "random_captions.json")

def generate_for_style(generator):
    """Generate captions for a specific style"""
    styles = list(generator.templates.keys())
    
    print("\n🎭 Available caption styles:")
    for i, style in enumerate(styles, 1):
        print(f"{i}. {style}")
    
    choice = input(f"\nChoose a style (1-{len(styles)}): ").strip()
    try:
        style_index = int(choice) - 1
        if 0 <= style_index < len(styles):
            selected_style = styles[style_index]
        else:
            print("❌ Invalid choice.")
            return
    except ValueError:
        print("❌ Invalid choice.")
        return
    
    count = input("How many captions? (default: 5): ").strip()
    try:
        count = int(count) if count else 5
    except ValueError:
        count = 5
    
    print(f"\n🎨 Generating {count} '{selected_style}' captions...")
    captions = []
    for _ in range(count):
        caption_data = generator.generate_rag_caption(template_category=selected_style)
        captions.append(caption_data)
    
    display_captions(captions)
    
    save = input("\n💾 Save these captions? (y/n): ").strip().lower()
    if save == 'y':
        filename = f"captions_{selected_style}.json"
        generator.save_generated_captions(captions, filename)

def show_trending_keywords(generator):
    """Show all trending keywords"""
    print(f"\n📈 All {len(generator.trending_keywords)} Trending Keywords:")
    print("-" * 50)
    
    for i, keyword in enumerate(generator.trending_keywords, 1):
        print(f"{i:3d}. {keyword}")
        if i % 20 == 0:
            cont = input("\nPress Enter to continue or 'q' to stop: ").strip()
            if cont.lower() == 'q':
                break

def show_caption_styles(generator):
    """Show all available caption styles with examples"""
    print("\n🎭 Available Caption Styles:")
    print("-" * 50)
    
    for style, templates in generator.templates.items():
        print(f"\n📝 {style.upper()}:")
        print(f"   Example: {templates[0]}")

def display_captions(captions):
    """Display generated captions in a nice format"""
    print("\n✨ Generated Captions:")
    print("=" * 50)
    
    for i, caption_data in enumerate(captions, 1):
        print(f"\n{i}. {caption_data['caption']}")
        print(f"   📊 Keyword: {caption_data['keyword']}")
        print(f"   🎯 Context: {caption_data['retrieved_context']}")
        print(f"   🎭 Style: {caption_data['template_category']}")

if __name__ == "__main__":
    main()
