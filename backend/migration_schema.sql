-- Migration Schema: Moving all JSON/CSV data to PostgreSQL
-- This schema includes tables for generated content, knowledge bases, and analytics

-- =============================================================================
-- GENERATED CONTENT TABLES
-- =============================================================================

-- Table for storing LLM-generated captions
CREATE TABLE IF NOT EXISTS generated_captions (
    id SERIAL PRIMARY KEY,
    caption_text TEXT NOT NULL,
    base_caption TEXT,
    hashtags JSONB DEFAULT '[]'::jsonb,
    keyword VARCHAR(255),
    context_snippets JSONB DEFAULT '[]'::jsonb,
    method VARCHAR(100),
    sources_used JSONB DEFAULT '[]'::jsonb,
    total_documents INTEGER,
    llm_model VARCHAR(100),
    generation_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    brand_id INTEGER REFERENCES brand_profiles(id) ON DELETE SET NULL
);

-- Table for complete social media posts
CREATE TABLE IF NOT EXISTS social_media_posts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    post_content TEXT NOT NULL,
    image_prompt TEXT,
    image_url TEXT,
    hashtags JSONB DEFAULT '[]'::jsonb,
    scheduled_for TIMESTAMP,
    published_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft', -- draft, scheduled, published, failed
    engagement_metrics JSONB DEFAULT '{}'::jsonb, -- likes, shares, comments, etc.
    brand_id INTEGER REFERENCES brand_profiles(id) ON DELETE CASCADE,
    caption_id INTEGER REFERENCES generated_captions(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- KNOWLEDGE BASE TABLES
-- =============================================================================

-- Table for coffee context/terminology
CREATE TABLE IF NOT EXISTS coffee_context (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL, -- flavor_descriptors, brewing_terms, sensory_words, etc.
    term VARCHAR(255) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    sentiment_score FLOAT,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(category, term)
);

-- Table for hashtag knowledge base
CREATE TABLE IF NOT EXISTS hashtag_knowledge (
    id SERIAL PRIMARY KEY,
    hashtag VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100),
    engagement_score FLOAT DEFAULT 0,
    trending_score FLOAT DEFAULT 0,
    platform VARCHAR(50),
    usage_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    last_seen TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table for trending keywords and topics
CREATE TABLE IF NOT EXISTS trending_keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    trend_score FLOAT DEFAULT 0,
    source VARCHAR(100), -- twitter, reddit, blogs, etc.
    geographical_region VARCHAR(100),
    context JSONB DEFAULT '{}'::jsonb,
    recorded_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- DATA ANALYTICS & INSIGHTS TABLES
-- =============================================================================

-- Table for worldwide coffee consumption habits
CREATE TABLE IF NOT EXISTS coffee_habits (
    id SERIAL PRIMARY KEY,
    country VARCHAR(100),
    region VARCHAR(100),
    consumption_metric VARCHAR(100),
    metric_value FLOAT,
    habit_type VARCHAR(100), -- daily_cups, preferred_time, brewing_method, etc.
    demographic_info JSONB DEFAULT '{}'::jsonb,
    data_source VARCHAR(255),
    recorded_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table for data quality reports
CREATE TABLE IF NOT EXISTS data_quality_reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(100),
    report_data JSONB NOT NULL,
    validation_status VARCHAR(50), -- passed, failed, warning
    issues_found INTEGER DEFAULT 0,
    validation_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- RAG & AI CONTEXT TABLES
-- =============================================================================

-- Table for RAG documents and embeddings (if using vector DB extension)
CREATE TABLE IF NOT EXISTS rag_documents (
    id SERIAL PRIMARY KEY,
    document_text TEXT NOT NULL,
    document_title TEXT,
    source_type VARCHAR(100), -- article, reddit_post, tweet, blog, etc.
    source_url TEXT,
    source_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    indexed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table for image generation prompts
CREATE TABLE IF NOT EXISTS image_prompts (
    id SERIAL PRIMARY KEY,
    prompt_text TEXT NOT NULL,
    style_keywords JSONB DEFAULT '[]'::jsonb,
    coffee_related BOOLEAN DEFAULT true,
    generated_image_url TEXT,
    generation_status VARCHAR(50), -- pending, generated, failed
    brand_id INTEGER REFERENCES brand_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Generated Captions indexes
CREATE INDEX IF NOT EXISTS idx_captions_keyword ON generated_captions(keyword);
CREATE INDEX IF NOT EXISTS idx_captions_generation_time ON generated_captions(generation_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_captions_brand ON generated_captions(brand_id);
CREATE INDEX IF NOT EXISTS idx_captions_method ON generated_captions(method);

-- Social Media Posts indexes
CREATE INDEX IF NOT EXISTS idx_posts_platform ON social_media_posts(platform);
CREATE INDEX IF NOT EXISTS idx_posts_status ON social_media_posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_scheduled ON social_media_posts(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_posts_brand ON social_media_posts(brand_id);
CREATE INDEX IF NOT EXISTS idx_posts_created ON social_media_posts(created_at DESC);

-- Coffee Context indexes
CREATE INDEX IF NOT EXISTS idx_context_category ON coffee_context(category);
CREATE INDEX IF NOT EXISTS idx_context_term ON coffee_context(term);
CREATE INDEX IF NOT EXISTS idx_context_usage ON coffee_context(usage_count DESC);

-- Hashtag Knowledge indexes
CREATE INDEX IF NOT EXISTS idx_hashtag_tag ON hashtag_knowledge(hashtag);
CREATE INDEX IF NOT EXISTS idx_hashtag_engagement ON hashtag_knowledge(engagement_score DESC);
CREATE INDEX IF NOT EXISTS idx_hashtag_trending ON hashtag_knowledge(trending_score DESC);
CREATE INDEX IF NOT EXISTS idx_hashtag_platform ON hashtag_knowledge(platform);

-- Trending Keywords indexes
CREATE INDEX IF NOT EXISTS idx_trending_keyword ON trending_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_trending_score ON trending_keywords(trend_score DESC);
CREATE INDEX IF NOT EXISTS idx_trending_date ON trending_keywords(recorded_date DESC);
CREATE INDEX IF NOT EXISTS idx_trending_source ON trending_keywords(source);

-- Coffee Habits indexes
CREATE INDEX IF NOT EXISTS idx_habits_country ON coffee_habits(country);
CREATE INDEX IF NOT EXISTS idx_habits_type ON coffee_habits(habit_type);
CREATE INDEX IF NOT EXISTS idx_habits_date ON coffee_habits(recorded_date);

-- RAG Documents indexes
CREATE INDEX IF NOT EXISTS idx_rag_source_type ON rag_documents(source_type);
CREATE INDEX IF NOT EXISTS idx_rag_source_id ON rag_documents(source_id);
CREATE INDEX IF NOT EXISTS idx_rag_indexed ON rag_documents(indexed_at DESC);

-- Image Prompts indexes
CREATE INDEX IF NOT EXISTS idx_prompts_status ON image_prompts(generation_status);
CREATE INDEX IF NOT EXISTS idx_prompts_brand ON image_prompts(brand_id);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =============================================================================

-- Trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to social_media_posts
CREATE TRIGGER update_posts_updated_at
    BEFORE UPDATE ON social_media_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for recent content generation stats
CREATE OR REPLACE VIEW recent_content_stats AS
SELECT 
    DATE(generation_timestamp) as date,
    COUNT(*) as captions_generated,
    COUNT(DISTINCT keyword) as unique_keywords,
    COUNT(DISTINCT brand_id) as brands_count,
    method
FROM generated_captions
WHERE generation_timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(generation_timestamp), method
ORDER BY date DESC;

-- View for hashtag performance
CREATE OR REPLACE VIEW hashtag_performance AS
SELECT 
    h.hashtag,
    h.engagement_score,
    h.trending_score,
    h.usage_count,
    h.platform,
    COUNT(DISTINCT gc.id) as times_used_in_captions
FROM hashtag_knowledge h
LEFT JOIN generated_captions gc ON gc.hashtags::text LIKE '%' || h.hashtag || '%'
GROUP BY h.id, h.hashtag, h.engagement_score, h.trending_score, h.usage_count, h.platform
ORDER BY h.trending_score DESC;

-- View for brand content overview
CREATE OR REPLACE VIEW brand_content_overview AS
SELECT 
    bp.brand_name,
    COUNT(DISTINCT gc.id) as total_captions,
    COUNT(DISTINCT smp.id) as total_posts,
    COUNT(DISTINCT CASE WHEN smp.status = 'published' THEN smp.id END) as published_posts,
    COUNT(DISTINCT ip.id) as total_image_prompts,
    bp.is_active
FROM brand_profiles bp
LEFT JOIN generated_captions gc ON gc.brand_id = bp.id
LEFT JOIN social_media_posts smp ON smp.brand_id = bp.id
LEFT JOIN image_prompts ip ON ip.brand_id = bp.id
GROUP BY bp.id, bp.brand_name, bp.is_active;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE generated_captions IS 'Stores all LLM-generated social media captions with context and metadata';
COMMENT ON TABLE social_media_posts IS 'Complete social media posts ready for publishing across platforms';
COMMENT ON TABLE coffee_context IS 'Coffee terminology, descriptors, and industry vocabulary for content generation';
COMMENT ON TABLE hashtag_knowledge IS 'Hashtag analytics including engagement scores and trending metrics';
COMMENT ON TABLE trending_keywords IS 'Trending coffee-related keywords and topics from various sources';
COMMENT ON TABLE coffee_habits IS 'Global coffee consumption patterns and preferences';
COMMENT ON TABLE data_quality_reports IS 'Data validation and quality assurance reports';
COMMENT ON TABLE rag_documents IS 'Documents used for RAG (Retrieval Augmented Generation) context';
COMMENT ON TABLE image_prompts IS 'AI image generation prompts for social media content';
