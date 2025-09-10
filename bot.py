import os
import logging
import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# Initialize OpenAI - using the latest API syntax
client = openai.OpenAI(api_key=OPENAI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I\'m an AI bot here to help answer questions in this group.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
    I'm an AI-powered bot that can answer questions in this group. 
    Just tag me with your question or ask a question in the group and I'll try to help!
    
    Commands:
    /start - Start the bot
    /help - Show this help message
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and respond to questions."""
    # Ignore messages from the bot itself
    if update.message.from_user.is_bot:
        return
        
    # Check if the message is from the group
    if str(update.message.chat.id) != GROUP_CHAT_ID:
        return
        
    message_text = update.message.text
    
    # Check if the bot is mentioned or if the message is likely a question
    is_question = (
        '?' in message_text or 
        any(word in message_text.lower() for word in ['what', 'why', 'how', 'when', 'where', 'who', 'can you', 'explain', 'help'])
    )
    
    # Only respond to questions or when directly mentioned
    bot_username = context.bot.username.lower() if context.bot.username else ""
    if not is_question and not (bot_username and bot_username in message_text.lower()):
        return
        
    try:
        # Show typing action
        await update.message.chat.send_action(action="typing")
        
        # Generate response using OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant in a Telegram group chat. Provide concise, helpful answers to questions. Keep responses under 200 words."},
                {"role": "user", "content": message_text}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        # Send the response
        await update.message.reply_text(answer)
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await update.message.reply_text("Sorry, I'm having trouble processing your question right now.")

def main():
    """Start the bot."""
    # Check if all required environment variables are set
    if not all([TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, GROUP_CHAT_ID]):
        logger.error("Please set all required environment variables: TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, GROUP_CHAT_ID")
        return
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
