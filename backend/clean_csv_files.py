#!/usr/bin/env python3
"""
CSV File Cleaning Utility
Cleans large CSV files in chunks to handle memory efficiently
Applies the same cleaning rules as the database cleaning script
"""

import pandas as pd
import re
import os
import sys
from datetime import datetime
import numpy as np

class CSVCleaner:
    def __init__(self, chunk_size=1000):
        self.chunk_size = chunk_size
        self.cleaning_stats = {
            'total_rows_processed': 0,
            'rows_cleaned': 0,
            'duplicates_removed': 0,
            'invalid_data_fixed': 0
        }
    
    def clean_text_field(self, text):
        """Clean a single text field"""
        if pd.isna(text) or text == '':
            return None
        
        # Convert to string if not already
        text = str(text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters and fix encoding issues
        text = re.sub(r'[^\x20-\x7E\x0A\x0D]', '', text)
        
        # Return None if empty after cleaning
        return text if text.strip() else None
    
    def clean_url(self, url):
        """Clean and validate URL"""
        if pd.isna(url) or url == '':
            return None
        
        url = str(url).strip().lower()
        
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if re.match(url_pattern, url):
            return url
        else:
            return None
    
    def standardize_rating(self, rating):
        """Standardize rating formats"""
        if pd.isna(rating) or rating == '':
            return None
        
        rating = str(rating).strip()
        
        # Already in X/Y format
        if re.match(r'^[0-9]+(\.[0-9]+)?/[0-9]+$', rating):
            return rating
        
        # Numeric rating, assume out of 5 if <= 5, out of 10 if <= 10
        if re.match(r'^[0-9]+(\.[0-9]+)?$', rating):
            num_rating = float(rating)
            if num_rating <= 5:
                return f"{rating}/5"
            elif num_rating <= 10:
                return f"{rating}/10"
        
        # Percentage rating
        if re.match(r'^[0-9]+(\.[0-9]+)?%$', rating):
            percent = float(rating.replace('%', ''))
            converted = round((percent / 100 * 5), 1)
            return f"{converted}/5"
        
        # Text ratings
        rating_lower = rating.lower()
        text_ratings = {
            'excellent': '5/5', 'outstanding': '5/5',
            'very good': '4/5', 'great': '4/5',
            'good': '3/5', 'decent': '3/5',
            'fair': '2/5', 'okay': '2/5',
            'poor': '1/5', 'bad': '1/5'
        }
        
        return text_ratings.get(rating_lower, None)
    
    def clean_reddit_data_chunk(self, chunk):
        """Clean a chunk of Reddit data"""
        original_count = len(chunk)
        
        # Clean text fields
        text_columns = ['keyword', 'subreddit', 'title', 'content']
        for col in text_columns:
            if col in chunk.columns:
                chunk[col] = chunk[col].apply(self.clean_text_field)
        
        # Remove rows where title and content are both null
        chunk = chunk.dropna(subset=['title', 'content'], how='all')
        
        cleaned_count = len(chunk)
        self.cleaning_stats['rows_cleaned'] += (original_count - cleaned_count)
        
        return chunk
    
    def clean_coffee_articles_chunk(self, chunk):
        """Clean a chunk of coffee articles data"""
        original_count = len(chunk)
        
        # Clean text fields
        text_columns = ['title', 'content', 'author', 'source']
        for col in text_columns:
            if col in chunk.columns:
                chunk[col] = chunk[col].apply(self.clean_text_field)
        
        # Clean and validate URLs
        if 'url' in chunk.columns:
            chunk['url'] = chunk['url'].apply(self.clean_url)
        
        # Standardize ratings
        if 'rating' in chunk.columns:
            chunk['rating'] = chunk['rating'].apply(self.standardize_rating)
        
        # Remove rows where title is null (essential field)
        chunk = chunk.dropna(subset=['title'])
        
        cleaned_count = len(chunk)
        self.cleaning_stats['rows_cleaned'] += (original_count - cleaned_count)
        
        return chunk
    
    def clean_twitter_data_chunk(self, chunk):
        """Clean a chunk of Twitter data"""
        original_count = len(chunk)
        
        # Clean text fields
        text_columns = ['keyword', 'text']
        for col in text_columns:
            if col in chunk.columns:
                chunk[col] = chunk[col].apply(self.clean_text_field)
        
        # Clean ID fields
        id_columns = ['tweet_id', 'author_id']
        for col in id_columns:
            if col in chunk.columns:
                chunk[col] = chunk[col].apply(lambda x: str(x).strip() if pd.notna(x) and x != '' else None)
        
        # Remove rows where text is null (essential field)
        chunk = chunk.dropna(subset=['text'])
        
        cleaned_count = len(chunk)
        self.cleaning_stats['rows_cleaned'] += (original_count - cleaned_count)
        
        return chunk
    
    def remove_duplicates_from_file(self, file_path, subset_columns):
        """Remove duplicates from cleaned file"""
        print(f"Removing duplicates from {file_path}...")
        
        # Read the cleaned file
        df = pd.read_csv(file_path)
        original_count = len(df)
        
        # Remove duplicates based on specified columns
        df = df.drop_duplicates(subset=subset_columns, keep='last')
        
        final_count = len(df)
        duplicates_removed = original_count - final_count
        
        # Save back to file
        df.to_csv(file_path, index=False)
        
        self.cleaning_stats['duplicates_removed'] += duplicates_removed
        print(f"Removed {duplicates_removed} duplicates from {file_path}")
    
    def clean_csv_file(self, input_file, output_file, data_type):
        """Clean a CSV file in chunks"""
        print(f"Cleaning {input_file} -> {output_file}")
        print(f"Data type: {data_type}")
        
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            return False
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Process file in chunks
            chunk_count = 0
            first_chunk = True
            
            for chunk in pd.read_csv(input_file, chunksize=self.chunk_size):
                chunk_count += 1
                self.cleaning_stats['total_rows_processed'] += len(chunk)
                
                print(f"Processing chunk {chunk_count} ({len(chunk)} rows)...")
                
                # Apply appropriate cleaning based on data type
                if data_type == 'reddit':
                    cleaned_chunk = self.clean_reddit_data_chunk(chunk)
                elif data_type == 'coffee':
                    cleaned_chunk = self.clean_coffee_articles_chunk(chunk)
                elif data_type == 'twitter':
                    cleaned_chunk = self.clean_twitter_data_chunk(chunk)
                else:
                    print(f"❌ Unknown data type: {data_type}")
                    return False
                
                # Write to output file
                mode = 'w' if first_chunk else 'a'
                header = first_chunk
                cleaned_chunk.to_csv(output_file, mode=mode, header=header, index=False)
                first_chunk = False
            
            print(f"✅ Cleaned {input_file} successfully")
            
            # Remove duplicates based on data type
            if data_type == 'reddit':
                self.remove_duplicates_from_file(output_file, ['title', 'content'])
            elif data_type == 'coffee':
                self.remove_duplicates_from_file(output_file, ['title', 'url'])
            elif data_type == 'twitter':
                self.remove_duplicates_from_file(output_file, ['tweet_id'])
            
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning {input_file}: {str(e)}")
            return False
    
    def print_cleaning_stats(self):
        """Print cleaning statistics"""
        print("\n" + "="*50)
        print("CSV CLEANING STATISTICS")
        print("="*50)
        print(f"Total rows processed: {self.cleaning_stats['total_rows_processed']}")
        print(f"Rows cleaned/removed: {self.cleaning_stats['rows_cleaned']}")
        print(f"Duplicates removed: {self.cleaning_stats['duplicates_removed']}")
        print(f"Invalid data fixed: {self.cleaning_stats['invalid_data_fixed']}")
        print("="*50)

def main():
    """Main function to clean all CSV files"""
    cleaner = CSVCleaner(chunk_size=1000)
    
    # Define file mappings: (input_file, output_file, data_type)
    file_mappings = [
        ('reddit_data_export.csv', 'cleaned_reddit_data.csv', 'reddit'),
        ('coffee_articles_export.csv', 'cleaned_coffee_articles.csv', 'coffee'),
        ('coffee_articles.csv', 'cleaned_coffee_articles_backup.csv', 'coffee'),
        ('worldwide_coffee_habits.csv', 'cleaned_worldwide_coffee_habits.csv', 'coffee'),
    ]
    
    print("Starting CSV cleaning process...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = 0
    total_files = len(file_mappings)
    
    for input_file, output_file, data_type in file_mappings:
        if os.path.exists(input_file):
            if cleaner.clean_csv_file(input_file, output_file, data_type):
                success_count += 1
        else:
            print(f"⚠️  Skipping {input_file} (file not found)")
    
    print(f"\n✅ Cleaning completed: {success_count}/{total_files} files processed successfully")
    cleaner.print_cleaning_stats()

if __name__ == "__main__":
    main()
