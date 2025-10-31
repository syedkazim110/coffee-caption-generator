import praw
import time
import psycopg2
import json
reddit = praw.Reddit(
    client_id="28brhYxU0F0LZBTFysKD-Q",
    client_secret="daF9wgR6qEegncYI-s9NW54tYtiyxQ",
    user_agent="coffee-trends-bot"
)

master_list = ['almond milk', 'ryze coffee', 'mushroom coffee benefits', 'decaf coffee caffeine', 'iced matcha', 'specialty coffee barcelona', 
               'nescafe decaf coffee', 'best flavored coffee', 'benefits of mushroom coffee', 'nitro coffee near me', 'mushroom coffee caffeine', 
               'decaf flavored coffee', 'ryze mushroom', 'cold brew latte', 'vanilla cream cold brew', 'what is specialty coffee', 'ryze coffee reviews', 
               'how much caffeine in coffee', 'four sigmatic', 'stok cold brew', 'the best mushroom coffee', 'best cold brew coffee', 'white cloud coffee', 
               'good decaf coffee', 'instant coffee packets', 'caffeine in cold brew', 'best mushroom coffee', 'swiss water decaf coffee', 'specialty coffee paris', 
               'coffee near me', 'calories in oat milk latte', 'decaf coffee caffeine content', 'specialty coffee amsterdam', 'ryze', 
               'ono specialty coffee & matcha', 'what is matcha', 'specialty coffee london', 'hazelnut flavored coffee', 'coffee shop', 'matcha latte powder', 
               'flavored coffee creamer', 'organic mushroom coffee', 'matcha latte recipe', 'matcha latte caffeine', 'matcha near me', 'specialty coffee madrid', 
               'folgers instant coffee', 'flavored coffee pods', 'akasa specialty coffee', 'nitro coffee can', 'decaf coffee while pregnant', 'oat latte calories', 
               'specialty coffee association', 'strawberry matcha', 'cold brew recipe', 'decaf coffee benefits', 'how much caffeine in instant coffee', 
               'calories in oat milk', 'best decaf coffee', 'four sigmatic mushroom coffee', 'iced brown sugar latte', 'cat and cloud coffee', 
               'cold brew concentrate', 'cold and brew', 'specialty coffee singapore', 'iced latte with oat milk', 'dose mushroom coffee', 
               'mushroom coffee reviews', 'nitro cold brew', 'how much caffeine is in decaf coffee', 'does decaf coffee have caffeine', 
               'nescafe instant coffee', 'indonesia specialty coffee', 'cold brew coffee', 'decaf coffee pods', 'blueberry flavored coffee', 
               'how to make cold brew', 'ryze mushroom coffee reviews', 'cat cloud coffee', 'what is instant coffee', 'chai latte', 
               'nitro coffee wisma nugra santana', 'matcha latte with oat milk', 'specialty coffee roasters', 'whole bean decaf coffee', 
               'chai matcha latte', 'speciality coffee', 'caffeine in instant coffee', 'multi functional coffee table', 'how to make cold brew coffee', 
               'what is nitro coffee', 'what is decaf coffee', 'oat milk latte calories', 'specialty coffee shop', 'instant coffee powder', 
               'caramel flavored coffee', 'decaf coffee instant', 'chocolate flavored coffee', 'good instant coffee', 'matcha tea', 
               'is mushroom coffee good for you', 'instant coffee caffeine content', 'what is a decaf coffee', 'coconut flavored coffee', 
               'matcha latte near me', 'mushroom tea', 'mushroom coffee near me', 'instant espresso', 'decaf coffee meaning', 
               'flavored coffee beans', 'oat milk calories', 'ground coffee', 'what is cold brew', 'vanilla cold brew', 'ryze reviews', 'instant coffee calories', 
               'how to make instant coffee', 'decaf coffee pregnancy', 'how to make matcha latte', 'navy specialty coffee', 'matcha strawberry latte', 
               'everyday dose coffee', 'cold brew', 'vanilla oat milk latte', 'mushroom coffee amazon', 'iced latte', 'iced matcha latte', 
               'what is mushroom coffee', 'mushroom coffee ryze', 'matcha coffee', 'what is matcha latte', 'ryze mushroom coffee benefits', 
               'how to make flavored coffee', 'best pod coffee', 'instant coffee caffeine', 'matcha latte', 'how to cold brew coffee', 
               'specialty coffee beans', 'everyday dose', 'sweet cream cold brew', 'nescafe gold instant coffee', 'tiong hoe specialty coffee', 
               'matcha tea latte', 'organic decaf coffee', 'specialty coffee meaning', 'specialty instant coffee', 'the best instant coffee', 
               'cold brew espresso', 'how much caffeine in cold brew', 'matcha latte calories', 'best instant coffee', 'decaf coffee near me', 
               'matcha powder', 'specialty coffee near me', 'caffeine in decaf coffee', 'cloud coffee recipe', 'cold brew tea', 'social specialty coffee', 
               'matcha oat milk latte', 'is decaf coffee bad for you', 'organic instant coffee', 'nescafe coffee', 'instant coffee brands', 
               'how much caffeine in decaf coffee', 'nescafe', 'how to make matcha', 'rita specialty coffee', 'iced oat milk latte']
results = []

for keyword in master_list:
    print(f"\n Searching Reddit for: {keyword}")
    for submission in reddit.subreddit("all").search(keyword, limit=5, sort="new"):
        post_data = {
            "keyword": keyword,
            "subreddit": submission.subreddit.display_name,
            "title": submission.title,
            "content": submission.selftext,
            "score": submission.score,
            "created_utc": submission.created_utc,
            "comments": []
        }

        # Get comments
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list()[:20]:  # first 20 comments
            post_data["comments"].append(comment.body)

        results.append(post_data)

    time.sleep(1)  
try:
    conn = psycopg2.connect(
        host="localhost",
        port="5434",
        database="reddit_db",
        user="postgres",
        password="password"
    )
    cursor = conn.cursor()
    
    print(f"\n💾 Saving {len(results)} posts to database...")
    
    for r in results:
        cursor.execute("""
            INSERT INTO reddit_data (keyword, subreddit, title, content, score, created_utc, comments)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (r['keyword'], r['subreddit'], r['title'], r['content'], r['score'], r['created_utc'], json.dumps(r['comments'])))
    
    conn.commit()
    print(f"✅ Successfully saved {len(results)} posts to PostgreSQL database!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f" Database error: {e}")
    # print("Make sure PostgreSQL is running with: docker compose up -d")
