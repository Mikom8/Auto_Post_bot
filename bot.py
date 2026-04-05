import os
import datetime
import pytz
import random
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from groq import Groq
from duckduckgo_search import DDGS

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

client = Groq(api_key=GROQ_API_KEY)
ET_TZ = pytz.timezone('Africa/Addis_Ababa')

def get_unique_news():
    """Fetches real-time tech data across various categories"""
    categories = [
        "Android and iOS mobile updates", 
        "Nvidia and AMD GPU hardware news", 
        "SpaceX and NASA space exploration", 
        "Artificial Intelligence and LLM breakthroughs", 
        "Cybersecurity and hacking alerts", 
        "Telegram and Social Media new features",
        "PC building and CPU releases"
    ]
    query = random.choice(categories)
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"latest {query} news April 2026", max_results=3))
            if results:
                return "\n".join([f"{r['title']}: {r['body']}" for r in results])
    except Exception:
        pass
    return "Global technology trends and digital innovation."

async def generate_and_send_post(context: ContextTypes.DEFAULT_TYPE):
    """Core logic to generate and send the post"""
    news_context = get_unique_news()
    
    prompt = f"""
    Context: {news_context}
    Write a professional, viral English Telegram post for '@MIKO_TECH'.
    The post should be unique and engaging.
    
    Format:
    🌐 [Catchy Topic Title]
    [2-3 clear sentences explaining the news or tech tip]
    
    📌 Key Highlights
    • [Point 1]
    • [Point 2]
    • [Point 3]
    
    💡 Why it matters
    • [Impact on users or tech world]
    
    ⛓ Source: [A relevant or official link]\n
    
    @MIKO_TECH
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        post_text = response.choices[0].message.content.strip()
        
        post_text = post_text.replace("**", "").replace("__", "")
        
        await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
        return True
    except Exception as e:
        print(f"Generation Error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command"""
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(
            "🚀 <b>MIKO TECH Bot Active!</b>\n\n"
            "⏰ <b>Scheduled:</b> 8 AM & 8 PM (EAT)\n"
            "📝 <b>Manual:</b> Use /post to send news now.", 
            parse_mode="HTML"
        )

async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual /post command for Admin"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin access only.")
        return

    status_msg = await update.message.reply_text("🔄 Finding unique tech news and posting...")
    success = await generate_and_send_post(context)
    
    if success:
        await status_msg.edit_text("✅ Post sent to @MIKO_TECH successfully!")
    else:
        await status_msg.edit_text("❌ Failed to generate post. Check logs.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    if app.job_queue:
        app.job_queue.run_daily(
            lambda ctx: generate_and_send_post(ctx), 
            time=datetime.time(hour=8, minute=0, second=0, tzinfo=ET_TZ)
        )
        app.job_queue.run_daily(
            lambda ctx: generate_and_send_post(ctx), 
            time=datetime.time(hour=20, minute=0, second=0, tzinfo=ET_TZ)
        )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post_now))
    
    print("Miko Tech Bot is running. Manual /post and Auto-Schedules active.")
    app.run_polling()

if __name__ == "__main__":
    main()