import requests
import random
import json
import time
import threading
import google.generativeai as genai
from flask import Flask

# --- CONFIGURATION & TOKENS ---
TELEGRAM_TOKEN = "8020220704:AAHX_bnLkv6YScy8YauPD7CMOOG6XaEXwHU"
GEMINI_API_KEY = "AIzaSyD55vdY2oTE9CAAmx1B70GGPq-oGh7uqXI"
NEWS_API_KEY = "0544a632a0534e04802dd6e71f5d5b1c"
RENDER_URL = "https://monster-nnd2.onrender.com" # তোর স্ক্রিনশট থেকে পাওয়া লিঙ্ক

NASA_TOKENS = [
    "haWU96o6AG2uIoXvsm3m2f3clop9e0aceP8LDEbc",
    "LOCtHcJdOeU1eLYsx8Q1X5WO5Nl3vmcANIB8werP",
    "v5HVdElCYhwg7DC9ifqDJdbjZgVLmWK2EIH3cG7n",
    "RuPystwisOD4LEQGsK1lT0TtcrV6PhA9DURlWOFK"
]
curr_nasa = 0
stats = {"total_imgs": 0, "users": set()}
user_modes = {}

# Gemini AI Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

app = Flask('')

@app.route('/')
def home():
    return f"Bot is alive! Images sent: {stats['total_imgs']}"

# --- CORE FUNCTIONS ---
def get_gemini_reply(text):
    try:
        response = model.generate_content(text)
        return response.text
    except: return "AI is currently resting. Try again later!"

def get_nasa():
    global curr_nasa
    date_str = f"{random.randint(2018, 2025)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
    for _ in range(len(NASA_TOKENS)):
        token = NASA_TOKENS[curr_nasa]
        url = f"https://api.nasa.gov/planetary/apod?api_key={token}&date={date_str}"
        res = requests.get(url)
        curr_nasa = (curr_nasa + 1) % len(NASA_TOKENS)
        if res.status_code == 200: return res.json().get('url'), res.json().get('title')
    return "https://picsum.photos/800/600", "NASA Limit Reached"

def get_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        art = random.choice(res['articles'])
        return art['urlToImage'] or "https://picsum.photos/800/600", art['title']
    except: return "https://picsum.photos/800/600", "News not found!"

# --- TELEGRAM BOARD ---
def send_board(chat_id, img_url, caption):
    stats["total_imgs"] += 1
    stats["users"].add(chat_id)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    markup = {"inline_keyboard": [
        [{"text": "🚀 NASA", "callback_data": "m_nasa"}, {"text": "📰 NEWS", "callback_data": "m_news"}],
        [{"text": "🐱 CAT", "callback_data": "m_cat"}, {"text": "🐶 DOG", "callback_data": "m_dog"}],
        [{"text": "🎎 ANIME", "callback_data": "m_waifu"}, {"text": "😂 JOKE", "callback_data": "m_joke"}],
        [{"text": "💡 FACT", "callback_data": "m_fact"}, {"text": "📜 QUOTE", "callback_data": "m_quote"}],
        [{"text": "📊 STATS", "callback_data": "m_stats"}, {"text": "🔄 NEW IMAGE", "callback_data": "fetch_new"}]
    ]}
    requests.post(url, data={"chat_id": chat_id, "photo": img_url, "caption": caption, "reply_markup": json.dumps(markup)})

# --- KEEP ALIVE ---
def keep_alive():
    while True:
        try: requests.get(RENDER_URL); print("Self-ping success!")
        except: pass
        time.sleep(30) # ৩০ সেকেন্ডের টাইমার

# --- MAIN BOT LOOP ---
def run_bot():
    last_id = 0
    threading.Thread(target=keep_alive, daemon=True).start()
    print("Bot is starting...")
    while True:
        try:
            updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_id + 1}", timeout=30).json()
            for up in updates.get("result", []):
                last_id = up["update_id"]
                chat_id = up.get("message", {}).get("chat", {}).get("id") or up.get("callback_query", {}).get("message", {}).get("chat", {}).get("id")
                
                if "callback_query" in up:
                    data = up["callback_query"]["data"]
                    if data == "m_stats":
                        msg = f"📊 Stats:\nImages: {stats['total_imgs']}\nUsers: {len(stats['users'])}"
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": msg})
                    elif data == "m_nasa": i, t = get_nasa(); send_board(chat_id, i, t)
                    elif data == "m_news": i, t = get_news(); send_board(chat_id, i, t)
                    elif data == "m_waifu":
                        r = requests.get("https://waifu.pics/api/sfw/waifu").json()
                        send_board(chat_id, r['url'], "Anime Style! ✨")
                    elif data == "m_joke":
                        r = requests.get("https://official-joke-api.appspot.com/random_joke").json()
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": f"{r['setup']}\n\n{r['punchline']}"})
                    elif data == "m_fact":
                        r = requests.get("https://uselessfacts.jsph.pl/random.json?language=en").json()
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": f"Did you know?\n{r['text']}"})
                    elif data == "m_quote":
                        r = requests.get("https://api.quotable.io/random").json()
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": f"\"{r['content']}\"\n- {r['author']}"})
                
                elif "message" in up and "text" in up["message"]:
                    txt = up["message"]["text"]
                    if txt == "/start": i, t = get_nasa(); send_board(chat_id, i, t)
                    else: 
                        reply = get_gemini_reply(txt)
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": reply})
        except: time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()
    run_bot()
