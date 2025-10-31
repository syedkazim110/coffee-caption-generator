import pandas as pd
import json
import re
from collections import defaultdict

def extract_coffee_context():
    """Extract engaging coffee language and context from coffee articles"""
    
    # Read the coffee articles
    df = pd.read_csv('coffee_articles.csv')
    
    # Initialize context categories
    context = {
        'flavor_descriptors': [],
        'coffee_experiences': [],
        'brewing_terms': [],
        'sensory_words': [],
        'coffee_emotions': [],
        'origin_descriptions': []
    }
    
    # Common coffee flavor descriptors
    flavor_patterns = [
        r'\b(notes? of|hints? of|flavors? of|taste of)\s+([^,.;]+)',
        r'\b(chocolaty|fruity|nutty|floral|citrusy|sweet|bitter|acidic|smooth|rich|bold|mild)\b',
        r'\b(blueberry|chocolate|vanilla|caramel|honey|berry|citrus|apple|cherry|peach)\b',
        r'\b(cedar|spice|herb|mint|cocoa|coffee|roasted|toasted)\b'
    ]
    
    # Experience and emotion words
    experience_patterns = [
        r'\b(perfect|amazing|incredible|delicious|satisfying|refreshing|energizing)\b',
        r'\b(morning|afternoon|cozy|warm|comfort|ritual|moment|experience)\b',
        r'\b(awakening|invigorating|soothing|calming|uplifting)\b'
    ]
    
    # Brewing and technical terms
    brewing_patterns = [
        r'\b(roasted|brewed|processed|extracted|ground|filtered|steamed)\b',
        r'\b(espresso|latte|cappuccino|americano|macchiato|cortado|flat white)\b',
        r'\b(single origin|blend|arabica|robusta|fair trade|organic)\b'
    ]
    
    # Process all articles
    for _, row in df.iterrows():
        content = str(row.get('content', '')) + ' ' + str(row.get('title', ''))
        
        # Extract flavor descriptors
        for pattern in flavor_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    context['flavor_descriptors'].extend([m.strip() for m in match if m.strip()])
                else:
                    context['flavor_descriptors'].append(match.strip())
        
        # Extract experience words
        for pattern in experience_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            context['coffee_experiences'].extend(matches)
        
        # Extract brewing terms
        for pattern in brewing_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            context['brewing_terms'].extend(matches)
        
        # Extract sensory descriptions (adjective + noun combinations)
        sensory_matches = re.findall(r'\b(rich|smooth|bold|creamy|velvety|silky|robust|delicate|intense|subtle)\s+(\w+)', content, re.IGNORECASE)
        for adj, noun in sensory_matches:
            context['sensory_words'].append(f"{adj} {noun}")
    
    # Clean and deduplicate
    for key in context:
        context[key] = list(set([item.lower().strip() for item in context[key] if item.strip()]))
        context[key] = [item for item in context[key] if len(item) > 2 and len(item) < 50]
    
    # Add some curated coffee emotions and experiences
    context['coffee_emotions'].extend([
        'obsessed', 'addicted', 'in love', 'can\'t live without', 'need this',
        'game changer', 'life changing', 'mind blown', 'hooked', 'craving'
    ])
    
    context['coffee_experiences'].extend([
        'first sip', 'morning ritual', 'afternoon pick-me-up', 'cozy moment',
        'perfect brew', 'coffee break', 'me time', 'comfort drink', 'daily dose'
    ])
    
    return context

def save_coffee_context():
    """Extract and save coffee context to JSON file"""
    context = extract_coffee_context()
    
    # Add timestamp
    from datetime import datetime
    context['timestamp'] = datetime.now().isoformat()
    context['total_terms'] = sum(len(v) for v in context.values() if isinstance(v, list))
    
    with open('coffee_context.json', 'w') as f:
        json.dump(context, f, indent=2)
    
    print("✅ Coffee context extracted and saved!")
    print(f"📊 Total terms extracted: {context['total_terms']}")
    for category, terms in context.items():
        if isinstance(terms, list):
            print(f"  - {category}: {len(terms)} terms")
    
    return context

if __name__ == "__main__":
    save_coffee_context()
