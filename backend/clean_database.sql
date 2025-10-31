-- ============================================================
-- COMPREHENSIVE DATABASE CLEANING SCRIPT
-- ============================================================
-- This script cleans all data quality issues in the PostgreSQL database
-- Run this after creating a backup with backup_database.py

-- Start transaction for safety
BEGIN;

-- ============================================================
-- REDDIT DATA CLEANING
-- ============================================================

-- Clean text fields in reddit_data table
UPDATE reddit_data SET
    keyword = TRIM(REGEXP_REPLACE(keyword, '\s+', ' ', 'g')),
    subreddit = TRIM(REGEXP_REPLACE(subreddit, '\s+', ' ', 'g')),
    title = TRIM(REGEXP_REPLACE(title, '\s+', ' ', 'g')),
    content = TRIM(REGEXP_REPLACE(content, '\s+', ' ', 'g'))
WHERE 
    keyword IS NOT NULL OR 
    subreddit IS NOT NULL OR 
    title IS NOT NULL OR 
    content IS NOT NULL;

-- Remove special characters and fix encoding issues
UPDATE reddit_data SET
    title = REGEXP_REPLACE(title, '[^\x20-\x7E\x0A\x0D]', '', 'g'),
    content = REGEXP_REPLACE(content, '[^\x20-\x7E\x0A\x0D]', '', 'g')
WHERE title IS NOT NULL OR content IS NOT NULL;

-- Handle null/empty values
UPDATE reddit_data SET
    keyword = CASE WHEN TRIM(keyword) = '' THEN NULL ELSE keyword END,
    subreddit = CASE WHEN TRIM(subreddit) = '' THEN NULL ELSE subreddit END,
    title = CASE WHEN TRIM(title) = '' THEN NULL ELSE title END,
    content = CASE WHEN TRIM(content) = '' THEN NULL ELSE content END;

-- Remove duplicate reddit posts based on title and content similarity
WITH duplicates AS (
    SELECT id, 
           ROW_NUMBER() OVER (
               PARTITION BY 
                   LOWER(TRIM(title)), 
                   LOWER(TRIM(SUBSTRING(content, 1, 100)))
               ORDER BY scraped_at DESC
           ) as rn
    FROM reddit_data
    WHERE title IS NOT NULL
)
DELETE FROM reddit_data 
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- ============================================================
-- COFFEE ARTICLES CLEANING
-- ============================================================

-- Clean text fields in coffee_articles table
UPDATE coffee_articles SET
    title = TRIM(REGEXP_REPLACE(title, '\s+', ' ', 'g')),
    content = TRIM(REGEXP_REPLACE(content, '\s+', ' ', 'g')),
    author = TRIM(REGEXP_REPLACE(author, '\s+', ' ', 'g')),
    source = TRIM(REGEXP_REPLACE(source, '\s+', ' ', 'g')),
    url = TRIM(url)
WHERE 
    title IS NOT NULL OR 
    content IS NOT NULL OR 
    author IS NOT NULL OR 
    source IS NOT NULL OR 
    url IS NOT NULL;

-- Remove special characters and fix encoding issues
UPDATE coffee_articles SET
    title = REGEXP_REPLACE(title, '[^\x20-\x7E\x0A\x0D]', '', 'g'),
    content = REGEXP_REPLACE(content, '[^\x20-\x7E\x0A\x0D]', '', 'g'),
    author = REGEXP_REPLACE(author, '[^\x20-\x7E\x0A\x0D]', '', 'g')
WHERE title IS NOT NULL OR content IS NOT NULL OR author IS NOT NULL;

-- Standardize rating formats
UPDATE coffee_articles SET
    rating = CASE 
        WHEN rating ~ '^[0-9]+(\.[0-9]+)?/[0-9]+$' THEN rating  -- Already in X/Y format
        WHEN rating ~ '^[0-9]+(\.[0-9]+)?$' AND rating::NUMERIC <= 5 THEN rating || '/5'  -- Assume out of 5
        WHEN rating ~ '^[0-9]+(\.[0-9]+)?$' AND rating::NUMERIC <= 10 THEN rating || '/10'  -- Assume out of 10
        WHEN rating ~ '^[0-9]+(\.[0-9]+)?%$' THEN 
            ROUND((REGEXP_REPLACE(rating, '%', '')::NUMERIC / 100 * 5), 1) || '/5'  -- Convert percentage to /5
        WHEN LOWER(rating) IN ('excellent', 'outstanding') THEN '5/5'
        WHEN LOWER(rating) IN ('very good', 'great') THEN '4/5'
        WHEN LOWER(rating) IN ('good', 'decent') THEN '3/5'
        WHEN LOWER(rating) IN ('fair', 'okay') THEN '2/5'
        WHEN LOWER(rating) IN ('poor', 'bad') THEN '1/5'
        ELSE NULL  -- Invalid ratings set to NULL
    END
WHERE rating IS NOT NULL AND TRIM(rating) != '';

-- Clean and validate URLs
UPDATE coffee_articles SET
    url = LOWER(TRIM(url))
WHERE url IS NOT NULL;

-- Remove invalid URLs
UPDATE coffee_articles SET
    url = NULL
WHERE url IS NOT NULL AND url !~ '^https?://[^\s/$.?#].[^\s]*$';

-- Handle null/empty values
UPDATE coffee_articles SET
    title = CASE WHEN TRIM(title) = '' THEN NULL ELSE title END,
    content = CASE WHEN TRIM(content) = '' THEN NULL ELSE content END,
    author = CASE WHEN TRIM(author) = '' THEN NULL ELSE author END,
    source = CASE WHEN TRIM(source) = '' THEN NULL ELSE source END,
    rating = CASE WHEN TRIM(rating) = '' THEN NULL ELSE rating END;

-- Remove duplicate articles based on content hash
WITH duplicates AS (
    SELECT id, 
           ROW_NUMBER() OVER (
               PARTITION BY content_hash
               ORDER BY scraped_at DESC
           ) as rn
    FROM coffee_articles
)
DELETE FROM coffee_articles 
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- ============================================================
-- TWITTER DATA CLEANING (if any data exists)
-- ============================================================

-- Clean text fields in twitter_data table
UPDATE twitter_data SET
    keyword = TRIM(REGEXP_REPLACE(keyword, '\s+', ' ', 'g')),
    text = TRIM(REGEXP_REPLACE(text, '\s+', ' ', 'g')),
    author_id = TRIM(author_id),
    tweet_id = TRIM(tweet_id)
WHERE 
    keyword IS NOT NULL OR 
    text IS NOT NULL OR 
    author_id IS NOT NULL OR 
    tweet_id IS NOT NULL;

-- Remove special characters and fix encoding issues
UPDATE twitter_data SET
    text = REGEXP_REPLACE(text, '[^\x20-\x7E\x0A\x0D]', '', 'g')
WHERE text IS NOT NULL;

-- Handle null/empty values
UPDATE twitter_data SET
    keyword = CASE WHEN TRIM(keyword) = '' THEN NULL ELSE keyword END,
    text = CASE WHEN TRIM(text) = '' THEN NULL ELSE text END,
    author_id = CASE WHEN TRIM(author_id) = '' THEN NULL ELSE author_id END;

-- Remove duplicate tweets
WITH duplicates AS (
    SELECT id, 
           ROW_NUMBER() OVER (
               PARTITION BY tweet_id
               ORDER BY scraped_at DESC
           ) as rn
    FROM twitter_data
)
DELETE FROM twitter_data 
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- ============================================================
-- FINAL CLEANUP AND OPTIMIZATION
-- ============================================================

-- Update statistics for better query performance
ANALYZE reddit_data;
ANALYZE coffee_articles;
ANALYZE twitter_data;

-- Vacuum to reclaim space from deleted records
VACUUM reddit_data;
VACUUM coffee_articles;
VACUUM twitter_data;

-- Commit all changes
COMMIT;

-- ============================================================
-- CLEANING SUMMARY QUERIES
-- ============================================================

-- Show cleaning results
SELECT 'REDDIT DATA' as table_name, COUNT(*) as total_records FROM reddit_data
UNION ALL
SELECT 'COFFEE ARTICLES' as table_name, COUNT(*) as total_records FROM coffee_articles
UNION ALL
SELECT 'TWITTER DATA' as table_name, COUNT(*) as total_records FROM twitter_data;

-- Show data quality metrics
SELECT 
    'Reddit Posts with Clean Titles' as metric,
    COUNT(*) as count
FROM reddit_data 
WHERE title IS NOT NULL AND title !~ '\s{2,}' AND LENGTH(TRIM(title)) > 0

UNION ALL

SELECT 
    'Coffee Articles with Valid Ratings' as metric,
    COUNT(*) as count
FROM coffee_articles 
WHERE rating IS NOT NULL AND rating ~ '^[0-9]+(\.[0-9]+)?/[0-9]+$'

UNION ALL

SELECT 
    'Coffee Articles with Valid URLs' as metric,
    COUNT(*) as count
FROM coffee_articles 
WHERE url IS NOT NULL AND url ~ '^https?://[^\s/$.?#].[^\s]*$';
