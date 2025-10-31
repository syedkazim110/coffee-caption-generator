-- Brand Profiles Schema for Multi-Brand Social Media Content Generation
-- This schema supports comprehensive brand onboarding with voice profiles, guardrails, and strategy

-- Drop existing table if recreating
DROP TABLE IF EXISTS brand_profiles CASCADE;

-- Create brand_profiles table
CREATE TABLE brand_profiles (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    brand_name VARCHAR(255) NOT NULL UNIQUE,
    brand_type VARCHAR(100), -- CPG, B2B Service, Media/News, Non-Profit
    product_nature TEXT, -- Core product/service description
    industry VARCHAR(100), -- Specialty Beverage, B2B SaaS, etc.
    target_audience TEXT, -- Demographics and psychographics
    content_language VARCHAR(50) DEFAULT 'English (US)',
    
    -- Brand Voice Profile (JSON structure)
    -- {
    --   "core_adjectives": ["Witty", "Informative", "Approachable"],
    --   "tone_variations": {
    --     "complaint": {"primary": "Empathetic", "secondary": "Formal"},
    --     "promo": {"primary": "Enthusiastic", "secondary": "Direct"}
    --   },
    --   "lexicon_always_use": ["proprietary process", "ethically sourced"],
    --   "lexicon_never_use": ["disruptive", "game-changing", "synergy"],
    --   "punctuation_style": "Limit emojis to one per post",
    --   "example_content": [] -- URLs or text of on-brand examples
    -- }
    voice_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Content Guardrails (JSON structure)
    -- {
    --   "inappropriate_topics": ["Politics", "Religion", "Competitive Benchmarks"],
    --   "mandatory_disclaimers": {"sponsored": "Always include #ad for sponsored posts"},
    --   "fact_check_level": "High", -- High/Medium/Low
    --   "image_style": "Minimalist, high-contrast, warm color palette"
    -- }
    guardrails JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Strategy & Workflow (JSON structure)
    -- {
    --   "content_mix": {"education": 40, "engagement": 40, "promotion": 20},
    --   "platform_rules": {
    --     "instagram": {"max_chars": 150, "style": "Visual-focused, casual"},
    --     "facebook": {"max_chars": 80, "style": "Conversational, friendly"},
    --     "linkedin": {"max_chars": 300, "style": "Professional, informative"},
    --     "twitter": {"max_chars": 100, "style": "Punchy, witty"}
    --   },
    --   "workflow_mode": "Draft & Require Approval"
    -- }
    strategy JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- RAG Content Sources (JSON structure)
    -- {
    --   "urls": ["https://example.com/blog"],
    --   "rss_feeds": ["https://example.com/feed"],
    --   "custom_documents": []
    -- }
    rag_sources JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Social Media Credentials (Placeholder - JSON structure)
    -- {
    --   "facebook": {"connected": false, "placeholder": "OAuth token"},
    --   "instagram": {"connected": false, "placeholder": "OAuth token"},
    --   "twitter": {"connected": false, "placeholder": "OAuth token"},
    --   "linkedin": {"connected": false, "placeholder": "OAuth token"}
    -- }
    social_credentials JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Ensure at least one brand is active
    CONSTRAINT at_least_one_active CHECK (is_active = true)
);

-- Create indexes for performance
CREATE INDEX idx_brand_active ON brand_profiles(is_active);
CREATE INDEX idx_brand_name ON brand_profiles(brand_name);
CREATE INDEX idx_brand_created ON brand_profiles(created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_brand_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER brand_updated_at_trigger
    BEFORE UPDATE ON brand_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_brand_updated_at();

-- Insert default/example brand (optional - for testing)
INSERT INTO brand_profiles (
    brand_name,
    brand_type,
    product_nature,
    industry,
    target_audience,
    content_language,
    voice_profile,
    guardrails,
    strategy,
    rag_sources
) VALUES (
    'Warpath Coffee',
    'Consumer Goods (CPG)',
    'Specialty whole coffee beans, veteran-owned',
    'Specialty Beverage',
    'Urban professionals, 25-40, value sustainability and veteran support',
    'English (US)',
    '{
        "core_adjectives": ["Bold", "Authentic", "Passionate", "Dedicated"],
        "tone_variations": {
            "complaint": {"primary": "Empathetic", "secondary": "Professional"},
            "promo": {"primary": "Enthusiastic", "secondary": "Direct"},
            "educational": {"primary": "Informative", "secondary": "Approachable"}
        },
        "lexicon_always_use": ["veteran-owned", "mission-driven", "ethically sourced", "quality first"],
        "lexicon_never_use": ["cheap", "generic", "mass-produced"],
        "punctuation_style": "Use military-inspired language naturally, limit emojis to 1-2 per post"
    }',
    '{
        "inappropriate_topics": ["Politics", "Religion", "Controversial social issues"],
        "mandatory_disclaimers": {"sponsored": "#ad", "affiliate": "#affiliate"},
        "fact_check_level": "High",
        "image_style": "Rustic, authentic, military-inspired, warm tones"
    }',
    '{
        "content_mix": {"education": 40, "engagement": 40, "promotion": 20},
        "platform_rules": {
            "instagram": {"max_chars": 150, "style": "Visual-focused, lifestyle"},
            "facebook": {"max_chars": 80, "style": "Conversational, community"},
            "linkedin": {"max_chars": 300, "style": "Professional, thought-leadership"},
            "twitter": {"max_chars": 100, "style": "Punchy, impactful"}
        },
        "workflow_mode": "Draft & Require Approval"
    }',
    '{
        "urls": ["https://www.coffeereview.com", "https://www.perfectdailygrind.com"],
        "rss_feeds": [],
        "custom_documents": []
    }'
);

-- Comments for documentation
COMMENT ON TABLE brand_profiles IS 'Stores comprehensive brand profiles for multi-brand social media content generation';
COMMENT ON COLUMN brand_profiles.voice_profile IS 'Brand voice configuration including adjectives, tone variations, and lexicon rules';
COMMENT ON COLUMN brand_profiles.guardrails IS 'Content safety rules, disclaimers, and quality controls';
COMMENT ON COLUMN brand_profiles.strategy IS 'Content strategy including mix ratios and platform-specific rules';
COMMENT ON COLUMN brand_profiles.rag_sources IS 'Custom RAG content sources for brand-specific knowledge';
