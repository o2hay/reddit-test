import requests
import feedparser
from google.genai import Client
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"  
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  
client = Client(api_key=GEMINI_API_KEY)

cookies = {
}

headers = {
}

url = "https://www.reddit.com/r/tennis/top.json?limit=15&t=day"
posts = requests.get(url, headers=headers, cookies=cookies).json()['data']['children']
hot_issues = []
for p in posts:
    data = p['data']
    if not any(w in data['title'].lower() for w in ['score', 'highlights', 'result']) and data['num_comments'] > 30:
        hot_issues.append(data)
    if len(hot_issues) >= 5:
        break

daily_report = "🎾 *Today's Report* 🎾\n\n"

for i, p in enumerate(hot_issues + kr_issues, 1):
    is_reddit = 'permalink' in p
    title = p['title'] if is_reddit else p.title
    link = f"https://www.reddit.com{p['permalink']}" if is_reddit else p.link
    
    content = ""
    if is_reddit:
        res = requests.get(f"{link.rstrip('/')}.json", headers=headers, cookies=cookies).json()
        raw_comments = [c['data'] for c in res[1]['data']['children'] if 'body' in c['data']]
        sorted_comments = sorted(raw_comments, key=lambda x: x.get('ups', 0), reverse=True)[:4]
        content = "\n".join([f"💬 (rec:{c.get('ups')}) {c['body']}" for c in sorted_comments])
        
    prompt = f"""
    Summary belows

    Subject: {title}
    Contents: {content}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash', 
        contents=prompt
    )
    
    tag = '[Buzz]'
    daily_report += f"🔥 *{tag}*\n{response.text.strip()}\n\n🔗 원문: {link}\n\n---\n\n"


if TELEGRAM_TOKEN != "YOUR_BOT_TOKEN":
    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": daily_report
    }
    
    res = requests.post(telegram_api_url, data=payload)
    if res.status_code == 200:
        print("✅ Done!")
    else:
        print(f"❌ Failed: {res.text}")
else:
    print("⚠️ Token not found")
    print(daily_report)
