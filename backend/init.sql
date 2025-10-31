CREATE TABLE IF NOT EXISTS reddit_data (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255),
    subreddit VARCHAR(255),
    title TEXT,
    content TEXT,
    score INTEGER,
    created_utc BIGINT,
    comments JSONB,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS twitter_data (
    id SERIAL PRIMARY KEY,
    tweet_id VARCHAR(50) UNIQUE NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    author_id VARCHAR(50),
    created_at TIMESTAMP,
    language VARCHAR(10),
    retweet_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coffee articles table
CREATE TABLE IF NOT EXISTS coffee_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    rating VARCHAR(10),
    published_date TIMESTAMP,
    author VARCHAR(255),
    source VARCHAR(100) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    tags TEXT[],
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_twitter_keyword ON twitter_data(keyword);
CREATE INDEX IF NOT EXISTS idx_twitter_created_at ON twitter_data(created_at);
CREATE INDEX IF NOT EXISTS idx_twitter_tweet_id ON twitter_data(tweet_id);

-- Coffee articles indexes
CREATE INDEX IF NOT EXISTS idx_coffee_source ON coffee_articles(source);
CREATE INDEX IF NOT EXISTS idx_coffee_published_date ON coffee_articles(published_date);
CREATE INDEX IF NOT EXISTS idx_coffee_content_hash ON coffee_articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_coffee_scraped_at ON coffee_articles(scraped_at);

-- ========================================
-- AI MODEL SETTINGS AND API CREDENTIALS
-- ========================================

-- AI model settings table
CREATE TABLE IF NOT EXISTS ai_model_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API credentials table for storing API keys
CREATE TABLE IF NOT EXISTS api_credentials (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    api_key TEXT NOT NULL,
    api_endpoint VARCHAR(255),
    is_configured BOOLEAN DEFAULT TRUE,
    last_validated_at TIMESTAMP,
    validation_status VARCHAR(50) DEFAULT 'pending',
    validation_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for API credentials
CREATE INDEX IF NOT EXISTS idx_api_credentials_model_id ON api_credentials(model_id);
CREATE INDEX IF NOT EXISTS idx_api_credentials_provider ON api_credentials(provider);

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
