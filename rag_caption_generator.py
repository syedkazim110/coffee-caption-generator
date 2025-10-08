import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
from datetime import datetime

class RAGCaptionGenerator:
    def __init__(self):
        self.load_data()
        self.setup_vectorizer()
        self.setup_templates()
    
    def load_data(self):
        """Load trending keywords, coffee context, and articles"""
        # Load trending keywords
        with open('trending_coffee_keywords.json', 'r') as f:
            trending_data = json.load(f)
            self.trending_keywords = trending_data['trending_keywords']
        
        # Load coffee context
        with open('coffee_context.json', 'r') as f:
            self.coffee_context = json.load(f)
        
        # Load coffee articles for RAG
        self.coffee_articles = pd.read_csv('coffee_articles.csv')
        
        # Create document corpus for RAG
        self.documents = []
        for _, row in self.coffee_articles.iterrows():
            content = str(row.get('content', '')) + ' ' + str(row.get('title', ''))
            self.documents.append(content)
    
    def setup_vectorizer(self):
        """Setup TF-IDF vectorizer for document retrieval"""
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
        # Fit vectorizer on documents
        self.doc_vectors = self.vectorizer.fit_transform(self.documents)
    
    def setup_templates(self):
        """Define catchy caption templates with RAG placeholders"""
        self.templates = {
            'pov_style': [
                "POV: You try {keyword} and it's {retrieved_context} ☕✨",
                "POV: You discover {keyword} with {retrieved_context} and your mind is blown 🔥",
                "POV: Someone describes {keyword} as {retrieved_context} and you're already ordering 👀☕"
            ],
            
            'relatable': [
                "Me: I don't need {keyword}. Also me: *reads it's {retrieved_context}* 🤷‍♀️",
                "{keyword} that's {retrieved_context} at 3pm? Excellent life choices 😅",
                "When {keyword} is {retrieved_context}, resistance is futile ☕"
            ],
            
            'trending_format': [
                "Everyone's talking about {keyword} being {retrieved_context} and honestly... they're right 🔥",
                "{keyword} with {retrieved_context} hits different 😍",
                "Not me googling '{keyword}' and finding out it's {retrieved_context} 🌙☕"
            ],
            
            'descriptive_catchy': [
                "This {keyword} is {retrieved_context} and I'm obsessed 😍",
                "{keyword} that's {retrieved_context}? Yes please! ☕✨",
                "When your {keyword} is {retrieved_context}... that's the good stuff 🔥"
            ],
            
            'question_hooks': [
                "Is it just me or is {keyword} with {retrieved_context} amazing? 🤔☕",
                "Who else thinks {keyword} being {retrieved_context} is life-changing? 🙋‍♀️",
                "Why is {keyword} that's {retrieved_context} so addictive? ✨"
            ],
            
            'experience_based': [
                "That moment when {keyword} is {retrieved_context} during your morning ritual ✨",
                "Nothing beats {keyword} that's {retrieved_context} for the perfect coffee break ☕",
                "{keyword} with {retrieved_context} making my day infinitely better 💯"
            ]
        }
    
    def retrieve_relevant_context(self, keyword, top_k=3):
        """Retrieve relevant context from coffee articles using RAG"""
        # Vectorize the keyword query
        query_vector = self.vectorizer.transform([keyword])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, self.doc_vectors).flatten()
        
        # Get top-k most similar documents
        top_indices = similarity_scores.argsort()[-top_k:][::-1]
        
        retrieved_contexts = []
        for idx in top_indices:
            if similarity_scores[idx] > 0.1:  # Only include if similarity is above threshold
                doc = self.documents[idx]
                # Extract relevant sentences containing coffee descriptors
                context = self.extract_coffee_descriptors(doc, keyword)
                if context:
                    retrieved_contexts.extend(context)
        
        return retrieved_contexts
    
    def extract_coffee_descriptors(self, document, keyword):
        """Extract relevant coffee descriptors from document"""
        import re
        
        # Look for descriptive phrases
        patterns = [
            r'(notes? of [^,.;]+)',
            r'(hints? of [^,.;]+)',
            r'(flavors? of [^,.;]+)',
            r'(taste of [^,.;]+)',
            r'([a-zA-Z]+ and [a-zA-Z]+ notes?)',
            r'(rich [^,.;]+)',
            r'(smooth [^,.;]+)',
            r'(bold [^,.;]+)',
            r'(delicate [^,.;]+)',
            r'(complex [^,.;]+)',
            r'(balanced [^,.;]+)'
        ]
        
        descriptors = []
        for pattern in patterns:
            matches = re.findall(pattern, document, re.IGNORECASE)
            descriptors.extend([match.strip() for match in matches if len(match.strip()) > 5])
        
        # Clean and filter descriptors
        cleaned_descriptors = []
        for desc in descriptors:
            desc = desc.lower().strip()
            if len(desc) > 5 and len(desc) < 50:
                cleaned_descriptors.append(desc)
        
        return list(set(cleaned_descriptors))[:3]  # Return top 3 unique descriptors
    
    def clean_keyword(self, keyword):
        """Clean and format keyword for better readability"""
        prefixes_to_remove = ['what is ', 'how to make ', 'best ', 'how much caffeine in ']
        
        for prefix in prefixes_to_remove:
            if keyword.lower().startswith(prefix):
                keyword = keyword[len(prefix):]
        
        return keyword.strip()
    
    def generate_rag_caption(self, keyword=None, template_category=None):
        """Generate caption using RAG approach"""
        # Select random keyword if not specified
        if not keyword:
            keyword = random.choice(self.trending_keywords)
        
        keyword = self.clean_keyword(keyword)
        
        # Retrieve relevant context using RAG
        retrieved_contexts = self.retrieve_relevant_context(keyword)
        
        # Fallback to curated context if RAG doesn't find good matches
        if not retrieved_contexts:
            retrieved_contexts = random.choices(
                self.coffee_context['flavor_descriptors'] + 
                self.coffee_context['sensory_words'], 
                k=2
            )
        
        # Select template category
        if not template_category:
            template_category = random.choice(list(self.templates.keys()))
        
        # Get template
        template = random.choice(self.templates[template_category])
        
        # Select best retrieved context
        retrieved_context = random.choice(retrieved_contexts) if retrieved_contexts else "amazing"
        
        # Generate caption
        caption = template.format(
            keyword=keyword,
            retrieved_context=retrieved_context
        )
        
        return {
            'caption': caption,
            'keyword': keyword,
            'retrieved_context': retrieved_context,
            'template_category': template_category,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_multiple_rag_captions(self, count=10, keyword=None):
        """Generate multiple RAG-based captions"""
        captions = []
        
        for _ in range(count):
            template_category = random.choice(list(self.templates.keys()))
            caption_data = self.generate_rag_caption(keyword, template_category)
            captions.append(caption_data)
        
        return captions
    
    def save_generated_captions(self, captions, filename='rag_generated_captions.json'):
        """Save generated captions to file"""
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_captions': len(captions),
            'method': 'RAG (Retrieval-Augmented Generation)',
            'captions': captions
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Saved {len(captions)} RAG-generated captions to {filename}")

def main():
    """Demo the RAG caption generator"""
    print("🎯 RAG-Based Catchy Coffee Caption Generator")
    print("=" * 50)
    
    generator = RAGCaptionGenerator()
    
    # Generate sample captions
    print("\n📝 Sample RAG-Generated Captions:")
    captions = generator.generate_multiple_rag_captions(15)
    
    for i, caption_data in enumerate(captions, 1):
        print(f"\n{i}. {caption_data['caption']}")
        print(f"   Keyword: {caption_data['keyword']}")
        print(f"   Retrieved Context: {caption_data['retrieved_context']}")
        print(f"   Style: {caption_data['template_category']}")
    
    # Save captions
    generator.save_generated_captions(captions)
    
    print(f"\n✨ Generated {len(captions)} RAG-based captions using retrieval from {len(generator.documents)} coffee articles!")

if __name__ == "__main__":
    main()
