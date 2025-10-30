"""
Brand Profile Management Module
Handles CRUD operations for brand profiles and LLM-powered suggestions
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import Dict, Any, List, Optional
import logging
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration - Try from environment first
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres')
}

# Only add password if it exists in environment
if os.getenv('DB_PASSWORD'):
    DB_CONFIG['password'] = os.getenv('DB_PASSWORD')

class BrandManager:
    def __init__(self, ollama_url="http://localhost:11434", ollama_model="phi3:mini"):
        """Initialize brand manager with database connection"""
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.connection = None
        self.connect_db()
    
    def connect_db(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            logger.info("Connected to brand profiles database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def create_brand(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new brand profile"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Extract data
            brand_name = brand_data.get('brand_name')
            brand_type = brand_data.get('brand_type')
            product_nature = brand_data.get('product_nature')
            industry = brand_data.get('industry')
            target_audience = brand_data.get('target_audience')
            content_language = brand_data.get('content_language', 'English (US)')
            
            voice_profile = json.dumps(brand_data.get('voice_profile', {}))
            guardrails = json.dumps(brand_data.get('guardrails', {}))
            strategy = json.dumps(brand_data.get('strategy', {}))
            rag_sources = json.dumps(brand_data.get('rag_sources', {}))
            social_credentials = json.dumps(brand_data.get('social_credentials', {}))
            
            # Insert brand
            cursor.execute("""
                INSERT INTO brand_profiles (
                    brand_name, brand_type, product_nature, industry, 
                    target_audience, content_language, voice_profile, 
                    guardrails, strategy, rag_sources, social_credentials
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, brand_name, created_at
            """, (
                brand_name, brand_type, product_nature, industry,
                target_audience, content_language, voice_profile,
                guardrails, strategy, rag_sources, social_credentials
            ))
            
            result = cursor.fetchone()
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Created brand profile: {brand_name}")
            return dict(result)
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error creating brand: {e}")
            raise
    
    def get_brand(self, brand_id: int) -> Optional[Dict[str, Any]]:
        """Get a brand profile by ID"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM brand_profiles WHERE id = %s
            """, (brand_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching brand: {e}")
            raise
    
    def get_all_brands(self) -> List[Dict[str, Any]]:
        """Get all brand profiles"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, brand_name, brand_type, industry, is_active, created_at
                FROM brand_profiles
                ORDER BY created_at DESC
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error fetching brands: {e}")
            raise
    
    def get_active_brand(self) -> Optional[Dict[str, Any]]:
        """Get the currently active brand with proper error handling"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM brand_profiles WHERE is_active = true LIMIT 1
            """)
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            # Explicitly rollback on error to prevent transaction abort state
            if self.connection:
                try:
                    self.connection.rollback()
                    logger.info("Transaction rolled back after error")
                except:
                    pass
            logger.error(f"Error fetching active brand: {e}")
            # Don't raise, return None to allow fallback
            return None
    
    def update_brand(self, brand_id: int, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a brand profile"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Build update query dynamically based on provided fields
            update_fields = []
            values = []
            
            field_mapping = {
                'brand_name': 'brand_name',
                'brand_type': 'brand_type',
                'product_nature': 'product_nature',
                'industry': 'industry',
                'target_audience': 'target_audience',
                'content_language': 'content_language'
            }
            
            json_field_mapping = {
                'voice_profile': 'voice_profile',
                'guardrails': 'guardrails',
                'strategy': 'strategy',
                'rag_sources': 'rag_sources',
                'social_credentials': 'social_credentials'
            }
            
            # Handle regular fields
            for key, db_field in field_mapping.items():
                if key in brand_data:
                    update_fields.append(f"{db_field} = %s")
                    values.append(brand_data[key])
            
            # Handle JSON fields
            for key, db_field in json_field_mapping.items():
                if key in brand_data:
                    update_fields.append(f"{db_field} = %s")
                    values.append(json.dumps(brand_data[key]))
            
            if not update_fields:
                raise ValueError("No fields to update")
            
            values.append(brand_id)
            
            query = f"""
                UPDATE brand_profiles 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, brand_name, updated_at
            """
            
            cursor.execute(query, values)
            result = cursor.fetchone()
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Updated brand profile: {result['brand_name']}")
            return dict(result)
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error updating brand: {e}")
            raise
    
    def set_active_brand(self, brand_id: int) -> Dict[str, Any]:
        """Set a brand as active (deactivates others)"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Deactivate all brands first
            cursor.execute("UPDATE brand_profiles SET is_active = false")
            
            # Activate the selected brand
            cursor.execute("""
                UPDATE brand_profiles 
                SET is_active = true
                WHERE id = %s
                RETURNING id, brand_name, is_active
            """, (brand_id,))
            
            result = cursor.fetchone()
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Set active brand: {result['brand_name']}")
            return dict(result)
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error setting active brand: {e}")
            raise
    
    def delete_brand(self, brand_id: int) -> bool:
        """Delete a brand profile"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                DELETE FROM brand_profiles WHERE id = %s
            """, (brand_id,))
            
            deleted = cursor.rowcount > 0
            self.connection.commit()
            cursor.close()
            
            if deleted:
                logger.info(f"✅ Deleted brand profile: {brand_id}")
            return deleted
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error deleting brand: {e}")
            raise
    
    # LLM-Powered Suggestion Methods
    
    def suggest_voice_adjectives(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate voice adjective suggestions using LLM"""
        try:
            brand_type = brand_data.get('brand_type', '')
            product_nature = brand_data.get('product_nature', '')
            target_audience = brand_data.get('target_audience', '')
            industry = brand_data.get('industry', '')
            
            prompt = f"""You are a brand strategist. Based on the following brand information, suggest 5 core voice adjectives that define the brand's personality.

Brand Type: {brand_type}
Product/Service: {product_nature}
Industry: {industry}
Target Audience: {target_audience}

Provide exactly 5 adjectives with a brief rationale for each. Format your response as:

1. [Adjective] - [One sentence rationale]
2. [Adjective] - [One sentence rationale]
3. [Adjective] - [One sentence rationale]
4. [Adjective] - [One sentence rationale]
5. [Adjective] - [One sentence rationale]

Choose adjectives that are:
- Authentic to the brand's nature
- Resonant with the target audience
- Distinctive and memorable
- Actionable for content creation

Your response:"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 400
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                suggestion_text = result.get('response', '').strip()
                
                # Parse the suggestions
                adjectives = self.parse_voice_adjectives(suggestion_text)
                
                return {
                    'adjectives': adjectives,
                    'raw_response': suggestion_text,
                    'method': 'LLM Generated'
                }
            else:
                return self.fallback_voice_adjectives(brand_type, industry)
                
        except Exception as e:
            logger.error(f"Error generating voice adjectives: {e}")
            return self.fallback_voice_adjectives(brand_type, industry)
    
    def parse_voice_adjectives(self, text: str) -> List[Dict[str, str]]:
        """Parse LLM-generated voice adjectives"""
        adjectives = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering
                line = line.lstrip('0123456789.-) ')
                
                if '-' in line:
                    parts = line.split('-', 1)
                    adjective = parts[0].strip()
                    rationale = parts[1].strip() if len(parts) > 1 else ''
                    
                    if adjective:
                        adjectives.append({
                            'adjective': adjective,
                            'rationale': rationale
                        })
        
        return adjectives[:5]  # Limit to 5
    
    def fallback_voice_adjectives(self, brand_type: str, industry: str) -> Dict[str, Any]:
        """Fallback voice adjectives if LLM fails"""
        adjective_map = {
            'Consumer Goods (CPG)': [
                {'adjective': 'Approachable', 'rationale': 'Friendly and accessible to everyday consumers'},
                {'adjective': 'Authentic', 'rationale': 'Genuine and trustworthy brand values'},
                {'adjective': 'Energetic', 'rationale': 'Dynamic and engaging presence'},
                {'adjective': 'Relatable', 'rationale': 'Connects with daily life experiences'},
                {'adjective': 'Quality-focused', 'rationale': 'Emphasizes product excellence'}
            ],
            'B2B Service': [
                {'adjective': 'Professional', 'rationale': 'Expert and business-oriented'},
                {'adjective': 'Reliable', 'rationale': 'Dependable and consistent service'},
                {'adjective': 'Innovative', 'rationale': 'Forward-thinking solutions'},
                {'adjective': 'Strategic', 'rationale': 'Goal-oriented approach'},
                {'adjective': 'Collaborative', 'rationale': 'Partnership-focused relationships'}
            ]
        }
        
        adjectives = adjective_map.get(brand_type, adjective_map['Consumer Goods (CPG)'])
        
        return {
            'adjectives': adjectives,
            'method': 'Fallback Template'
        }
    
    def suggest_tone_variations(self, core_adjectives: List[str]) -> Dict[str, Any]:
        """Generate tone variation table using LLM"""
        try:
            adjectives_str = ', '.join(core_adjectives)
            
            prompt = f"""You are a brand voice strategist. Based on these core brand voice adjectives: {adjectives_str}

Create a tone variation table for different social media scenarios. For each scenario, suggest a PRIMARY and SECONDARY tone that adapts the core voice appropriately.

Provide exactly this format:

CUSTOMER COMPLAINT
Primary: [Tone]
Secondary: [Tone]
Instruction: [Brief guidance]

NEW PRODUCT LAUNCH
Primary: [Tone]
Secondary: [Tone]
Instruction: [Brief guidance]

EDUCATIONAL CONTENT
Primary: [Tone]
Secondary: [Tone]
Instruction: [Brief guidance]

PROMOTIONAL POST
Primary: [Tone]
Secondary: [Tone]
Instruction: [Brief guidance]

COMMUNITY ENGAGEMENT
Primary: [Tone]
Secondary: [Tone]
Instruction: [Brief guidance]

Your response:"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.6,
                        "num_predict": 500
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                suggestion_text = result.get('response', '').strip()
                
                # Parse tone variations
                variations = self.parse_tone_variations(suggestion_text)
                
                return {
                    'tone_variations': variations,
                    'raw_response': suggestion_text,
                    'method': 'LLM Generated'
                }
            else:
                return self.fallback_tone_variations()
                
        except Exception as e:
            logger.error(f"Error generating tone variations: {e}")
            return self.fallback_tone_variations()
    
    def parse_tone_variations(self, text: str) -> Dict[str, Dict[str, str]]:
        """Parse LLM-generated tone variations"""
        variations = {}
        current_scenario = None
        current_data = {}
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for scenario header (all caps)
            if line and line.isupper() and not line.startswith('PRIMARY') and not line.startswith('SECONDARY'):
                if current_scenario and current_data:
                    variations[current_scenario.lower().replace(' ', '_')] = current_data
                current_scenario = line
                current_data = {}
            
            # Parse primary tone
            elif line.startswith('Primary:'):
                current_data['primary'] = line.replace('Primary:', '').strip()
            
            # Parse secondary tone
            elif line.startswith('Secondary:'):
                current_data['secondary'] = line.replace('Secondary:', '').strip()
            
            # Parse instruction
            elif line.startswith('Instruction:'):
                current_data['instruction'] = line.replace('Instruction:', '').strip()
        
        # Add last scenario
        if current_scenario and current_data:
            variations[current_scenario.lower().replace(' ', '_')] = current_data
        
        return variations
    
    def fallback_tone_variations(self) -> Dict[str, Any]:
        """Fallback tone variations if LLM fails"""
        variations = {
            'customer_complaint': {
                'primary': 'Empathetic',
                'secondary': 'Professional',
                'instruction': 'Prioritize understanding and solution-focused language'
            },
            'new_product_launch': {
                'primary': 'Enthusiastic',
                'secondary': 'Informative',
                'instruction': 'Build excitement while providing clear product details'
            },
            'educational_content': {
                'primary': 'Informative',
                'secondary': 'Approachable',
                'instruction': 'Focus on value and actionable insights'
            },
            'promotional_post': {
                'primary': 'Persuasive',
                'secondary': 'Direct',
                'instruction': 'Clear call-to-action with benefit-focused messaging'
            },
            'community_engagement': {
                'primary': 'Friendly',
                'secondary': 'Conversational',
                'instruction': 'Encourage interaction and build relationships'
            }
        }
        
        return {
            'tone_variations': variations,
            'method': 'Fallback Template'
        }
    
    def suggest_lexicon(self, product_nature: str, industry: str) -> Dict[str, Any]:
        """Generate lexicon suggestions (always use / never use)"""
        try:
            prompt = f"""You are a brand content strategist. Based on this product and industry information:

Product/Service: {product_nature}
Industry: {industry}

Suggest two lists:

ALWAYS USE (5-7 terms):
Terms, phrases, or keywords that should always be included when relevant because they represent the brand's unique value, key features, or selling points.

NEVER USE (5-7 terms):
Terms, phrases, or jargon that should be avoided because they're overused, irrelevant, or contradict the brand values.

Format your response as:

ALWAYS USE:
- [term/phrase] - [why]
- [term/phrase] - [why]
...

NEVER USE:
- [term/phrase] - [why]
- [term/phrase] - [why]
...

Your response:"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.6,
                        "num_predict": 400
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                suggestion_text = result.get('response', '').strip()
                
                # Parse lexicon
                lexicon = self.parse_lexicon(suggestion_text)
                
                return {
                    'always_use': lexicon['always_use'],
                    'never_use': lexicon['never_use'],
                    'raw_response': suggestion_text,
                    'method': 'LLM Generated'
                }
            else:
                return self.fallback_lexicon(product_nature)
                
        except Exception as e:
            logger.error(f"Error generating lexicon: {e}")
            return self.fallback_lexicon(product_nature)
    
    def parse_lexicon(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse LLM-generated lexicon"""
        always_use = []
        never_use = []
        current_section = None
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if 'ALWAYS USE' in line.upper():
                current_section = 'always'
            elif 'NEVER USE' in line.upper():
                current_section = 'never'
            elif line.startswith('-') and current_section:
                # Remove leading dash
                line = line.lstrip('- ')
                
                if '-' in line:
                    parts = line.split('-', 1)
                    term = parts[0].strip()
                    reason = parts[1].strip() if len(parts) > 1 else ''
                else:
                    term = line
                    reason = ''
                
                if term:
                    item = {'term': term, 'reason': reason}
                    if current_section == 'always':
                        always_use.append(item)
                    else:
                        never_use.append(item)
        
        return {
            'always_use': always_use[:7],
            'never_use': never_use[:7]
        }
    
    def fallback_lexicon(self, product_nature: str) -> Dict[str, Any]:
        """Fallback lexicon if LLM fails"""
        # Extract key terms from product nature
        always_use = []
        words = product_nature.lower().split()
        
        for word in words[:5]:
            if len(word) > 3:
                always_use.append({
                    'term': word,
                    'reason': 'Core product characteristic'
                })
        
        never_use = [
            {'term': 'cheap', 'reason': 'Implies low quality'},
            {'term': 'disruptive', 'reason': 'Overused buzzword'},
            {'term': 'game-changing', 'reason': 'Cliché marketing term'},
            {'term': 'revolutionary', 'reason': 'Hyperbolic claim'},
            {'term': 'synergy', 'reason': 'Corporate jargon'}
        ]
        
        return {
            'always_use': always_use,
            'never_use': never_use,
            'method': 'Fallback Template'
        }
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


def main():
    """Demo the Brand Manager"""
    print("🏢 Brand Manager Demo")
    print("=" * 50)
    
    manager = BrandManager()
    
    # Demo 1: Get all brands
    print("\n📋 Current Brands:")
    brands = manager.get_all_brands()
    for brand in brands:
        print(f"   • {brand['brand_name']} ({brand['brand_type']}) - Active: {brand['is_active']}")
    
    # Demo 2: Get active brand
    print("\n✅ Active Brand:")
    active = manager.get_active_brand()
    if active:
        print(f"   • {active['brand_name']}")
        print(f"   • Voice Adjectives: {active['voice_profile'].get('core_adjectives', [])}")
    
    # Demo 3: Generate voice suggestions
    print("\n🤖 LLM Voice Adjective Suggestions:")
    test_data = {
        'brand_type': 'Consumer Goods (CPG)',
        'product_nature': 'Organic cold-pressed juices',
        'industry': 'Health & Wellness',
        'target_audience': 'Health-conscious millennials'
    }
    
    suggestions = manager.suggest_voice_adjectives(test_data)
    print(f"   Method: {suggestions['method']}")
    for adj in suggestions['adjectives']:
        print(f"   • {adj['adjective']}: {adj['rationale']}")
    
    manager.close()
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
