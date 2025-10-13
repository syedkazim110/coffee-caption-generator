"""
Platform-Specific Content Strategy Module
Handles character limits, tone adjustments, and formatting for different social media platforms
"""

from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Platform specifications
PLATFORM_SPECS = {
    'instagram': {
        'max_chars': 150,
        'min_chars': 40,
        'tone_style': 'Visual-focused, casual, engaging, lifestyle-oriented',
        'format_style': 'Emoji-friendly, aspirational, call to engagement',
        'hashtag_strategy': 'Use 3-5 hashtags inline or at end',
        'emoji_usage': 'Moderate to high (1-2 per caption)'
    },
    'facebook': {
        'max_chars': 80,
        'min_chars': 40,
        'tone_style': 'Conversational, friendly, community-focused',
        'format_style': 'Personal connection, storytelling snippets',
        'hashtag_strategy': 'Use 1-3 hashtags, more subtle',
        'emoji_usage': 'Light (0-1 per caption)'
    },
    'linkedin': {
        'max_chars': 300,
        'min_chars': 150,
        'tone_style': 'Professional, informative, thought-leadership',
        'format_style': 'Industry insights, business value, expertise',
        'hashtag_strategy': 'Use 2-4 professional hashtags',
        'emoji_usage': 'Minimal to none'
    },
    'twitter': {
        'max_chars': 100,
        'min_chars': 70,
        'tone_style': 'Punchy, witty, trending',
        'format_style': 'Quick impact, viral potential, shareworthy',
        'hashtag_strategy': 'Use 1-2 trending hashtags',
        'emoji_usage': 'Moderate (1 per caption)'
    }
}


class PlatformStrategy:
    """Handles platform-specific content generation and validation"""
    
    def __init__(self):
        self.platform_specs = PLATFORM_SPECS
    
    def get_platform_spec(self, platform: str) -> Dict[str, Any]:
        """Get specifications for a platform"""
        platform_lower = platform.lower()
        if platform_lower not in self.platform_specs:
            logger.warning(f"Unknown platform: {platform}, using Instagram defaults")
            return self.platform_specs['instagram']
        return self.platform_specs[platform_lower]
    
    def build_platform_prompt(
        self, 
        platform: str, 
        brand_voice: Dict[str, Any],
        keyword: str,
        context_snippets: list
    ) -> str:
        """Build platform-specific prompt for LLM"""
        spec = self.get_platform_spec(platform)
        
        # Extract brand voice elements
        adjectives = brand_voice.get('core_adjectives', [])
        lexicon_always = brand_voice.get('lexicon_always_use', [])
        lexicon_never = brand_voice.get('lexicon_never_use', [])
        
        # Build adjectives string
        adjectives_str = ', '.join(adjectives[:5]) if adjectives else 'Engaging, Authentic'
        
        # Build lexicon constraints
        always_use_str = ', '.join(lexicon_always[:5]) if lexicon_always else ''
        never_use_str = ', '.join(lexicon_never[:5]) if lexicon_never else ''
        
        # Build context string
        context_str = ' '.join(context_snippets[:2])[:300] if context_snippets else ''
        
        # Platform-specific instructions
        platform_instructions = {
            'instagram': 'Create a visually inspiring, lifestyle-focused caption. Be aspirational and engaging.',
            'facebook': 'Write in a warm, conversational tone that encourages community interaction.',
            'linkedin': 'Provide professional insights and thought leadership. Be informative and valuable.',
            'twitter': 'Write a punchy, memorable one-liner. Make it shareable and impactful.'
        }
        
        instruction = platform_instructions.get(platform.lower(), platform_instructions['instagram'])
        
        # Build the prompt
        prompt = f"""You are a professional social media copywriter. Create a caption for {platform.upper()}.

PLATFORM: {platform.upper()}
CHARACTER LIMIT: {spec['min_chars']}-{spec['max_chars']} characters (STRICT - must fit within this range)
TONE STYLE: {spec['tone_style']}
FORMAT: {spec['format_style']}
EMOJI USAGE: {spec['emoji_usage']}

BRAND VOICE: {adjectives_str}
TOPIC: {keyword}

ALWAYS INCLUDE (when relevant): {always_use_str if always_use_str else 'N/A'}
NEVER USE: {never_use_str if never_use_str else 'N/A'}

CONTEXT: {context_str}

INSTRUCTIONS:
{instruction}
- Write ONLY the caption text, no hashtags (hashtags will be added separately)
- Character count MUST be between {spec['min_chars']}-{spec['max_chars']} characters
- Use {spec['emoji_usage'].lower()}
- Be authentic to the brand voice
- Make it platform-appropriate

Your caption:"""

        return prompt
    
    def validate_caption_length(self, caption: str, platform: str) -> Dict[str, Any]:
        """Validate caption meets platform character limits"""
        spec = self.get_platform_spec(platform)
        
        # Remove hashtags if present for accurate count
        caption_text = caption.split('#')[0].strip() if '#' in caption else caption
        
        char_count = len(caption_text)
        is_valid = spec['min_chars'] <= char_count <= spec['max_chars']
        
        return {
            'valid': is_valid,
            'char_count': char_count,
            'min_chars': spec['min_chars'],
            'max_chars': spec['max_chars'],
            'platform': platform,
            'needs_truncation': char_count > spec['max_chars'],
            'needs_expansion': char_count < spec['min_chars']
        }
    
    def truncate_caption(self, caption: str, platform: str) -> str:
        """Truncate caption to fit platform limits - improved to avoid incomplete sentences"""
        spec = self.get_platform_spec(platform)
        max_chars = spec['max_chars']
        
        if len(caption) <= max_chars:
            return caption
        
        logger.warning(f"Truncating caption for {platform}: {len(caption)} > {max_chars} chars")
        
        # Try to find the last complete sentence within the limit
        truncated = caption[:max_chars]
        
        # Look for sentence endings
        last_period = truncated.rfind('.')
        last_exclaim = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        sentence_end = max(last_period, last_exclaim, last_question)
        
        # If we have at least 60% of the content with a sentence ending, use it
        if sentence_end > max_chars * 0.6:
            result = caption[:sentence_end + 1].strip()
            logger.info(f"Truncated at sentence boundary: {len(result)} chars")
            return result
        
        # Otherwise, truncate at word boundary and add period (no "...")
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.5:
            truncated_at_word = caption[:last_space].strip()
            # Add period only if it doesn't already end with punctuation
            if truncated_at_word and truncated_at_word[-1] not in '.!?,;:':
                result = truncated_at_word + '.'
            else:
                result = truncated_at_word
            logger.info(f"Truncated at word boundary: {len(result)} chars")
            return result
        
        # Last resort: cut at limit and add period
        result = truncated.strip()
        if result and result[-1] not in '.!?':
            result += '.'
        logger.info(f"Truncated at character limit: {len(result)} chars")
        return result
    
    def format_hashtags_for_platform(self, hashtags: list, platform: str) -> str:
        """Format hashtags according to platform best practices"""
        spec = self.get_platform_spec(platform)
        
        # Limit hashtag count based on platform
        if platform.lower() == 'instagram':
            hashtags = hashtags[:5]
        elif platform.lower() == 'facebook':
            hashtags = hashtags[:3]
        elif platform.lower() == 'linkedin':
            hashtags = hashtags[:4]
        elif platform.lower() == 'twitter':
            hashtags = hashtags[:2]
        else:
            hashtags = hashtags[:3]
        
        return ' '.join(hashtags)
    
    def get_platform_tone_modifier(self, platform: str, base_tone: str) -> str:
        """Get platform-specific tone modifier"""
        tone_modifiers = {
            'instagram': 'visual and inspirational',
            'facebook': 'warm and conversational',
            'linkedin': 'professional and insightful',
            'twitter': 'concise and impactful'
        }
        
        modifier = tone_modifiers.get(platform.lower(), 'engaging')
        return f"{base_tone}, {modifier}"
    
    def apply_platform_formatting(self, caption: str, platform: str) -> str:
        """Apply platform-specific formatting rules"""
        platform_lower = platform.lower()
        
        # LinkedIn: Remove most emojis
        if platform_lower == 'linkedin':
            # Keep only professional emojis
            professional_emojis = ['💼', '📊', '📈', '🎯', '💡', '🔍', '✅']
            for char in caption:
                if self._is_emoji(char) and char not in professional_emojis:
                    caption = caption.replace(char, '')
        
        # Facebook: Ensure conversational flow
        if platform_lower == 'facebook':
            # Add question or engagement prompt if not present
            if not any(caption.endswith(x) for x in ['?', '!', '.']):
                caption += '!'
        
        # Twitter: Ensure no trailing spaces
        if platform_lower == 'twitter':
            caption = ' '.join(caption.split())  # Normalize spaces
        
        return caption.strip()
    
    def _is_emoji(self, char: str) -> bool:
        """Check if character is an emoji"""
        return ord(char) > 127  # Simple emoji detection
    
    def get_all_platforms(self) -> list:
        """Get list of supported platforms"""
        return list(self.platform_specs.keys())
    
    def get_platform_summary(self, platform: str) -> Dict[str, Any]:
        """Get a summary of platform specifications"""
        spec = self.get_platform_spec(platform)
        return {
            'platform': platform,
            'character_range': f"{spec['min_chars']}-{spec['max_chars']} chars",
            'tone': spec['tone_style'],
            'emoji_usage': spec['emoji_usage'],
            'hashtag_strategy': spec['hashtag_strategy']
        }


def main():
    """Demo platform strategies"""
    print("📱 Platform Strategy Demo")
    print("=" * 60)
    
    strategy = PlatformStrategy()
    
    # Demo 1: Show all platform specs
    print("\n📋 Platform Specifications:")
    for platform in strategy.get_all_platforms():
        summary = strategy.get_platform_summary(platform)
        print(f"\n{platform.upper()}:")
        print(f"   • Character Range: {summary['character_range']}")
        print(f"   • Tone: {summary['tone']}")
        print(f"   • Emoji: {summary['emoji_usage']}")
        print(f"   • Hashtags: {summary['hashtag_strategy']}")
    
    # Demo 2: Validate captions
    print("\n\n✅ Caption Validation Demo:")
    test_captions = {
        'instagram': "This cold brew is absolutely amazing! Perfect for those morning vibes when you need that extra boost ☕✨",
        'facebook': "Morning coffee ritual ☕ Who else can't start their day without it?",
        'linkedin': "The specialty coffee industry continues to demonstrate resilience and innovation. As consumer preferences evolve toward sustainable and ethically-sourced products, brands that prioritize transparency and quality are seeing significant growth in market share.",
        'twitter': "Cold brew perfection in every sip ☕ #CoffeeLovers"
    }
    
    for platform, caption in test_captions.items():
        validation = strategy.validate_caption_length(caption, platform)
        status = "✅ VALID" if validation['valid'] else "❌ INVALID"
        print(f"\n{platform.upper()}: {status}")
        print(f"   • Caption: {caption[:50]}...")
        print(f"   • Length: {validation['char_count']} chars")
        print(f"   • Required: {validation['min_chars']}-{validation['max_chars']} chars")
        
        if not validation['valid']:
            if validation['needs_truncation']:
                truncated = strategy.truncate_caption(caption, platform)
                print(f"   • Truncated: {truncated}")
    
    # Demo 3: Hashtag formatting
    print("\n\n🏷️ Hashtag Formatting Demo:")
    test_hashtags = ['#coffee', '#coffeelover', '#specialtycoffee', '#coffeetime', '#barista']
    
    for platform in strategy.get_all_platforms():
        formatted = strategy.format_hashtags_for_platform(test_hashtags, platform)
        print(f"\n{platform.upper()}:")
        print(f"   • {formatted}")
    
    print("\n\n✅ Demo complete!")


if __name__ == "__main__":
    main()
