-- OAuth Service Database Schema
-- This schema handles OAuth connections, tokens, and social media posting

-- Social media connections table
CREATE TABLE IF NOT EXISTS social_connections (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL,
    platform VARCHAR(50) NOT NULL,
    
    -- OAuth credentials (encrypted)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP,
    
    -- OAuth app credentials
    client_id VARCHAR(255) NOT NULL,
    client_secret TEXT NOT NULL,
    
    -- Connected account information
    platform_user_id VARCHAR(255),
    platform_username VARCHAR(255),
    account_name VARCHAR(255),
    profile_picture_url TEXT,
    account_metadata JSONB DEFAULT '{}',
    
    -- Connection status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    connection_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(brand_id, platform, platform_user_id)
);

-- Scheduled posts table
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL,
    
    -- Post content
    caption TEXT NOT NULL,
    hashtags TEXT[] DEFAULT '{}',
    image_url TEXT,
    image_base64 TEXT,
    
    -- Platform targeting
    platforms VARCHAR(50)[] NOT NULL,
    platform_specific_content JSONB DEFAULT '{}',
    
    -- Scheduling
    scheduled_time TIMESTAMP NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Post metadata
    post_type VARCHAR(50) DEFAULT 'immediate', -- immediate, scheduled, recurring
    recurrence_pattern VARCHAR(100), -- daily, weekly, monthly
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, published, failed, cancelled
    approval_required BOOLEAN DEFAULT false,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    
    -- Publishing results
    published_at TIMESTAMP,
    publishing_results JSONB DEFAULT '{}', -- {platform: {post_id, url, error}}
    
    -- Error handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Post publishing history
CREATE TABLE IF NOT EXISTS post_history (
    id SERIAL PRIMARY KEY,
    scheduled_post_id INTEGER REFERENCES scheduled_posts(id),
    brand_id INTEGER NOT NULL,
    platform VARCHAR(50) NOT NULL,
    
    -- Post details
    platform_post_id VARCHAR(255),
    post_url TEXT,
    caption TEXT,
    
    -- Publishing metadata
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- success, failed
    error_message TEXT,
    
    -- Engagement metrics (populated via webhooks)
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    engagement_data JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook events table
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    
    -- Event payload
    payload JSONB NOT NULL,
    
    -- Processing status
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    processing_error TEXT,
    
    -- Timestamps
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OAuth state tracking (for security)
CREATE TABLE IF NOT EXISTS oauth_states (
    id SERIAL PRIMARY KEY,
    state_token VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    brand_id INTEGER NOT NULL,
    
    -- PKCE for enhanced security
    code_verifier VARCHAR(255),
    code_challenge VARCHAR(255),
    
    -- Expiration
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API keys for service-to-service authentication
CREATE TABLE IF NOT EXISTS service_api_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    
    -- Permissions
    scopes TEXT[] DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_social_connections_brand_platform ON social_connections(brand_id, platform);
CREATE INDEX IF NOT EXISTS idx_social_connections_active ON social_connections(is_active);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_scheduled_time ON scheduled_posts(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_brand ON scheduled_posts(brand_id);
CREATE INDEX IF NOT EXISTS idx_post_history_scheduled_post ON post_history(scheduled_post_id);
CREATE INDEX IF NOT EXISTS idx_post_history_brand ON post_history(brand_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON webhook_events(processed);
CREATE INDEX IF NOT EXISTS idx_oauth_states_token ON oauth_states(state_token);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires ON oauth_states(expires_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_social_connections_updated_at BEFORE UPDATE ON social_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_posts_updated_at BEFORE UPDATE ON scheduled_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_post_history_updated_at BEFORE UPDATE ON post_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default service API key (change in production!)
INSERT INTO service_api_keys (key_name, api_key, scopes, is_active)
VALUES (
    'main-app-service',
    'dev-service-key-change-in-production',
    ARRAY['oauth:read', 'oauth:write', 'posts:publish', 'posts:schedule'],
    true
) ON CONFLICT DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE social_connections IS 'Stores OAuth connections for social media platforms';
COMMENT ON TABLE scheduled_posts IS 'Manages scheduled and immediate social media posts';
COMMENT ON TABLE post_history IS 'Historical record of published posts with engagement metrics';
COMMENT ON TABLE webhook_events IS 'Incoming webhook events from social platforms';
COMMENT ON TABLE oauth_states IS 'Tracks OAuth state tokens for security';
COMMENT ON TABLE service_api_keys IS 'API keys for service-to-service authentication';
