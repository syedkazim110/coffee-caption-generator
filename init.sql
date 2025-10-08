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
