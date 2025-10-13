import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import hashlib
import requests
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from platform_strategies import PlatformStrategy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration - use environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

class LLMRAGCaptionGenerator:
    def __init__(self, ollama_model="phi3:mini", ollama_url="http://localhost:11434", brand_id=None):
        """Initialize LLM + RAG Caption Generator with Ollama"""
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.use_ollama = self.check_ollama_connection()
        
        if not self.use_ollama:
            logger.warning("Ollama not available. Using local fallback generation.")
        
        # Brand profile context (loaded dynamically)
        self.brand_profile = None
        self.brand_voice_adjectives = []
        self.brand_lexicon_always = []
        self.brand_lexicon_never = []
        self.brand_name = "Coffee Brand"  # Default fallback
        self.brand_guardrails = {}
        self.brand_image_style = "Professional coffee photography with natural lighting"  # Default
        
        self.load_trending_keywords()
        self.setup_database_connection()
        
        # CRITICAL FIX: Load brand profile before generating content
        self.load_brand_profile(brand_id)
        
        self.load_fresh_content()
        self.setup_vectorizer()
        self.caption_history = set()  # Track generated captions to avoid duplicates
        self.image_prompt_history = set()  # Track generated image prompts to avoid duplicates
        
        # NEW: Initialize hashtag RAG system and image prompt generation
        self.load_hashtag_knowledge_base()
        self.setup_hashtag_vectorizer()
        self.load_visual_context_database()
        
        # Initialize platform strategy
        self.platform_strategy = PlatformStrategy()
        logger.info("Platform strategy initialized")
        
    def generate_coffee_knowledge(self, keyword: str) -> Dict[str, Any]:
        """Generate comprehensive coffee knowledge dynamically using LLM"""
        if not self.use_ollama:
            # Fallback to basic knowledge structure
            return self.get_manual_knowledge(keyword)
        
        try:
            # Simplified, more direct prompt
            prompt = f"""You are a coffee expert. Describe {keyword} in exactly this format:

COLOR: [one specific color word]
NATURE: [what it is in 3-5 words]
TEXTURE: [texture in 3-5 words]  
FLAVOR_PROFILE: [3 flavor words, comma separated]
PREPARATION: [how made in 3-5 words]
VISUAL_TRAITS: [3 visual traits, comma separated]
MOOD: [2 moods, comma separated]

Example for matcha:
COLOR: vibrant green
NATURE: powdered Japanese green tea
TEXTURE: fine powder becomes frothy
FLAVOR_PROFILE: earthy, grassy, umami
PREPARATION: whisked with hot water
VISUAL_TRAITS: bright green color, foam layer, ceramic bowl
MOOD: calm, focused

Now describe {keyword}:"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Very low for factual accuracy
                        "top_p": 0.9,
                        "num_predict": 300,
                        "num_ctx": 2048,
                        "stop": ["\n\n", "Example"]
                    }
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                knowledge_text = result.get('response', '').strip()
                
                logger.info(f"Raw LLM response for {keyword}: {knowledge_text[:200]}")
                
                # Parse the structured response
                knowledge = self.parse_coffee_knowledge(knowledge_text, keyword)
                
                # If parsing failed (generic values), use manual knowledge
                if knowledge.get('color') == 'rich brown' and keyword.lower() in ['matcha', 'matcha latte', 'matcha tea']:
                    logger.warning(f"LLM returned generic values for {keyword}, using manual knowledge")
                    return self.get_manual_knowledge(keyword)
                
                logger.info(f"✅ Generated knowledge for '{keyword}': color={knowledge.get('color')}, nature={knowledge.get('nature')}")
                return knowledge
            else:
                logger.warning(f"LLM API returned {response.status_code} for {keyword}, using manual knowledge")
                return self.get_manual_knowledge(keyword)
                
        except Exception as e:
            logger.error(f"Error generating coffee knowledge: {e}, using manual knowledge")
            return self.get_manual_knowledge(keyword)
    
    def get_manual_knowledge(self, keyword: str) -> Dict[str, Any]:
        """Provide accurate manual knowledge for common coffee types"""
        keyword_lower = keyword.lower()
        
        # Manual knowledge base for accurate coffee characteristics
        manual_knowledge = {
            'matcha': {
                'color': 'vibrant green',
                'nature': 'powdered Japanese green tea',
                'texture': 'fine powder, frothy when whisked',
                'flavor_profile': ['earthy', 'grassy', 'umami', 'slightly sweet'],
                'preparation': 'whisked with hot water or milk',
                'visual_traits': ['bright green color', 'foam layer', 'ceramic bowl', 'bamboo whisk'],
                'mood': ['calm', 'focused', 'zen'],
                'unique_traits': ['antioxidant rich', 'ceremonial Japanese tradition', 'natural energy boost']
            },
            'matcha latte': {
                'color': 'vibrant green',
                'nature': 'green tea powder with steamed milk',
                'texture': 'creamy, frothy, smooth',
                'flavor_profile': ['earthy', 'sweet', 'creamy', 'grassy'],
                'preparation': 'matcha whisked with steamed milk',
                'visual_traits': ['green layer', 'milk foam', 'latte art possible'],
                'mood': ['energizing', 'comforting'],
                'unique_traits': ['green color stands out', 'less caffeine than coffee', 'smooth taste']
            },
            'cold brew': {
                'color': 'dark brown',
                'nature': 'coffee steeped in cold water',
                'texture': 'smooth, rich, concentrated',
                'flavor_profile': ['smooth', 'sweet', 'low acidity', 'chocolatey'],
                'preparation': 'steeped 12-24 hours cold',
                'visual_traits': ['dark liquid', 'ice cubes', 'minimal foam'],
                'mood': ['refreshing', 'energizing'],
                'unique_traits': ['less acidic', 'naturally sweet', 'highly caffeinated']
            },
            'espresso': {
                'color': 'dark brown',
                'nature': 'concentrated coffee shot',
                'texture': 'thick, rich crema',
                'flavor_profile': ['intense', 'bold', 'slightly bitter', 'aromatic'],
                'preparation': 'high pressure extraction',
                'visual_traits': ['golden crema layer', 'small cup', 'thick consistency'],
                'mood': ['energizing', 'bold'],
                'unique_traits': ['crema on top', 'intense flavor', 'base for many drinks']
            },
            'latte': {
                'color': 'light brown',
                'nature': 'espresso with steamed milk',
                'texture': 'creamy, smooth, velvety',
                'flavor_profile': ['mild', 'creamy', 'smooth', 'slightly sweet'],
                'preparation': 'espresso plus steamed milk foam',
                'visual_traits': ['latte art', 'white foam', 'layered appearance'],
                'mood': ['comforting', 'smooth'],
                'unique_traits': ['foam art possible', 'milk forward', 'smooth taste']
            },
            'cappuccino': {
                'color': 'medium brown',
                'nature': 'espresso with foamed milk',
                'texture': 'thick foam, airy, light',
                'flavor_profile': ['strong', 'creamy', 'balanced', 'aromatic'],
                'preparation': 'espresso with thick foam layer',
                'visual_traits': ['thick foam cap', 'cocoa dust optional', 'distinct layers'],
                'mood': ['traditional', 'sophisticated'],
                'unique_traits': ['thick foam', 'stronger than latte', 'Italian classic']
            }
        }
        
        # Check for exact or partial matches
        for key, data in manual_knowledge.items():
            if key in keyword_lower:
                data['keyword'] = keyword
                return data
        
        # Default fallback for unknown coffee types
        return self.fallback_knowledge(keyword)
    
    def parse_coffee_knowledge(self, knowledge_text: str, keyword: str) -> Dict[str, Any]:
        """Parse LLM-generated knowledge into structured format"""
        knowledge = {'keyword': keyword}
        
        # Extract fields from the response
        lines = knowledge_text.split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                field = parts[0].strip().upper()
                value = parts[1].strip() if len(parts) > 1 else ''
                
                # Map fields to keys
                if 'COLOR' in field:
                    knowledge['color'] = value
                elif 'NATURE' in field:
                    knowledge['nature'] = value
                elif 'TEXTURE' in field:
                    knowledge['texture'] = value
                elif 'FLAVOR' in field:
                    # Split by commas and clean up
                    flavors = [f.strip() for f in value.split(',')]
                    knowledge['flavor_profile'] = flavors
                elif 'PREPARATION' in field:
                    knowledge['preparation'] = value
                elif 'VISUAL' in field:
                    # Split by commas
                    visuals = [v.strip() for v in value.split(',')]
                    knowledge['visual_traits'] = visuals
                elif 'CULTURAL' in field or 'CONTEXT' in field:
                    knowledge['cultural_context'] = value
                elif 'MOOD' in field:
                    moods = [m.strip() for m in value.split(',')]
                    knowledge['mood'] = moods
                elif 'UNIQUE' in field or 'TRAIT' in field:
                    traits = [t.strip() for t in value.split(',')]
                    knowledge['unique_traits'] = traits
        
        # Ensure all required fields exist
        if 'color' not in knowledge:
            knowledge['color'] = 'rich brown'
        if 'nature' not in knowledge:
            knowledge['nature'] = f'{keyword} coffee'
        if 'visual_traits' not in knowledge:
            knowledge['visual_traits'] = ['coffee cup', 'aromatic']
        
        return knowledge
    
    def fallback_knowledge(self, keyword: str) -> Dict[str, Any]:
        """Provide fallback knowledge when LLM generation fails"""
        return {
            'keyword': keyword,
            'color': 'rich brown',
            'nature': f'{keyword} coffee beverage',
            'texture': 'smooth liquid',
            'flavor_profile': ['rich', 'aromatic', 'flavorful'],
            'preparation': 'brewed',
            'visual_traits': ['coffee cup', 'steam rising', 'aromatic'],
            'mood': ['energizing', 'comforting'],
            'unique_traits': ['flavorful', 'aromatic']
        }
    
    def setup_database_connection(self):
        """Setup database connection"""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to database for fresh content")
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            self.connection = None
    
    def load_brand_profile(self, brand_id: int = None):
        """Load brand profile from database and configure caption generator"""
        if not self.connection:
            logger.warning("No database connection. Using default brand settings.")
            return
        
        try:
            # First, ensure we're not in an aborted transaction state
            try:
                self.connection.rollback()
            except:
                pass
            
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            if brand_id:
                # Load specific brand by ID
                cursor.execute("SELECT * FROM brand_profiles WHERE id = %s", (brand_id,))
            else:
                # Load active brand
                cursor.execute("SELECT * FROM brand_profiles WHERE is_active = true LIMIT 1")
            
            brand = cursor.fetchone()
            cursor.close()
            
            if brand:
                self.brand_profile = dict(brand)
                self.brand_name = brand['brand_name']
                
                # Load voice profile
                voice_profile = brand.get('voice_profile', {})
                if isinstance(voice_profile, str):
                    voice_profile = json.loads(voice_profile)
                
                self.brand_voice_adjectives = voice_profile.get('core_adjectives', [])
                self.brand_lexicon_always = voice_profile.get('lexicon_always_use', [])
                self.brand_lexicon_never = voice_profile.get('lexicon_never_use', [])
                
                # Load guardrails
                guardrails = brand.get('guardrails', {})
                if isinstance(guardrails, str):
                    guardrails = json.loads(guardrails)
                self.brand_guardrails = guardrails
                
                # Load image style from guardrails
                self.brand_image_style = guardrails.get('image_style', 'Professional coffee photography with natural lighting')
                
                logger.info(f"✅ Loaded brand profile: {self.brand_name}")
                logger.info(f"   Voice adjectives: {', '.join(self.brand_voice_adjectives[:3])}")
                logger.info(f"   Always use: {', '.join(self.brand_lexicon_always[:3])}")
                logger.info(f"   Never use: {', '.join(self.brand_lexicon_never[:3])}")
                logger.info(f"   Image style: {self.brand_image_style[:50]}...")
            else:
                logger.warning("No brand profile found. Using default settings.")
                
        except Exception as e:
            logger.error(f"Error loading brand profile: {e}")
            logger.warning("Using default brand settings.")
    
    def load_trending_keywords(self):
        """Load trending keywords"""
        try:
            with open('trending_coffee_keywords.json', 'r') as f:
                trending_data = json.load(f)
                self.trending_keywords = trending_data['trending_keywords']
            logger.info(f"Loaded {len(self.trending_keywords)} trending keywords")
        except Exception as e:
            logger.error(f"Error loading trending keywords: {e}")
            self.trending_keywords = []
    
    def load_fresh_content(self):
        """Load fresh content from all sources"""
        self.documents = []
        self.document_metadata = []
        
        # Load original coffee articles
        self.load_coffee_articles()
        
        # Load fresh Reddit content
        self.load_reddit_content()
        
        # Load fresh Twitter content
        self.load_twitter_content()
        
        # Load fresh blog content
        self.load_blog_content()
        
        logger.info(f"Total documents loaded: {len(self.documents)}")
    
    def load_coffee_articles(self):
        """Load original coffee articles"""
        try:
            df = pd.read_csv('coffee_articles.csv')
            for _, row in df.iterrows():
                content = str(row.get('content', '')) + ' ' + str(row.get('title', ''))
                if len(content.strip()) > 50:
                    self.documents.append(content)
                    self.document_metadata.append({
                        'source': 'coffee_articles',
                        'type': 'article',
                        'freshness_score': 0.5,
                        'date': datetime.now() - timedelta(days=30)
                    })
            logger.info(f"Loaded {len(df)} original coffee articles")
        except Exception as e:
            logger.warning(f"Error loading coffee articles: {e}")
    
    def load_reddit_content(self):
        """Load fresh Reddit content from database"""
        if not self.connection:
            return
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT title, content, comments, score, created_utc, subreddit
                FROM reddit_data 
                WHERE scraped_at >= NOW() - INTERVAL '7 days'
                ORDER BY score DESC, scraped_at DESC
                LIMIT 300
            """)
            
            reddit_posts = cursor.fetchall()
            
            for post in reddit_posts:
                content_parts = [post['title'] or '']
                
                if post['content']:
                    content_parts.append(post['content'])
                
                if post['comments']:
                    try:
                        comments = json.loads(post['comments'])
                        content_parts.extend(comments[:2])
                    except:
                        pass
                
                combined_content = ' '.join(content_parts)
                
                if len(combined_content.strip()) > 50:
                    self.documents.append(combined_content)
                    self.document_metadata.append({
                        'source': 'reddit',
                        'type': 'post',
                        'subreddit': post['subreddit'],
                        'score': post['score'] or 0,
                        'freshness_score': 1.0,
                        'date': datetime.fromtimestamp(post['created_utc']) if post['created_utc'] else datetime.now()
                    })
            
            logger.info(f"Loaded {len(reddit_posts)} Reddit posts")
            cursor.close()
            
        except Exception as e:
            logger.warning(f"Error loading Reddit content: {e}")
    
    def load_twitter_content(self):
        """Load fresh Twitter content from database"""
        if not self.connection:
            return
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT text, like_count, retweet_count, created_at
                FROM twitter_data 
                WHERE scraped_at >= NOW() - INTERVAL '3 days'
                AND language = 'en'
                ORDER BY (like_count + retweet_count) DESC, scraped_at DESC
                LIMIT 200
            """)
            
            tweets = cursor.fetchall()
            
            for tweet in tweets:
                if tweet['text'] and len(tweet['text'].strip()) > 30:
                    self.documents.append(tweet['text'])
                    self.document_metadata.append({
                        'source': 'twitter',
                        'type': 'tweet',
                        'engagement': (tweet['like_count'] or 0) + (tweet['retweet_count'] or 0),
                        'freshness_score': 1.0,
                        'date': tweet['created_at'] or datetime.now()
                    })
            
            logger.info(f"Loaded {len(tweets)} tweets")
            cursor.close()
            
        except Exception as e:
            logger.warning(f"Error loading Twitter content: {e}")
    
    def load_blog_content(self):
        """Load fresh blog content from database"""
        if not self.connection:
            return
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT title, content, source, categories
                FROM blog_articles 
                WHERE scraped_at >= NOW() - INTERVAL '14 days'
                ORDER BY scraped_at DESC
                LIMIT 150
            """)
            
            articles = cursor.fetchall()
            
            for article in articles:
                content = (article['title'] or '') + ' ' + (article['content'] or '')
                
                if len(content.strip()) > 100:
                    self.documents.append(content)
                    self.document_metadata.append({
                        'source': f"blog_{article['source']}",
                        'type': 'blog_article',
                        'categories': article['categories'],
                        'freshness_score': 0.9,
                        'date': datetime.now()
                    })
            
            logger.info(f"Loaded {len(articles)} blog articles")
            cursor.close()
            
        except Exception as e:
            logger.warning(f"Error loading blog content: {e}")
    
    def setup_vectorizer(self):
        """Setup TF-IDF vectorizer"""
        self.vectorizer = TfidfVectorizer(
            max_features=2000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True,
            min_df=2,
            max_df=0.8
        )
        
        if self.documents:
            self.doc_vectors = self.vectorizer.fit_transform(self.documents)
            logger.info(f"Vectorized {len(self.documents)} documents")
        else:
            logger.warning("No documents to vectorize")
    
    def retrieve_relevant_context(self, keyword: str, top_k: int = 8) -> List[str]:
        """Enhanced RAG retrieval optimized for keyword-based queries"""
        if not hasattr(self, 'doc_vectors') or not self.documents:
            logger.warning("No vectorized documents available")
            return []
        
        # Expand keyword for better semantic matching with coffee content
        expanded_query = self.expand_keyword_for_search(keyword)
        logger.info(f"Expanded query from '{keyword}' to '{expanded_query}'")
        
        # Vectorize the expanded query
        query_vector = self.vectorizer.transform([expanded_query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, self.doc_vectors).flatten()
        
        # Apply freshness and engagement boosts
        boosted_scores = []
        for i, score in enumerate(similarity_scores):
            metadata = self.document_metadata[i]
            freshness_boost = metadata.get('freshness_score', 0.5)
            
            # Boost recent content
            days_old = (datetime.now() - metadata.get('date', datetime.now())).days
            recency_boost = max(0.2, 1 - (days_old / 30))
            
            # Boost high-engagement content
            engagement_boost = 1.0
            if metadata.get('source') == 'twitter':
                engagement = metadata.get('engagement', 0)
                engagement_boost = min(2.0, 1 + (engagement / 100))
            elif metadata.get('source') == 'reddit':
                score_val = metadata.get('score', 0)
                engagement_boost = min(2.0, 1 + (score_val / 50))
            
            final_score = score * freshness_boost * recency_boost * engagement_boost
            boosted_scores.append(final_score)
        
        # Always get the top documents regardless of threshold - this fixes the uniqueness issue
        top_indices = np.argsort(boosted_scores)[-top_k*2:][::-1]  # Get more candidates
        
        retrieved_contexts = []
        sources_used = set()
        
        for idx in top_indices:
            # Much lower threshold - accept any document with similarity > 0
            if boosted_scores[idx] >= 0:  # Always use actual content, never fallback to generic
                doc = self.documents[idx]
                source = self.document_metadata[idx].get('source', 'unknown')
                
                # Ensure source diversity - max 2 from same source
                source_count = len([s for s in sources_used if s == source])
                if source_count < 2:
                    snippets = self.extract_relevant_snippets(doc, keyword)
                    if snippets:
                        retrieved_contexts.extend(snippets[:2])  # Max 2 snippets per doc
                        sources_used.add(source)
                
                # Stop when we have enough diverse content
                if len(retrieved_contexts) >= 10:
                    break
        
        # If we somehow still have no content, take top documents anyway
        if not retrieved_contexts and self.documents:
            logger.warning(f"No content found for '{keyword}', using top documents")
            for idx in top_indices[:3]:
                doc = self.documents[idx]
                snippets = self.extract_relevant_snippets(doc, keyword)
                retrieved_contexts.extend(snippets[:1])
        
        logger.info(f"Retrieved {len(retrieved_contexts)} context snippets from {len(sources_used)} sources")
        return retrieved_contexts[:8] if retrieved_contexts else []

    def expand_keyword_for_search(self, keyword: str) -> str:
        """Expand keyword with coffee-related terms for better document retrieval"""
        # Map keywords to related coffee terms
        keyword_expansions = {
            'cold brew': 'cold brew iced coffee cold brewing concentrate smooth',
            'latte': 'latte milk coffee steamed foam cappuccino espresso',
            'espresso': 'espresso shot coffee strong italian caffeine crema',
            'matcha': 'matcha green tea powder japanese ceremonial grade whisked',
            'cappuccino': 'cappuccino espresso steamed milk foam coffee italian',
            'french press': 'french press plunger pot immersion brewing coffee',
            'pour over': 'pour over drip v60 chemex filter coffee brewing',
            'americano': 'americano espresso hot water black coffee',
            'macchiato': 'macchiato espresso milk spotted coffee',
            'mocha': 'mocha chocolate coffee espresso cocoa',
            'decaf': 'decaf decaffeinated caffeine free coffee',
            'specialty coffee': 'specialty artisan third wave single origin quality',
            'coffee beans': 'coffee beans roasted green arabica robusta origin',
            'barista': 'barista coffee professional brewing milk steaming art',
            'roast': 'roast roasting dark light medium coffee beans flavor'
        }
        
        # Find matching expansion
        expanded_terms = []
        for key, expansion in keyword_expansions.items():
            if key.lower() in keyword.lower():
                expanded_terms.append(expansion)
                break
        
        # Always add general coffee terms for broader matching
        general_terms = "coffee drink beverage taste flavor delicious amazing experience"
        
        # Combine original keyword with expansions
        if expanded_terms:
            return f"{keyword} {' '.join(expanded_terms)} {general_terms}"
        else:
            return f"{keyword} {general_terms}"
    
    def extract_relevant_snippets(self, document: str, keyword: str) -> List[str]:
        """Extract relevant snippets from document"""
        sentences = document.split('.')
        relevant_snippets = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                # Check if sentence is relevant to coffee or contains descriptive language
                if any(word in sentence.lower() for word in ['coffee', 'taste', 'flavor', 'aroma', 'brew', 'roast', 'bean', 'cup', 'drink', 'delicious', 'amazing', 'perfect', 'rich', 'smooth', 'bold']):
                    relevant_snippets.append(sentence)
        
        return relevant_snippets[:5]
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.ollama_model in model_names or any(self.ollama_model in name for name in model_names):
                    logger.info(f"✅ Ollama connected successfully with model: {self.ollama_model}")
                    return True
                else:
                    logger.warning(f"Model {self.ollama_model} not found. Available models: {model_names}")
                    # Try to find a suitable text generation model
                    text_gen_models = [name for name in model_names if any(gen_model in name.lower() for gen_model in ['llama', 'mistral', 'codellama', 'phi', 'gemma', 'qwen'])]
                    
                    if text_gen_models:
                        self.ollama_model = text_gen_models[0]
                        logger.info(f"Using available text generation model: {self.ollama_model}")
                        return True
                    elif model_names:
                        # Fallback to first available model
                        self.ollama_model = model_names[0]
                        logger.info(f"Using available model (may not be optimal for text generation): {self.ollama_model}")
                        return True
                    return False
            return False
        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}")
            return False
    
    def generate_llm_caption(self, keyword: str, context_snippets: List[str]) -> str:
        """Generate caption using LLM"""
        if self.use_ollama:
            return self.generate_ollama_caption(keyword, context_snippets)
        else:
            return self.generate_local_caption(keyword, context_snippets)
    
    def generate_ollama_caption(self, keyword: str, context_snippets: List[str], knowledge: Dict[str, Any] = None) -> str:
        """Generate caption using Ollama with brand voice and coffee knowledge"""
        try:
            # Prepare context - use more context for better generation
            context_text = " ".join(context_snippets[:2])[:200] if context_snippets else ""
            
            # Prepare knowledge context if available
            knowledge_text = ""
            if knowledge:
                color = knowledge.get('color', '')
                nature = knowledge.get('nature', '')
                flavors = ', '.join(knowledge.get('flavor_profile', [])[:3])
                mood = ', '.join(knowledge.get('mood', [])[:2])
                
                knowledge_text = f"""
Coffee Knowledge:
- Color: {color}
- Nature: {nature}
- Flavor Profile: {flavors}
- Mood: {mood}
"""
            
            # Build brand voice context
            brand_voice_text = ""
            if self.brand_voice_adjectives:
                brand_voice_text = f"\nBrand Voice Adjectives: {', '.join(self.brand_voice_adjectives[:5])}"
            
            lexicon_text = ""
            if self.brand_lexicon_always:
                lexicon_text += f"\nAlways use these terms when relevant: {', '.join(self.brand_lexicon_always[:5])}"
            if self.brand_lexicon_never:
                lexicon_text += f"\nNever use these terms: {', '.join(self.brand_lexicon_never[:5])}"
            
            # Create brand-aware prompt
            prompt = f"""Create a catchy social media caption about "{keyword}" for {self.brand_name}.

{knowledge_text}
{brand_voice_text}
{lexicon_text}

Brand Guidelines:
- Write in a tone that embodies: {', '.join(self.brand_voice_adjectives[:3]) if self.brand_voice_adjectives else 'professional, engaging, authentic'}
- Mention "{self.brand_name}" as the brand (NEVER mention other coffee brand names)
- Incorporate the coffee's actual characteristics (color, flavor, nature) into the caption
- Make it authentic and shareable

Context about coffee: {context_text}

Write a complete, engaging caption without emojis. Make it align with the brand voice and reflect the coffee's true nature:"""

            # Make request to Ollama with settings for complete captions
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,  # Reduced for more consistent output
                        "top_p": 0.9,
                        "num_predict": 250,  # Increased significantly for complete captions
                        "stop": ["\n\n", "Context:", "Here's another", "Next:"],  # Removed aggressive stops
                        "num_ctx": 2048,  # Larger context window
                        "repeat_penalty": 1.1
                    }
                },
                timeout=90  # Longer timeout for complete generation
            )
            
            if response.status_code == 200:
                result = response.json()
                caption = result.get('response', '').strip()
                
                # Clean up the caption
                caption = self.clean_generated_caption(caption)
                return caption
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self.generate_local_caption(keyword, context_snippets)
            
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return self.generate_local_caption(keyword, context_snippets)
    
    def clean_generated_caption(self, caption: str) -> str:
        """Clean up generated caption with aggressive attribution removal"""
        import re
        
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
    
    def extract_hashtags_from_content(self) -> List[str]:
        """Extract trending hashtags from social media content"""
        hashtags = set()
        
        # Extract hashtags from documents
        for doc in self.documents:
            # Find hashtags in the text
            import re
            found_hashtags = re.findall(r'#\w+', doc)
            hashtags.update([tag.lower() for tag in found_hashtags])
        
        # Add common coffee hashtags
        common_coffee_hashtags = [
            '#coffee', '#coffeelover', '#coffeeaddict', '#coffeetime', '#espresso',
            '#latte', '#cappuccino', '#barista', '#coffeeshop', '#coldbrewcoffee',
            '#specialtycoffee', '#coffeeculture', '#coffeeart', '#morningcoffee',
            '#coffeebreak', '#coffeegram', '#coffeelife', '#coffeelovers',
            '#matcha', '#matchalatte', '#coffeebeans', '#pourover', '#frenchpress'
        ]
        
        hashtags.update(common_coffee_hashtags)
        return list(hashtags)
    
    def generate_relevant_hashtags(self, keyword: str, context_snippets: List[str]) -> List[str]:
        """Generate relevant hashtags for a keyword"""
        # Get all available hashtags
        all_hashtags = self.extract_hashtags_from_content()
        
        # Keyword-specific hashtag mapping
        keyword_hashtags = {
            'cold brew': ['#coldbrew', '#coldbrewcoffee', '#icedcoffee'],
            'latte': ['#latte', '#latteart', '#coffeeart', '#milkcoffee'],
            'espresso': ['#espresso', '#espressoshot', '#strongcoffee'],
            'matcha': ['#matcha', '#matchalatte', '#greentea', '#matcharecipes'],
            'specialty coffee': ['#specialtycoffee', '#thirdwavecoffee', '#artisancoffee'],
            'decaf': ['#decaf', '#decafcoffee', '#caffeinefree'],
            'cappuccino': ['#cappuccino', '#foamart', '#italianstyle'],
            'french press': ['#frenchpress', '#pressedcoffee', '#slowbrew'],
            'pour over': ['#pourover', '#v60', '#chemex', '#handbrewed']
        }
        
        # Start with keyword-specific hashtags
        selected_hashtags = []
        
        # Add keyword-specific hashtags
        for key, tags in keyword_hashtags.items():
            if key in keyword.lower():
                selected_hashtags.extend(tags)
        
        # Add general coffee hashtags
        general_tags = ['#coffee', '#coffeelover', '#coffeetime']
        selected_hashtags.extend(general_tags)
        
        # Add context-based hashtags
        if context_snippets:
            context_text = ' '.join(context_snippets).lower()
            if 'morning' in context_text:
                selected_hashtags.append('#morningcoffee')
            if 'barista' in context_text:
                selected_hashtags.append('#barista')
            if 'roast' in context_text:
                selected_hashtags.append('#coffeeroast')
            if 'bean' in context_text:
                selected_hashtags.append('#coffeebeans')
        
        # Remove duplicates and limit to 5 hashtags
        unique_hashtags = list(dict.fromkeys(selected_hashtags))
        return unique_hashtags[:5]
    
    def generate_local_caption(self, keyword: str, context_snippets: List[str]) -> str:
        """Generate caption using local logic (fallback) - NO TEMPLATES"""
        logger.warning("Using local fallback - LLM generation failed")
        
        # Extract descriptive words from context
        descriptors = []
        for snippet in context_snippets[:3]:
            words = snippet.lower().split()
            coffee_descriptors = [w for w in words if w in ['amazing', 'perfect', 'delicious', 'rich', 'smooth', 'bold', 'creamy', 'aromatic', 'incredible', 'outstanding', 'exceptional', 'wonderful', 'fantastic']]
            descriptors.extend(coffee_descriptors)
        
        if descriptors:
            descriptor = random.choice(descriptors)
        else:
            descriptor = random.choice(['amazing', 'incredible', 'perfect', 'exceptional'])
        
        # Generate more dynamic, varied captions without fixed templates
        emojis = ['☕', '✨', '🔥', '😍', '💯', '👀', '🤤', '🌟', '💫', '🎯']
        
        # Create more varied structures
        structures = [
            f"Discovering {keyword} has been {descriptor}",
            f"This {keyword} experience is absolutely {descriptor}",
            f"When {keyword} meets perfection",
            f"Obsessed with this {descriptor} {keyword}",
            f"Game-changing {keyword} moment",
            f"Pure {descriptor} {keyword} bliss"
        ]
        
        base_caption = random.choice(structures)
        emoji_combo = random.sample(emojis, 2)
        
        return f"{base_caption} {' '.join(emoji_combo)}"
    
    def intelligent_truncate(self, caption: str, max_chars: int) -> str:
        """Intelligently truncate caption without adding '...' - clean ending"""
        if len(caption) <= max_chars:
            return caption
        
        # Try to find the last complete sentence within the limit
        truncated = caption[:max_chars]
        
        # Look for sentence endings
        last_period = truncated.rfind('.')
        last_exclaim = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        sentence_end = max(last_period, last_exclaim, last_question)
        
        # If we have at least 60% of the content with a sentence ending, use it
        if sentence_end > max_chars * 0.6:
            return caption[:sentence_end + 1].strip()
        
        # Otherwise, truncate at word boundary without "..."
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.5:
            # Check if the last word before space ends with punctuation
            truncated_at_word = caption[:last_space].strip()
            if truncated_at_word and truncated_at_word[-1] not in '.!?,;:':
                # Add period for clean ending
                return truncated_at_word + '.'
            return truncated_at_word
        
        # Last resort: just cut at the limit and add period
        return truncated.strip() + '.'
    
    def clean_keyword(self, keyword: str) -> str:
        """Clean keyword for better readability"""
        prefixes_to_remove = ['what is ', 'how to make ', 'best ', 'how much caffeine in ', 'how to ']
        
        for prefix in prefixes_to_remove:
            if keyword.lower().startswith(prefix):
                keyword = keyword[len(prefix):]
        
        return keyword.strip()
    
    def generate_caption_hash(self, caption: str) -> str:
        """Generate hash for caption to track duplicates"""
        return hashlib.md5(caption.lower().encode()).hexdigest()
    
    def is_caption_unique(self, caption: str) -> bool:
        """Check if caption is unique"""
        caption_hash = self.generate_caption_hash(caption)
        return caption_hash not in self.caption_history
    
    def generate_unique_caption(self, keyword: str = None, max_attempts: int = 10) -> Dict[str, Any]:
        """Generate a unique caption using LLM + RAG with hashtags and dynamic knowledge"""
        attempts = 0
        
        while attempts < max_attempts:
            # Select keyword
            if not keyword:
                selected_keyword = random.choice(self.trending_keywords)
            else:
                selected_keyword = keyword
            
            selected_keyword = self.clean_keyword(selected_keyword)
            
            # STEP 1: Generate dynamic coffee knowledge (hidden from user)
            coffee_knowledge = self.generate_coffee_knowledge(selected_keyword)
            
            # STEP 2: Retrieve relevant context using RAG
            context_snippets = self.retrieve_relevant_context(selected_keyword)
            
            # STEP 3: Generate caption using LLM with knowledge
            base_caption = self.generate_ollama_caption(selected_keyword, context_snippets, coffee_knowledge) if self.use_ollama else self.generate_local_caption(selected_keyword, context_snippets)
            
            # STEP 4: Generate relevant hashtags
            hashtags = self.generate_relevant_hashtags(selected_keyword, context_snippets)
            
            # Combine caption with hashtags
            full_caption = f"{base_caption}\n\n{' '.join(hashtags)}"
            
            # Check uniqueness (using base caption for uniqueness check)
            if self.is_caption_unique(base_caption):
                # Add to history
                self.caption_history.add(self.generate_caption_hash(base_caption))
                
                return {
                    'caption': full_caption,
                    'base_caption': base_caption,
                    'hashtags': hashtags,
                    'keyword': selected_keyword,
                    'context_snippets': context_snippets[:5],
                    'coffee_knowledge': coffee_knowledge,  # Include knowledge in output (for debugging/reference)
                    'method': 'LLM + Dynamic Knowledge + RAG + Hashtags',
                    'timestamp': datetime.now().isoformat()
                }
            
            attempts += 1
        
        # If we can't generate unique caption, return anyway with warning
        logger.warning(f"Could not generate unique caption after {max_attempts} attempts")
        hashtags = self.generate_relevant_hashtags(selected_keyword, context_snippets)
        full_caption = f"{base_caption}\n\n{' '.join(hashtags)}"
        
        return {
            'caption': full_caption,
            'base_caption': base_caption,
            'hashtags': hashtags,
            'keyword': selected_keyword,
            'context_snippets': context_snippets[:3],
            'coffee_knowledge': coffee_knowledge,
            'method': 'LLM + Dynamic Knowledge + RAG + Hashtags (non-unique)',
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_multiple_captions(self, count: int = 10, keyword: str = None) -> List[Dict[str, Any]]:
        """Generate multiple unique captions"""
        captions = []
        
        for i in range(count):
            logger.info(f"Generating caption {i+1}/{count}")
            caption_data = self.generate_unique_caption(keyword)
            captions.append(caption_data)
        
        return captions
    
    def save_generated_captions(self, captions: List[Dict[str, Any]], filename: str = 'llm_rag_captions.json'):
        """Save generated captions to file"""
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_captions': len(captions),
            'method': 'LLM + RAG (Dynamic Generation)',
            'sources_used': ['coffee_articles', 'reddit', 'twitter', 'blogs'],
            'total_documents': len(self.documents),
            'llm_used': f'Ollama ({self.ollama_model})' if self.use_ollama else 'Local Fallback',
            'captions': captions
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"✅ Saved {len(captions)} LLM+RAG captions to {filename}")

    # NEW: Hashtag RAG System
    def load_hashtag_knowledge_base(self):
        """Load hashtag knowledge base for RAG selection"""
        try:
            with open('coffee_hashtag_knowledge_base.json', 'r') as f:
                data = json.load(f)
                self.hashtag_data = data['hashtags']
            
            # Prepare hashtag documents for RAG
            self.hashtag_documents = []
            self.hashtag_metadata = []
            
            for entry in self.hashtag_data:
                # Use content as document for similarity search
                self.hashtag_documents.append(entry['content'])
                self.hashtag_metadata.append({
                    'hashtag': entry['hashtag'],
                    'keyword': entry['metadata']['keyword'],
                    'popularity_score': entry['metadata']['popularity_score'],
                    'relevance_score': entry['metadata']['relevance_score'],
                    'source': entry['metadata']['source']
                })
            
            logger.info(f"Loaded hashtag knowledge base: {len(self.hashtag_data)} hashtags")
            
        except Exception as e:
            logger.warning(f"Could not load hashtag knowledge base: {e}")
            self.hashtag_data = []
            self.hashtag_documents = []
            self.hashtag_metadata = []

    def setup_hashtag_vectorizer(self):
        """Setup vectorizer for hashtag RAG system"""
        if self.hashtag_documents:
            self.hashtag_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True,
                min_df=1
            )
            
            try:
                self.hashtag_vectors = self.hashtag_vectorizer.fit_transform(self.hashtag_documents)
                logger.info(f"Vectorized {len(self.hashtag_documents)} hashtag documents")
            except Exception as e:
                logger.warning(f"Could not vectorize hashtag documents: {e}")
                self.hashtag_vectors = None
        else:
            self.hashtag_vectorizer = None
            self.hashtag_vectors = None

    def select_hashtags_with_rag(self, caption: str, keyword: str, top_k: int = 5) -> List[str]:
        """Use RAG to select most relevant hashtags with proper deduplication"""
        if not hasattr(self, 'hashtag_vectors') or self.hashtag_vectors is None:
            # Fallback to original method
            hashtags = self.generate_relevant_hashtags(keyword, [])
            return self.deduplicate_hashtags(hashtags)
        
        try:
            # Create query from caption and keyword
            query_text = f"{caption} {keyword}"
            query_vector = self.hashtag_vectorizer.transform([query_text])
            
            # Calculate similarity scores
            similarity_scores = cosine_similarity(query_vector, self.hashtag_vectors).flatten()
            
            # Boost scores based on hashtag popularity and relevance
            boosted_scores = []
            for i, score in enumerate(similarity_scores):
                metadata = self.hashtag_metadata[i]
                
                # Boost by popularity and relevance
                popularity_boost = metadata['popularity_score'] / 100.0
                relevance_boost = metadata['relevance_score']
                
                final_score = score + (popularity_boost * 0.3) + (relevance_boost * 0.2)
                boosted_scores.append(final_score)
            
            # Get top hashtags with improved threshold
            top_indices = np.argsort(boosted_scores)[-top_k*2:][::-1]  # Get more candidates
            
            selected_hashtags = []
            seen_hashtags = set()  # Track seen hashtags for deduplication
            
            for idx in top_indices:
                if boosted_scores[idx] > 0.3:  # Increased threshold for better quality
                    hashtag = self.hashtag_metadata[idx]['hashtag']
                    
                    # Avoid duplicates
                    if hashtag.lower() not in seen_hashtags:
                        selected_hashtags.append(hashtag)
                        seen_hashtags.add(hashtag.lower())
                    
                    # Stop when we have enough unique hashtags
                    if len(selected_hashtags) >= top_k:
                        break
            
            # Ensure we have some hashtags
            if not selected_hashtags:
                selected_hashtags = ['#coffee', '#coffeelover', '#coffeetime']
            
            # Always include core coffee hashtag if not present
            if not any('#coffee' == tag.lower() for tag in selected_hashtags):
                # Remove last hashtag if at capacity and add #coffee
                if len(selected_hashtags) >= top_k:
                    selected_hashtags = selected_hashtags[:-1]
                selected_hashtags.insert(0, '#coffee')
            
            # Final deduplication
            return self.deduplicate_hashtags(selected_hashtags[:5])
            
        except Exception as e:
            logger.warning(f"Error in hashtag RAG selection: {e}")
            hashtags = self.generate_relevant_hashtags(keyword, [])
            return self.deduplicate_hashtags(hashtags)

    def deduplicate_hashtags(self, hashtags: List[str]) -> List[str]:
        """Remove duplicate hashtags while preserving order"""
        seen = set()
        unique_hashtags = []
        
        for hashtag in hashtags:
            hashtag_lower = hashtag.lower()
            if hashtag_lower not in seen:
                unique_hashtags.append(hashtag)
                seen.add(hashtag_lower)
        
        return unique_hashtags

    # NEW: Visual Context and Image Prompt Generation
    def load_visual_context_database(self):
        """Initialize dynamic visual context generation - no more predetermined data!"""
        # No static database - everything will be generated dynamically by LLM
        self.visual_context_db = None
        logger.info("Visual context will be generated dynamically by LLM")

    def generate_image_prompt(self, caption_data: Dict[str, Any]) -> str:
        """Generate unique, creative image prompt using LLM with coffee knowledge"""
        keyword = caption_data['keyword']
        caption = caption_data['base_caption']
        context_snippets = caption_data.get('context_snippets', [])
        knowledge = caption_data.get('coffee_knowledge', None)
        
        # Use LLM to generate unique image prompts with knowledge
        if self.use_ollama:
            return self.generate_ollama_image_prompt(keyword, caption, context_snippets, knowledge)
        else:
            return self.generate_local_image_prompt(keyword, caption, context_snippets)

    def generate_ollama_image_prompt(self, keyword: str, caption: str, context_snippets: List[str], knowledge: Dict[str, Any] = None) -> str:
        """Generate brand-aware image prompt using brand profile and guardrails"""
        try:
            # Extract knowledge attributes if available
            color = "rich brown"
            texture = "smooth"
            visual_traits = []
            
            if knowledge:
                color = knowledge.get('color', 'rich brown')
                texture = knowledge.get('texture', 'smooth')
                visual_traits = knowledge.get('visual_traits', [])
            
            # Use brand image style from guardrails - THIS IS CRITICAL
            brand_style_guide = self.brand_image_style
            
            # Build STRONGLY brand-aware prompt with explicit requirements
            prompt = f"""You MUST create an image description that follows the EXACT brand style guidelines.

MANDATORY Brand Image Style: {brand_style_guide}

Product to Show: {keyword}
Product Color: {color}
Product Texture: {texture}
Visual Elements: {', '.join(visual_traits) if visual_traits else 'appealing presentation'}

CRITICAL REQUIREMENTS:
1. MUST follow the brand style: "{brand_style_guide}"
2. The main subject is {keyword} - NOT a generic coffee cup
3. MUST incorporate the specified visual style from brand guidelines
4. Use the actual product characteristics (color: {color}, texture: {texture})
5. Create a cohesive image matching the brand identity

Write ONLY a direct image description (2-3 sentences) that strictly follows the brand style guidelines above:"""

            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "top_p": 0.9,
                        "num_predict": 300,
                        "stop": ["\n\n", "Brand:", "Caption:"],
                        "num_ctx": 2048,
                        "repeat_penalty": 1.2
                    }
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                image_prompt = result.get('response', '').strip()
                
                # Clean up the prompt
                image_prompt = self.clean_image_prompt(image_prompt)
                
                # Ensure we got a good prompt
                if len(image_prompt) < 50:
                    logger.warning("LLM generated short image prompt, using local fallback")
                    return self.generate_local_image_prompt(keyword, caption, [])
                
                return image_prompt
            else:
                logger.error(f"Ollama API error for image prompt: {response.status_code}")
                return self.generate_local_image_prompt(keyword, caption, [])
            
        except Exception as e:
            logger.error(f"Ollama image prompt generation error: {e}")
            return self.generate_local_image_prompt(keyword, caption, [])
    
    def clean_image_prompt(self, prompt: str) -> str:
        """Clean up generated image prompt for direct use with image generation LLMs"""
        # Remove meta-text patterns and unwanted elements
        unwanted_patterns = [
            "Here's a unique image prompt:",
            "Image prompt:",
            "Photography prompt:",
            "Here's a creative prompt:",
            "Creative image prompt:",
            "Visual Description Prompt",
            "Caption Mood Description",
            "Title of Image Prompt",
            "Coffee Type Focus",
            "Caption Mood Reflection",
            "Prompt Visual Descri",
            "Caption (for a blog post):",
            "Caption Idea",
            "Original Setting/Location:",
            "Caption Mood (to use as backdrop):",
            "Scene Setup Idea",
            "Composition Angle in",
            "Visual Descri"
        ]
        
        # Remove unwanted patterns and their associated text
        for pattern in unwanted_patterns:
            if pattern.lower() in prompt.lower():
                # Split by sentences and remove those containing unwanted patterns
                sentences = prompt.split('.')
                cleaned_sentences = []
                for sentence in sentences:
                    if pattern.lower() not in sentence.lower():
                        cleaned_sentences.append(sentence)
                prompt = '. '.join(cleaned_sentences).strip()
        
        # Remove numbered labels like "#957", "Scene 1:", etc.
        import re
        prompt = re.sub(r'#\d+\s*-\s*', '', prompt)
        prompt = re.sub(r'Scene \d+:', '', prompt)
        prompt = re.sub(r'Caption \d+:', '', prompt)
        
        # Remove colons and dashes at the start
        prompt = re.sub(r'^[:\-\s]+', '', prompt)
        
        # Remove quotes if wrapped
        if (prompt.startswith('"') and prompt.endswith('"')) or (prompt.startswith("'") and prompt.endswith("'")):
            prompt = prompt[1:-1].strip()
        
        # Remove parenthetical explanations
        prompt = re.sub(r'\([^)]*\)', '', prompt)
        
        # Clean up extra spaces and line breaks
        prompt = ' '.join(prompt.split())
        prompt = prompt.replace('  ', ' ').replace(' .', '.').replace('..', '.')
        
        # Remove trailing incomplete sentences
        if prompt.endswith('...') or prompt.endswith('..'):
            # Find the last complete sentence
            sentences = prompt.split('.')
            if len(sentences) > 1:
                # Keep all but the last incomplete sentence
                prompt = '. '.join(sentences[:-1]) + '.'
        
        # Ensure it starts with a capital letter and is properly formatted
        if prompt and prompt[0].islower():
            prompt = prompt[0].upper() + prompt[1:]
        
        # Ensure reasonable length for image generation
        if len(prompt) > 400:
            # Find a good breaking point
            words = prompt.split()
            if len(words) > 50:
                prompt = ' '.join(words[:50])
                if not prompt.endswith('.'):
                    prompt += '.'
        
        return prompt.strip()

    def generate_local_image_prompt(self, keyword: str, caption: str, context_snippets: List[str]) -> str:
        """Generate brand-aware image prompt using brand style from guardrails"""
        logger.warning("Using local fallback for image prompt generation")
        
        # Use brand image style as base
        base_style = self.brand_image_style
        
        # Build simple, brand-aware prompt
        prompt = f"Professional product photography of {keyword}. {base_style}. Natural lighting, appealing composition, suitable for social media."
        
        return prompt

    def generate_complete_post(self, keyword: str = None, platform: str = 'instagram', scenario: str = None) -> Dict[str, Any]:
        """Generate complete social media post with platform-specific caption, hashtags, and image prompt"""
        
        logger.info(f"Generating post for platform: {platform}, scenario: {scenario}")
        
        # Get platform specifications
        platform_spec = self.platform_strategy.get_platform_spec(platform)
        
        # Step 1: Generate caption with platform-specific requirements and scenario
        caption_data = self.generate_platform_specific_caption(keyword, platform, platform_spec, scenario)
        
        # Step 2: Use hashtag RAG to select better hashtags
        rag_hashtags = self.select_hashtags_with_rag(
            caption_data['base_caption'], 
            caption_data['keyword']
        )
        
        # Step 3: Format hashtags for the platform
        platform_hashtags = self.platform_strategy.format_hashtags_for_platform(
            rag_hashtags, 
            platform
        )
        
        # Step 4: Apply platform-specific formatting to caption
        formatted_caption = self.platform_strategy.apply_platform_formatting(
            caption_data['base_caption'],
            platform
        )
        
        # Step 5: Validate and adjust caption length if needed
        validation = self.platform_strategy.validate_caption_length(formatted_caption, platform)
        if not validation['valid'] and validation['needs_truncation']:
            formatted_caption = self.platform_strategy.truncate_caption(formatted_caption, platform)
            logger.info(f"Caption truncated for {platform}: {validation['char_count']} -> {len(formatted_caption)} chars")
        
        # Step 6: Generate image prompt
        image_prompt = self.generate_image_prompt(caption_data)
        
        # Step 7: Combine everything
        complete_post = {
            'caption': formatted_caption,
            'hashtags': platform_hashtags.split(),
            'full_caption': f"{formatted_caption}\n\n{platform_hashtags}",
            'image_prompt': image_prompt,
            'keyword': caption_data['keyword'],
            'context_snippets': caption_data['context_snippets'],
            'visual_style': self.detect_visual_style(caption_data['base_caption']),
            'generation_method': f'LLM + Content RAG + Hashtag RAG + Platform Strategy ({platform})',
            'platform': platform,
            'platform_specs': {
                'char_range': f"{platform_spec['min_chars']}-{platform_spec['max_chars']}",
                'tone': platform_spec['tone_style'],
                'emoji_usage': platform_spec['emoji_usage']
            },
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'content_sources': len(self.documents),
                'hashtag_knowledge': len(self.hashtag_data),
                'llm_model': self.ollama_model if self.use_ollama else 'Local Fallback',
                'validation': validation
            }
        }
        
        return complete_post
    
    def generate_platform_specific_caption(self, keyword: str, platform: str, platform_spec: Dict[str, Any], scenario: str = None) -> Dict[str, Any]:
        """Generate caption tailored to platform specifications with optional scenario context"""
        
        # Simple logic: use provided keyword, or fall back to random trending keyword
        if keyword:
            selected_keyword = keyword
        else:
            selected_keyword = random.choice(self.trending_keywords)
        
        selected_keyword = self.clean_keyword(selected_keyword)
        
        # Generate dynamic coffee knowledge
        coffee_knowledge = self.generate_coffee_knowledge(selected_keyword)
        
        # Retrieve relevant context using RAG
        context_snippets = self.retrieve_relevant_context(selected_keyword)
        
        # Generate caption using platform-specific prompt with scenario
        if self.use_ollama:
            base_caption = self.generate_platform_aware_caption_ollama(
                selected_keyword, 
                context_snippets, 
                coffee_knowledge,
                platform,
                platform_spec,
                scenario
            )
        else:
            base_caption = self.generate_local_caption(selected_keyword, context_snippets)
        
        # Add to caption history
        self.caption_history.add(self.generate_caption_hash(base_caption))
        
        return {
            'base_caption': base_caption,
            'keyword': selected_keyword,
            'context_snippets': context_snippets[:5],
            'coffee_knowledge': coffee_knowledge
        }
    
    def generate_platform_aware_caption_ollama(
        self, 
        keyword: str, 
        context_snippets: List[str], 
        knowledge: Dict[str, Any],
        platform: str,
        platform_spec: Dict[str, Any],
        scenario: str = None
    ) -> str:
        """Generate platform-aware caption using Ollama with platform specifications and optional scenario"""
        max_retries = 3
        
        # Dynamic num_predict based on platform character limits
        max_chars = platform_spec['max_chars']
        min_chars = platform_spec['min_chars']
        
        # Calculate appropriate num_predict (roughly 1 token = 4 characters)
        # Add buffer for safety
        num_predict = min(200, int((max_chars * 0.8) / 4))
        
        for attempt in range(max_retries):
            try:
                # If scenario is provided, build a completely different prompt focused on the scenario
                if scenario:
                    # Extract key scenario elements for validation
                    scenario_keywords = self.extract_scenario_keywords(scenario)
                    
                    # Build increasingly aggressive prompts on retries
                    if attempt == 0:
                        prompt = self.build_scenario_prompt_level1(scenario, keyword, platform, platform_spec)
                    elif attempt == 1:
                        prompt = self.build_scenario_prompt_level2(scenario, keyword, platform, platform_spec, scenario_keywords)
                    else:
                        prompt = self.build_scenario_prompt_level3(scenario, keyword, platform, platform_spec, scenario_keywords)
                    
                    # Use lower temperature for scenario-based generation
                    temperature = 0.3
                    repeat_penalty = 1.3
                else:
                    # Use platform strategy to build the normal prompt with STRONG character limit emphasis
                    brand_voice = {
                        'core_adjectives': self.brand_voice_adjectives,
                        'lexicon_always_use': self.brand_lexicon_always,
                        'lexicon_never_use': self.brand_lexicon_never
                    }
                    
                    prompt = self.platform_strategy.build_platform_prompt(
                        platform,
                        brand_voice,
                        keyword,
                        context_snippets
                    )
                    
                    # Add coffee knowledge context
                    if knowledge:
                        knowledge_text = f"""
Coffee Details:
- Color: {knowledge.get('color', '')}
- Nature: {knowledge.get('nature', '')}
- Flavor: {', '.join(knowledge.get('flavor_profile', [])[:3])}

"""
                        prompt = prompt.replace('CONTEXT:', f'{knowledge_text}CONTEXT:')
                    
                    # CRITICAL: Add explicit character limit enforcement
                    char_limit_reminder = f"""

⚠️ CRITICAL CHARACTER LIMIT: {min_chars}-{max_chars} characters MAXIMUM
- Current attempt: {attempt + 1}/{max_retries}
- You have EXACTLY {max_chars} characters available
- Write a COMPLETE sentence that ENDS within {max_chars} characters
- DO NOT exceed {max_chars} characters or the caption will be cut off
- Count your characters carefully as you write
"""
                    prompt += char_limit_reminder
                    
                    # Use normal temperature for non-scenario generation
                    temperature = 0.7
                    repeat_penalty = 1.1
                    scenario_keywords = []
                
                # Make request to Ollama with dynamic num_predict
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "top_p": 0.9,
                            "num_predict": num_predict,  # Dynamic based on platform
                            "stop": ["\n\n", "Context:", "Hashtags:", "Example:", "⚠️"],
                            "num_ctx": 2048,
                            "repeat_penalty": repeat_penalty
                        }
                    },
                    timeout=90
                )
                
                if response.status_code == 200:
                    result = response.json()
                    caption = result.get('response', '').strip()
                    caption = self.clean_generated_caption(caption)
                    
                    # Validate scenario compliance if scenario was provided
                    if scenario and scenario_keywords:
                        validation_passed, missing_keywords = self.validate_scenario_compliance(caption, scenario_keywords)
                        
                        if not validation_passed:
                            logger.warning(f"Attempt {attempt + 1}: Caption missing scenario keywords: {missing_keywords}")
                            if attempt < max_retries - 1:
                                continue  # Retry with stronger prompt
                            else:
                                logger.error(f"Failed to generate scenario-compliant caption after {max_retries} attempts")
                                # Force include missing keywords
                                caption = self.force_scenario_compliance(caption, scenario_keywords, missing_keywords)
                    
                    # CRITICAL: Validate caption length and regenerate if needed
                    caption_length = len(caption)
                    
                    if caption_length > max_chars:
                        logger.warning(f"Attempt {attempt + 1}: Caption too long ({caption_length} > {max_chars})")
                        
                        if attempt < max_retries - 1:
                            # Retry with even stricter prompt
                            logger.info(f"Regenerating with stricter character limit...")
                            continue
                        else:
                            # Last resort: truncate intelligently without "..."
                            logger.warning(f"Final attempt exceeded limit, truncating intelligently")
                            caption = self.intelligent_truncate(caption, max_chars)
                    
                    elif caption_length < min_chars:
                        logger.warning(f"Caption too short for {platform} ({caption_length} < {min_chars})")
                        
                        if attempt < max_retries - 1:
                            # Retry to get longer caption
                            continue
                        else:
                            # Extend caption slightly
                            caption = f"{caption} {self.brand_name}"
                    
                    else:
                        # Caption is within limits - success!
                        logger.info(f"✅ Generated caption within limits: {caption_length} chars ({min_chars}-{max_chars})")
                        return caption
                    
                    return caption
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    if attempt == max_retries - 1:
                        return self.generate_local_caption(keyword, context_snippets)
                
            except Exception as e:
                logger.error(f"Ollama platform-aware generation error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return self.generate_local_caption(keyword, context_snippets)
        
        return self.generate_local_caption(keyword, context_snippets)
    
    def extract_scenario_keywords(self, scenario: str) -> List[str]:
        """Extract critical keywords from scenario for validation"""
        import re
        
        keywords = []
        
        # Extract discount percentages (e.g., "10% off", "20% discount")
        discount_matches = re.findall(r'\d+%\s*(?:off|discount)', scenario.lower())
        keywords.extend(discount_matches)
        
        # Extract product names (capitalized words, typically 2-4 words)
        # Look for patterns like "Italian Frogman Espresso"
        product_matches = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}', scenario)
        keywords.extend(product_matches)
        
        # Extract key promotional words
        promo_words = ['sale', 'offer', 'deal', 'promotion', 'launch', 'new', 'limited']
        for word in promo_words:
            if word in scenario.lower():
                keywords.append(word)
        
        return keywords
    
    def validate_scenario_compliance(self, caption: str, scenario_keywords: List[str]) -> tuple[bool, List[str]]:
        """Validate that caption includes critical scenario keywords"""
        caption_lower = caption.lower()
        missing_keywords = []
        
        for keyword in scenario_keywords:
            keyword_lower = keyword.lower()
            # For product names, check if all words appear (order doesn't matter)
            if ' ' in keyword:
                words = keyword_lower.split()
                if not all(word in caption_lower for word in words):
                    missing_keywords.append(keyword)
            else:
                if keyword_lower not in caption_lower:
                    missing_keywords.append(keyword)
        
        validation_passed = len(missing_keywords) == 0
        return validation_passed, missing_keywords
    
    def force_scenario_compliance(self, caption: str, all_keywords: List[str], missing_keywords: List[str]) -> str:
        """Force include missing scenario keywords in caption - AGGRESSIVE VERSION"""
        import re
        
        # Prioritize most important missing keywords (discounts and product names)
        important_missing = []
        
        for keyword in missing_keywords:
            # Include discounts (with %), product names (capitalized), and sale-related words
            if '%' in keyword or any(char.isupper() for char in keyword) or keyword.lower() in ['sale', 'offer', 'deal']:
                important_missing.append(keyword)
        
        if important_missing:
            # More aggressive approach: rebuild caption with scenario at the start
            # Remove any existing promotional fluff
            caption_clean = re.sub(r'^(Get ready to|Indulge in|Enjoy|Experience|Discover)\s+', '', caption, flags=re.IGNORECASE)
            
            # Build strong promotional prefix with all missing elements
            if any('%' in kw for kw in important_missing):
                # Has discount
                discount = next((kw for kw in important_missing if '%' in kw), '')
                product = next((kw for kw in important_missing if any(c.isupper() for c in kw)), '')
                
                if discount and product:
                    # Perfect: we have both discount and product name
                    forced_caption = f"🔥 SALE! {discount} on {product}! {caption_clean}"
                elif discount:
                    forced_caption = f"🔥 SALE! {discount}! {caption_clean}"
                else:
                    forced_caption = f"{' '.join(important_missing)}! {caption_clean}"
            else:
                # No discount, just product name or other keywords
                forced_caption = f"{'🔥 ' if 'sale' in missing_keywords else ''}{' '.join(important_missing)}! {caption_clean}"
            
            logger.info(f"✅ FORCED scenario compliance: '{forced_caption[:100]}...'")
            return forced_caption
        
        return caption
    
    def build_scenario_prompt_level1(self, scenario: str, keyword: str, platform: str, platform_spec: Dict[str, Any]) -> str:
        """Build first-level scenario prompt (polite but firm)"""
        return f"""⚠️ CRITICAL SCENARIO REQUIREMENT ⚠️

SCENARIO TO FOLLOW: "{scenario}"

Create a social media caption for {keyword} that DIRECTLY addresses this scenario.

MANDATORY REQUIREMENTS:
1. If the scenario mentions a discount (e.g., "10% off"), YOU MUST include it prominently
2. If the scenario mentions a specific product name, use that EXACT name
3. Match the scenario tone: Sale = promotional/urgent, Launch = exciting/new
4. The scenario details must be in the caption, not just implied

Brand: {self.brand_name}
Platform: {platform} ({platform_spec['min_chars']}-{platform_spec['max_chars']} characters)
Voice: {', '.join(self.brand_voice_adjectives[:2]) if self.brand_voice_adjectives else 'engaging'}

Generate ONLY the caption (no explanations):"""
    
    def build_scenario_prompt_level2(self, scenario: str, keyword: str, platform: str, platform_spec: Dict[str, Any], keywords: List[str]) -> str:
        """Build second-level scenario prompt (more aggressive with examples)"""
        # Create example based on scenario
        example_caption = self.create_example_from_scenario(scenario, keyword)
        
        return f"""🚨 CRITICAL: YOU MUST FOLLOW THE SCENARIO EXACTLY 🚨

SCENARIO: "{scenario}"

REQUIRED KEYWORDS THAT MUST APPEAR:
{chr(10).join(f"✓ {kw}" for kw in keywords[:5])}

CORRECT EXAMPLE:
"{example_caption}"

WRONG (what NOT to do):
"Sip on Italy with our Espresso..." ❌ (missing scenario details)

YOUR TASK:
Create a caption for {keyword} following the EXACT scenario above.
Brand: {self.brand_name}

Generate caption with ALL required keywords:"""
    
    def build_scenario_prompt_level3(self, scenario: str, keyword: str, platform: str, platform_spec: Dict[str, Any], keywords: List[str]) -> str:
        """Build third-level scenario prompt (maximum aggression)"""
        keyword_list = ", ".join(keywords[:5])
        
        return f"""FINAL WARNING - FOLLOW INSTRUCTIONS OR FAIL

SCENARIO (MUST BE IN CAPTION): "{scenario}"

YOU MUST INCLUDE THESE EXACT WORDS:
{keyword_list}

Template to follow:
[DISCOUNT/OFFER] for [PRODUCT NAME]! [Additional appeal]. Brand: {self.brand_name}

Generate caption NOW with ALL required elements:"""
    
    def create_example_from_scenario(self, scenario: str, keyword: str) -> str:
        """Create a concrete example caption from scenario"""
        scenario_lower = scenario.lower()
        
        # Extract discount if present
        import re
        discount_match = re.search(r'(\d+%\s*(?:off|discount))', scenario_lower)
        discount = discount_match.group(1) if discount_match else ""
        
        # Extract product name
        product_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', scenario)
        product = product_match.group(1) if product_match else keyword
        
        # Build example
        if discount and 'sale' in scenario_lower:
            return f"🔥 Sale! {discount} on {product}! Limited time offer from {self.brand_name}. Don't miss out!"
        elif 'launch' in scenario_lower or 'new' in scenario_lower:
            return f"Introducing {product}! Now available from {self.brand_name}. Experience the difference!"
        else:
            return f"{product} - {discount if discount else 'Special offer'} from {self.brand_name}!"

    def detect_visual_style(self, caption: str) -> str:
        """Detect appropriate visual style from caption"""
        caption_lower = caption.lower()
        
        if any(word in caption_lower for word in ['amazing', 'incredible', 'perfect', 'exceptional']):
            return 'artistic'
        elif any(word in caption_lower for word in ['cozy', 'warm', 'morning', 'traditional']):
            return 'rustic'
        elif any(word in caption_lower for word in ['modern', 'specialty', 'craft', 'artisan']):
            return 'modern_cafe'
        else:
            return 'minimalist'

    def generate_multiple_complete_posts(self, count: int = 5, keyword: str = None) -> List[Dict[str, Any]]:
        """Generate multiple complete posts"""
        complete_posts = []
        
        for i in range(count):
            logger.info(f"Generating complete post {i+1}/{count}")
            post_data = self.generate_complete_post(keyword)
            complete_posts.append(post_data)
        
        return complete_posts

    def save_complete_posts(self, posts: List[Dict[str, Any]], filename: str = 'complete_social_media_posts.json'):
        """Save complete posts to file"""
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_posts': len(posts),
            'generation_method': 'Complete Social Media Content Generation',
            'features': [
                'LLM Caption Generation',
                'Content RAG',
                'Hashtag RAG Selection',
                'Image Prompt Generation',
                'Visual Style Detection'
            ],
            'posts': posts
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"✅ Saved {len(posts)} complete posts to {filename}")

def main():
    """Demo the Enhanced LLM + RAG Complete Content Generator"""
    print("🤖 Enhanced LLM + RAG Complete Social Media Content Generator")
    print("=" * 60)
    print("Features: Caption + Hashtag RAG + Image Prompts")
    
    # Initialize generator
    generator = LLMRAGCaptionGenerator()
    
    print(f"\n📊 System Status:")
    print(f"   • Content Sources: {len(generator.documents)} documents")
    print(f"   • Hashtag Knowledge: {len(getattr(generator, 'hashtag_data', []))} hashtags")
    print(f"   • LLM Model: {generator.ollama_model if generator.use_ollama else 'Local Fallback'}")
    
    # Demo 1: Generate complete social media posts
    print("\n🎨 Generating Complete Social Media Posts:")
    print("-" * 40)
    
    complete_posts = generator.generate_multiple_complete_posts(3)
    
    for i, post in enumerate(complete_posts, 1):
        print(f"\n📱 Post {i}:")
        print(f"   Keyword: {post['keyword']}")
        print(f"   Caption: {post['caption']}")
        print(f"   Hashtags: {' '.join(post['hashtags'])}")
        print(f"   Visual Style: {post['visual_style']}")
        print(f"   Image Prompt: {post['image_prompt']}")
        print(f"   Method: {post['generation_method']}")
    
    # Save complete posts
    generator.save_complete_posts(complete_posts)
    
    # Demo 2: Show hashtag RAG in action
    print(f"\n🏷️  Hashtag RAG System Demo:")
    print("-" * 30)
    
    test_caption = "This cold brew experience is absolutely amazing"
    test_keyword = "cold brew"
    rag_hashtags = generator.select_hashtags_with_rag(test_caption, test_keyword)
    
    print(f"   Caption: '{test_caption}'")
    print(f"   Keyword: '{test_keyword}'")
    print(f"   RAG Selected Hashtags: {' '.join(rag_hashtags)}")
    
    # Demo 3: Show image prompt generation
    print(f"\n🖼️  Image Prompt Generation Demo:")
    print("-" * 35)
    
    sample_caption_data = {
        'keyword': 'vanilla oat milk latte',
        'base_caption': 'Pure vanilla oat milk latte bliss this morning'
    }
    
    image_prompt = generator.generate_image_prompt(sample_caption_data)
    visual_style = generator.detect_visual_style(sample_caption_data['base_caption'])
    
    print(f"   Keyword: {sample_caption_data['keyword']}")
    print(f"   Caption: {sample_caption_data['base_caption']}")
    print(f"   Visual Style: {visual_style}")
    print(f"   Image Prompt: {image_prompt}")
    
    # Summary
    print(f"\n✅ Demo Completed Successfully!")
    print(f"   • Generated {len(complete_posts)} complete posts")
    print(f"   • Used Content RAG from {len(generator.documents)} sources")
    print(f"   • Applied Hashtag RAG from {len(getattr(generator, 'hashtag_data', []))} hashtags")
    print(f"   • Created image prompts with visual context")
    print(f"   • Saved results to 'complete_social_media_posts.json'")

if __name__ == "__main__":
    main()
