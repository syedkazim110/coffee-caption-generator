#!/usr/bin/env python3
"""
Database Helper Module
Provides functions to interact with PostgreSQL database instead of JSON/CSV files
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import os

# Database connection configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'reddit_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5434')
}

class DatabaseHelper:
    """Helper class for database operations"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # =========================================================================
    # GENERATED CAPTIONS
    # =========================================================================
    
    def save_captions(self, captions: List[Dict], method: str, sources_used: List[str], 
                      total_documents: int, llm_model: str, brand_id: Optional[int] = None):
        """
        Save generated captions to database
        
        Args:
            captions: List of caption dictionaries
            method: Generation method used
            sources_used: List of data sources
            total_documents: Total documents processed
            llm_model: LLM model used
            brand_id: Optional brand ID
        """
        insert_query = """
            INSERT INTO generated_captions 
            (caption_text, base_caption, hashtags, keyword, context_snippets, 
             method, sources_used, total_documents, llm_model, generation_timestamp, brand_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        batch_data = []
        for caption in captions:
            batch_data.append((
                caption.get('caption', ''),
                caption.get('base_caption', ''),
                json.dumps(caption.get('hashtags', [])),
                caption.get('keyword', ''),
                json.dumps(caption.get('context_snippets', [])),
                method,
                json.dumps(sources_used),
                total_documents,
                llm_model,
                caption.get('timestamp', datetime.now()),
                brand_id
            ))
        
        execute_batch(self.cursor, insert_query, batch_data)
        self.conn.commit()
        return len(batch_data)
    
    def get_captions(self, limit: int = 100, keyword: Optional[str] = None, 
                     brand_id: Optional[int] = None) -> List[Dict]:
        """
        Retrieve generated captions from database
        
        Args:
            limit: Maximum number of captions to retrieve
            keyword: Filter by keyword
            brand_id: Filter by brand
        """
        query = "SELECT * FROM generated_captions WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND keyword ILIKE %s"
            params.append(f"%{keyword}%")
        
        if brand_id:
            query += " AND brand_id = %s"
            params.append(brand_id)
        
        query += " ORDER BY generation_timestamp DESC LIMIT %s"
        params.append(limit)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # =========================================================================
    # COFFEE CONTEXT
    # =========================================================================
    
    def get_coffee_context(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get coffee context terms from database
        
        Args:
            category: Optional category filter
        """
        query = "SELECT category, term FROM coffee_context"
        params = []
        
        if category:
            query += " WHERE category = %s"
            params.append(category)
        
        query += " ORDER BY usage_count DESC"
        
        self.cursor.execute(query, params)
        
        context = {}
        for row in self.cursor.fetchall():
            cat = row['category']
            if cat not in context:
                context[cat] = []
            context[cat].append(row['term'])
        
        return context
    
    def add_coffee_terms(self, category: str, terms: List[str]):
        """Add new coffee context terms"""
        insert_query = """
            INSERT INTO coffee_context (category, term, usage_count)
            VALUES (%s, %s, 1)
            ON CONFLICT (category, term) DO UPDATE
            SET usage_count = coffee_context.usage_count + 1,
                last_updated = NOW()
        """
        
        batch_data = [(category, term) for term in terms]
        execute_batch(self.cursor, insert_query, batch_data)
        self.conn.commit()
    
    # =========================================================================
    # HASHTAG KNOWLEDGE
    # =========================================================================
    
    def get_hashtags(self, platform: Optional[str] = None, 
                     min_engagement: float = 0) -> List[Dict]:
        """
        Get hashtags from database
        
        Args:
            platform: Filter by platform
            min_engagement: Minimum engagement score
        """
        query = "SELECT * FROM hashtag_knowledge WHERE engagement_score >= %s"
        params = [min_engagement]
        
        if platform:
            query += " AND platform = %s"
            params.append(platform)
        
        query += " ORDER BY trending_score DESC, engagement_score DESC"
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_hashtag_metrics(self, hashtag: str, engagement_score: float, 
                               trending_score: float):
        """Update hashtag engagement and trending scores"""
        query = """
            UPDATE hashtag_knowledge 
            SET engagement_score = %s, trending_score = %s, last_seen = NOW()
            WHERE hashtag = %s
        """
        self.cursor.execute(query, (engagement_score, trending_score, hashtag))
        self.conn.commit()
    
    # =========================================================================
    # SOCIAL MEDIA POSTS
    # =========================================================================
    
    def save_post(self, platform: str, content: str, image_prompt: Optional[str] = None,
                  hashtags: Optional[List[str]] = None, brand_id: Optional[int] = None,
                  scheduled_for: Optional[datetime] = None) -> int:
        """
        Save a social media post to database
        
        Returns:
            Post ID
        """
        insert_query = """
            INSERT INTO social_media_posts 
            (platform, post_content, image_prompt, hashtags, brand_id, scheduled_for, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'draft')
            RETURNING id
        """
        
        self.cursor.execute(insert_query, (
            platform,
            content,
            image_prompt,
            json.dumps(hashtags or []),
            brand_id,
            scheduled_for
        ))
        
        post_id = self.cursor.fetchone()['id']
        self.conn.commit()
        return post_id
    
    def get_posts(self, platform: Optional[str] = None, status: Optional[str] = None,
                  brand_id: Optional[int] = None) -> List[Dict]:
        """Get social media posts from database"""
        query = "SELECT * FROM social_media_posts WHERE 1=1"
        params = []
        
        if platform:
            query += " AND platform = %s"
            params.append(platform)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if brand_id:
            query += " AND brand_id = %s"
            params.append(brand_id)
        
        query += " ORDER BY created_at DESC"
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_post_status(self, post_id: int, status: str, 
                           published_at: Optional[datetime] = None):
        """Update post status"""
        query = """
            UPDATE social_media_posts 
            SET status = %s, published_at = %s, updated_at = NOW()
            WHERE id = %s
        """
        self.cursor.execute(query, (status, published_at, post_id))
        self.conn.commit()
    
    # =========================================================================
    # RAG DOCUMENTS
    # =========================================================================
    
    def save_rag_document(self, text: str, title: Optional[str] = None,
                          source_type: str = 'article', source_url: Optional[str] = None,
                          metadata: Optional[Dict] = None):
        """Save a document for RAG"""
        insert_query = """
            INSERT INTO rag_documents 
            (document_text, document_title, source_type, source_url, metadata)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        self.cursor.execute(insert_query, (
            text,
            title,
            source_type,
            source_url,
            json.dumps(metadata or {})
        ))
        
        doc_id = self.cursor.fetchone()['id']
        self.conn.commit()
        return doc_id
    
    def search_rag_documents(self, query: str, limit: int = 10) -> List[Dict]:
        """Search RAG documents (basic text search)"""
        search_query = """
            SELECT * FROM rag_documents 
            WHERE document_text ILIKE %s OR document_title ILIKE %s
            ORDER BY indexed_at DESC
            LIMIT %s
        """
        
        search_term = f"%{query}%"
        self.cursor.execute(search_query, (search_term, search_term, limit))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # =========================================================================
    # TRENDING KEYWORDS
    # =========================================================================
    
    def get_trending_keywords(self, source: Optional[str] = None, 
                              limit: int = 50) -> List[Dict]:
        """Get trending keywords"""
        query = "SELECT * FROM trending_keywords"
        params = []
        
        if source:
            query += " WHERE source = %s"
            params.append(source)
        
        query += " ORDER BY trend_score DESC, recorded_date DESC LIMIT %s"
        params.append(limit)
        
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # =========================================================================
    # BRAND PROFILES
    # =========================================================================
    
    def get_active_brands(self) -> List[Dict]:
        """Get all active brand profiles"""
        query = "SELECT * FROM brand_profiles WHERE is_active = true ORDER BY brand_name"
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_brand_by_name(self, brand_name: str) -> Optional[Dict]:
        """Get brand profile by name"""
        query = "SELECT * FROM brand_profiles WHERE brand_name = %s"
        self.cursor.execute(query, (brand_name,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    # =========================================================================
    # STATISTICS & ANALYTICS
    # =========================================================================
    
    def get_content_stats(self, days: int = 30) -> Dict:
        """Get content generation statistics"""
        query = """
            SELECT 
                COUNT(*) as total_captions,
                COUNT(DISTINCT keyword) as unique_keywords,
                COUNT(DISTINCT brand_id) as brands_count
            FROM generated_captions
            WHERE generation_timestamp >= NOW() - INTERVAL '%s days'
        """
        
        self.cursor.execute(query, (days,))
        return dict(self.cursor.fetchone())
    
    def get_database_summary(self) -> Dict:
        """Get summary of all tables and record counts"""
        tables = [
            'generated_captions', 'coffee_context', 'hashtag_knowledge',
            'trending_keywords', 'coffee_habits', 'social_media_posts',
            'rag_documents', 'coffee_articles', 'reddit_data', 
            'twitter_data', 'brand_profiles'
        ]
        
        summary = {}
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            self.cursor.execute(query)
            summary[table] = self.cursor.fetchone()['count']
        
        return summary


# Convenience function for quick database access
def get_db() -> DatabaseHelper:
    """Get a database helper instance"""
    return DatabaseHelper()


# Example usage functions
if __name__ == '__main__':
    # Example: Get database summary
    with get_db() as db:
        summary = db.get_database_summary()
        print("Database Summary:")
        print("=" * 50)
        for table, count in summary.items():
            print(f"{table:.<40} {count:>6} records")
