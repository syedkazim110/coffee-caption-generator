-- Migration: Add preferred LLM model selection to brand profiles
-- This allows each brand to have its own preferred AI model

-- Add column for preferred LLM model (per-brand setting)
ALTER TABLE brand_profiles 
ADD COLUMN IF NOT EXISTS preferred_llm_model VARCHAR(100) DEFAULT 'ollama_phi3';

-- Add comment to explain the column
COMMENT ON COLUMN brand_profiles.preferred_llm_model IS 'Preferred AI model for caption generation (e.g., ollama_phi3, openai_gpt4, etc.)';

-- Update existing brands to use default model
UPDATE brand_profiles 
SET preferred_llm_model = 'ollama_phi3' 
WHERE preferred_llm_model IS NULL;

-- Optional: Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_brand_profiles_llm_model 
ON brand_profiles(preferred_llm_model);

-- Create table for global AI model settings (optional)
CREATE TABLE IF NOT EXISTS ai_model_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default global settings
INSERT INTO ai_model_settings (setting_key, setting_value, description)
VALUES 
    ('global_default_model', 'ollama_phi3', 'Global default AI model when no brand-specific preference is set'),
    ('global_fallback_model', 'ollama_phi3', 'Fallback model to use when primary model fails')
ON CONFLICT (setting_key) DO NOTHING;

-- Create table to track model usage statistics (optional but useful)
CREATE TABLE IF NOT EXISTS ai_model_usage (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brand_profiles(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    request_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 4) DEFAULT 0.0,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(brand_id, model_id)
);

-- Create index for usage tracking
CREATE INDEX IF NOT EXISTS idx_ai_model_usage_brand 
ON ai_model_usage(brand_id);

CREATE INDEX IF NOT EXISTS idx_ai_model_usage_model 
ON ai_model_usage(model_id);

-- Function to update model usage statistics
CREATE OR REPLACE FUNCTION update_model_usage(
    p_brand_id INTEGER,
    p_model_id VARCHAR(100),
    p_provider VARCHAR(50),
    p_tokens INTEGER DEFAULT 0,
    p_cost DECIMAL(10, 4) DEFAULT 0.0
) RETURNS VOID AS $$
BEGIN
    INSERT INTO ai_model_usage (brand_id, model_id, provider, request_count, total_tokens, total_cost_usd, last_used_at)
    VALUES (p_brand_id, p_model_id, p_provider, 1, p_tokens, p_cost, CURRENT_TIMESTAMP)
    ON CONFLICT (brand_id, model_id) 
    DO UPDATE SET
        request_count = ai_model_usage.request_count + 1,
        total_tokens = ai_model_usage.total_tokens + p_tokens,
        total_cost_usd = ai_model_usage.total_cost_usd + p_cost,
        last_used_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully! Added preferred_llm_model to brand_profiles.';
END $$;
