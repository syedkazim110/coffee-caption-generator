#!/usr/bin/env python3
"""
Archive Old Data Files
Moves JSON/CSV files to archive folder after successful migration to PostgreSQL
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# Files to archive (now stored in database)
FILES_TO_ARCHIVE = [
    # Generated captions
    'llm_rag_captions.json',
    'rag_generated_captions.json',
    
    # Coffee context
    'coffee_context.json',
    
    # Hashtags
    'hashtag_knowledge_base.json',
    'coffee_hashtag_knowledge_base.json',
    
    # Trending keywords
    'trending_coffee_keywords.json',
    'coffee_hashtags_trending.json',
    
    # Social media posts
    'complete_social_media_posts.json',
    
    # Data quality reports
    'data_quality_report_*.json',
    
    # Coffee habits
    'worldwide_coffee_habits.csv',
    
    # Test outputs
    'test_knowledge_output.json',
]

def archive_files():
    """Archive old JSON/CSV files to archive folder"""
    
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_dir = f'archive/pre_migration_{timestamp}'
    os.makedirs(archive_dir, exist_ok=True)
    
    print("=" * 60)
    print("ARCHIVING OLD DATA FILES")
    print("=" * 60)
    print(f"\nArchive directory: {archive_dir}\n")
    
    archived_count = 0
    skipped_count = 0
    
    for file_pattern in FILES_TO_ARCHIVE:
        if '*' in file_pattern:
            # Handle wildcard patterns
            import glob
            matching_files = glob.glob(file_pattern)
            
            for file_path in matching_files:
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    dest = os.path.join(archive_dir, os.path.basename(file_path))
                    try:
                        shutil.move(file_path, dest)
                        print(f"✓ Archived: {file_path}")
                        archived_count += 1
                    except Exception as e:
                        print(f"✗ Error archiving {file_path}: {e}")
        else:
            # Handle single file
            if os.path.exists(file_pattern) and os.path.isfile(file_pattern):
                dest = os.path.join(archive_dir, file_pattern)
                try:
                    shutil.move(file_pattern, dest)
                    print(f"✓ Archived: {file_pattern}")
                    archived_count += 1
                except Exception as e:
                    print(f"✗ Error archiving {file_pattern}: {e}")
            else:
                print(f"⊘ Not found: {file_pattern}")
                skipped_count += 1
    
    # Create README in archive directory
    readme_content = f"""# Archive - Pre-Migration Data Files

This directory contains data files that were migrated to PostgreSQL on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}.

## Migration Details

- Migration Script: migrate_data_to_postgres.py
- Archive Date: {datetime.now().isoformat()}
- Total Files Archived: {archived_count}

## Database Location

All data is now stored in PostgreSQL database:
- Database: reddit_db
- Host: localhost
- Port: 5434

## Accessing Data

Use the `db_helper.py` module to interact with the database instead of these files.

Example:
```python
from db_helper import get_db

# Get captions from database
with get_db() as db:
    captions = db.get_captions(limit=10)
    
# Get coffee context
with get_db() as db:
    context = db.get_coffee_context()
```

## Files in This Archive

{chr(10).join([f"- {f}" for f in os.listdir(archive_dir) if f != 'README.md'])}

## Note

These files are kept for backup purposes. You can safely delete this archive folder after verifying that all data has been successfully migrated to the database.
"""
    
    readme_path = os.path.join(archive_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print("\n" + "=" * 60)
    print("ARCHIVE SUMMARY")
    print("=" * 60)
    print(f"Files archived: {archived_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Archive location: {archive_dir}")
    print(f"README created: {readme_path}")
    print("\n✓ Archival completed successfully!")
    print("\nNote: All data is now in PostgreSQL database.")
    print("Use db_helper.py to access the data.")

if __name__ == '__main__':
    response = input("\nThis will move JSON/CSV files to archive folder. Continue? (y/n): ")
    if response.lower() == 'y':
        archive_files()
    else:
        print("Archival cancelled.")
