-- Migration: Add API key management for AI models
-- This allows users to configure API keys for cloud-based AI providers

-- Create table for storing API credentials
CREATE TABLE IF NOT EXISTS api_credentials (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    api_key TEXT NOT NULL, -- Will be encrypted in application layer
    api_endpoint VARCHAR(255),
    is_configured BOOLEAN DEFAULT TRUE,
    last_validated_at TIMESTAMP,
    validation_status VARCHAR(50) DEFAULT 'pending', -- pending, valid, invalid
    validation_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_model_id FOREIGN KEY (model_id) 
        REFERENCES ai_model_settings(setting_key) ON DELETE CASCADE
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_api_credentials_model_id 
ON api_credentials(model_id);

CREATE INDEX IF NOT EXISTS idx_api_credentials_provider 
ON api_credentials(provider);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_api_credentials_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp update
DROP TRIGGER IF EXISTS trigger_update_api_credentials_timestamp ON api_credentials;
CREATE TRIGGER trigger_update_api_credentials_timestamp
    BEFORE UPDATE ON api_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_api_credentials_timestamp();

-- Add helper function to check if model is configured
CREATE OR REPLACE FUNCTION is_model_configured(p_model_id VARCHAR(100))
RETURNS BOOLEAN AS $$
DECLARE
    configured BOOLEAN;
BEGIN
    SELECT is_configured INTO configured
    FROM api_credentials
    WHERE model_id = p_model_id AND validation_status = 'valid';
    
    RETURN COALESCE(configured, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Add helper function to get API key for model
CREATE OR REPLACE FUNCTION get_model_api_key(p_model_id VARCHAR(100))
RETURNS TEXT AS $$
DECLARE
    key TEXT;
BEGIN
    SELECT api_key INTO key
    FROM api_credentials
    WHERE model_id = p_model_id AND is_configured = TRUE;
    
    RETURN key;
END;
$$ LANGUAGE plpgsql;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed! API credentials table created with encryption support.';
    RAISE NOTICE 'Use POST /api/ai-models/{model_id}/configure to set API keys.';
END $$;
