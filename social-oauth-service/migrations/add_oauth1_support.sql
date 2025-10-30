-- Add OAuth 1.0a support for Twitter media uploads
-- Twitter's v1.1 media upload endpoint requires OAuth 1.0a authentication

ALTER TABLE social_connections
ADD COLUMN IF NOT EXISTS oauth1_access_token TEXT,
ADD COLUMN IF NOT EXISTS oauth1_access_token_secret TEXT,
ADD COLUMN IF NOT EXISTS oauth1_enabled BOOLEAN DEFAULT false;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_social_connections_oauth1_enabled 
ON social_connections(brand_id, platform, oauth1_enabled);

-- Add comment for documentation
COMMENT ON COLUMN social_connections.oauth1_access_token IS 'OAuth 1.0a access token (encrypted) - Required for Twitter media uploads';
COMMENT ON COLUMN social_connections.oauth1_access_token_secret IS 'OAuth 1.0a access token secret (encrypted) - Required for Twitter media uploads';
COMMENT ON COLUMN social_connections.oauth1_enabled IS 'Whether OAuth 1.0a credentials are available for this connection';
