#!/usr/bin/env python3
"""Test script to verify attribution removal from captions"""

import re

def clean_generated_caption(caption: str) -> str:
    """Clean up generated caption with aggressive attribution removal"""
    
    # Remove common unwanted prefixes/suffixes
    unwanted_prefixes = [
        "Here's a catchy caption:",
        "Caption:",
        "Here's a caption:",
        "Social media caption:",
        "Here's your caption:",
        "Generated caption:"
    ]
    
    for prefix in unwanted_prefixes:
        if caption.lower().startswith(prefix.lower()):
            caption = caption[len(prefix):].strip()
    
    # Remove quotes if the entire caption is wrapped in them
    if (caption.startswith('"') and caption.endswith('"')) or (caption.startswith("'") and caption.endswith("'")):
        caption = caption[1:-1].strip()
    
    # AGGRESSIVE: Remove social media handles (@ mentions)
    caption = re.sub(r'@[\w]+', '', caption)
    
    # AGGRESSIVE: Remove attribution patterns at the END of caption
    # Pattern: "- Name Name" or "— Name Name" or "- Coffee Maven Caroline Cormier" at end
    # This catches full names with titles/descriptors (Coffee Maven, etc.)
    caption = re.sub(r'\s*[-—–]\s*[A-Z][a-zA-Z\s]+[A-Z][a-zA-Z]+\s*["\']?$', '', caption)
    
    # Pattern: Remove any "- [Title] Name Name" format (e.g., "- Coffee Maven Caroline Cormier")
    caption = re.sub(r'\s*[-—–]\s*(?:Coffee|Tea|Barista|Maven)?\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+\s*["\']?$', '', caption, flags=re.IGNORECASE)
    
    # Pattern: "- Name Name | SOURCE" at end
    caption = re.sub(r'\s*[-—–]\s*[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+\s*\|.*$', '', caption)
    
    # Pattern: "| SOURCE" at end
    caption = re.sub(r'\s*\|.*$', '', caption)
    
    # Remove "BARISTA MAGAZINE" and similar
    caption = re.sub(r'\s*[-—–]?\s*BARISTA\s+MAGAZINE.*$', '', caption, flags=re.IGNORECASE)
    caption = re.sub(r'\s*[-—–]?\s*via\s+.*$', '', caption, flags=re.IGNORECASE)
    
    # Remove patterns like "by [Name]" at end
    caption = re.sub(r'\s*[-—–]?\s*by\s+[A-Z][a-zA-Z\s]+$', '', caption, flags=re.IGNORECASE)
    
    # Remove any text after a dash that looks like attribution (contains proper nouns)
    caption = re.sub(r'\s*[-—–]\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\s*["\']?$', '', caption)
    
    # Remove any trailing dashes, quotes, or attribution markers
    caption = re.sub(r'\s*[-—–"\'\s]+$', '', caption)
    
    # Clean up multiple spaces
    caption = re.sub(r'\s+', ' ', caption)
    
    # Clean up trailing punctuation and whitespace
    caption = caption.strip(' .-—–"\'\s')
    
    # Ensure proper sentence ending
    if caption and not caption[-1] in '.!?':
        # If the caption doesn't end with punctuation, check if it looks complete
        words = caption.split()
        if len(words) > 3:  # Only add period if it's a substantial caption
            caption += '.'
    
    # Ensure it's not too long
    if len(caption) > 280:
        caption = caption[:277] + "..."
    
    return caption.strip()


# Test cases
test_captions = [
    'Experience a taste of unity with our nitro coffee, where every sip pays homage to global fellowship. Join us as we explore this bold blend\'s journey from farms across the continents crafted in honor and armor against divisiveness." - Coffee Maven Caroline Cormier',
    'This amazing cold brew is incredible - Barista John Smith',
    'Perfect latte art today — Coffee Expert Jane Doe',
    'Great espresso shot | BARISTA MAGAZINE',
    'Delicious cappuccino - via Coffee Weekly',
    'Amazing mocha by Sarah Williams',
    'Incredible matcha latte - Tea Maven Robert Johnson'
]

print("🧪 Testing Attribution Removal")
print("=" * 60)

for i, original in enumerate(test_captions, 1):
    cleaned = clean_generated_caption(original)
    print(f"\n📝 Test {i}:")
    print(f"   Original: {original[:80]}...")
    print(f"   Cleaned:  {cleaned}")
    print(f"   ✅ Attribution removed: {'-' not in cleaned[-30:] if len(cleaned) > 30 else True}")

print("\n" + "=" * 60)
print("✅ All tests completed!")
