from pytrends.request import TrendReq
import pandas as pd

pytrends = TrendReq(hl='en-US', tz=360, retries=3, backoff_factor=0.5)

kw_list = [
    "cold brew", "nitro coffee", "matcha latte", "oat milk latte", "mushroom coffee",
    "functional coffee", "RTD coffee", "specialty coffee", "instant coffee", "decaf coffee",
    "brown sugar latte", "flavored coffee", "capsule coffee", "pod coffee", "cloud coffee"
]

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Blacklist of words/brands you don't want
blacklist = [
    "machine", "maker", "brewer", "appliance", 
    "starbucks", "dunkin", "nespresso", "keurig", "lavazza", "tim hortons"
]

def clean_related_queries(related_queries, blacklist):
    cleaned = {}
    for kw, results in related_queries.items():
        if results and "top" in results and results["top"] is not None:
            df = results["top"]
            # filter out blacklisted queries
            df = df[~df['query'].str.contains("|".join(blacklist), case=False, na=False)]
            cleaned[kw] = df.reset_index(drop=True)
    return cleaned

# Collect all clean queries
all_clean_queries = []

for kw_chunk in chunks(kw_list, 5):
    pytrends.build_payload(kw_chunk, timeframe='today 12-m')
    related_queries = pytrends.related_queries()
    cleaned = clean_related_queries(related_queries, blacklist)
    
    for kw, df in cleaned.items():
        print(f"\n✅ Cleaned queries for {kw}:")
        print(df)
        all_clean_queries.extend(df["query"].tolist())

# Convert to unique master list
all_clean_queries = list(set(all_clean_queries))
print("\n📌 Master list of clean coffee-related queries:")
print(all_clean_queries)

# Save to JSON file with timestamp
import json
from datetime import datetime

trending_data = {
    "timestamp": datetime.now().isoformat(),
    "trending_keywords": all_clean_queries,
    "total_keywords": len(all_clean_queries)
}

with open("trending_coffee_keywords.json", "w") as f:
    json.dump(trending_data, f, indent=2)

print(f"\n✅ Saved {len(all_clean_queries)} trending keywords to trending_coffee_keywords.json")
