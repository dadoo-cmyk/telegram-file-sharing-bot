import time, uuid, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "enter your token here"
ADMIN_ID =  # Replace with your Telegram user ID

uploaded_content = {}  # token: {type, content, timestamp}
user_content_access = {}  # user_id: {content, expiry}

def remove_user_content(user_id):
    user_content_access.pop(user_id, None)

# ADMIN uploads a document or text
async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not allowed to upload content.")
        return

    content_type = None
    content = None
    
    # Check if it's a document
    if update.message.document:
        content_type = "document"
        content = update.message.document.file_id
        original_message = "📄 File"
    # Check if it's a photo
    elif update.message.photo:
        content_type = "photo"
        content = update.message.photo[-1].file_id  # Get highest resolution photo
        original_message = "🖼️ Photo"
    # Check if it's text
    elif update.message.text:
        content_type = "text"
        content = update.message.text
        original_message = "📝 Text message"
    # Check if it's audio
    elif update.message.audio:
        content_type = "audio"
        content = update.message.audio.file_id
        original_message = "🎵 Audio"
    # Check if it's video
    elif update.message.video:
        content_type = "video"
        content = update.message.video.file_id
        original_message = "🎬 Video"
    # Check if it's voice message
    elif update.message.voice:
        content_type = "voice"
        content = update.message.voice.file_id
        original_message = "🎤 Voice message"
    # Check if it's sticker
    elif update.message.sticker:
        content_type = "sticker"
        content = update.message.sticker.file_id
        original_message = "😀 Sticker"
    else:
        await update.message.reply_text("❌ Unsupported content type.")
        return

    token = str(uuid.uuid4())
    uploaded_content[token] = {
        "type": content_type,
        "content": content,
        "timestamp": time.time(),
        "original_type": original_message
    }

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={token}"
    
    await update.message.reply_text(
        f"✅ {original_message} saved.\n"
        f"🔗 Share this link:\n{link}\n"
        f"📋 Token: {token}"
    )

# USER uses start with token
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Welcome! 👋\n"
            "Use a valid link to access content.\n\n"
            "Admin commands:\n"
            "/upload - Upload a file or text\n"
            "/list - List all shared content\n"
            "/delete <token> - Delete content"
        )
        return

    token = args[0]
    content_data = uploaded_content.get(token)
    
    if not content_data:
        await update.message.reply_text("❌ Content not found or expired.")
        return

    user_id = update.message.from_user.id
    content_type = content_data["type"]
    content = content_data["content"]
    original_type = content_data["original_type"]

    # Send content based on type
    try:
        if content_type == "document":
            await update.message.reply_document(content)
        elif content_type == "photo":
            await update.message.reply_photo(content)
        elif content_type == "text":
            await update.message.reply_text(f"📝 Message:\n\n{content}")
        elif content_type == "audio":
            await update.message.reply_audio(content)
        elif content_type == "video":
            await update.message.reply_video(content)
        elif content_type == "voice":
            await update.message.reply_voice(content)
        elif content_type == "sticker":
            await update.message.reply_sticker(content)
        
        await update.message.reply_text(
            f"⚠️ This {original_type.lower()} will be deleted in 30 minutes. Save it now."
        )

        # Set timer for deletion
        user_content_access[user_id] = {
            "content": content,
            "expiry": time.time() + 1800,
            "type": content_type
        }
        threading.Timer(1800, remove_user_content, args=(user_id,)).start()
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending content: {str(e)}")

# ADMIN command to list all shared content
async def list_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not uploaded_content:
        await update.message.reply_text("📭 No content has been shared yet.")
        return
    
    message = "📋 Shared Content:\n\n"
    for token, data in uploaded_content.items():
        time_ago = int((time.time() - data["timestamp"]) / 60)  # minutes ago
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={token}"
        message += f"• {data['original_type']}\n"
        message += f"  Token: {token}\n"
        message += f"  Link: {link}\n"
        message += f"  Shared: {time_ago} minutes ago\n"
        message += f"  Preview: {str(data['content'])[:50]}...\n\n"
    
    await update.message.reply_text(message)

# ADMIN command to delete content
async def delete_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /delete <token>")
        return
    
    token = context.args[0]
    
    if token in uploaded_content:
        del uploaded_content[token]
        await update.message.reply_text(f"✅ Content with token '{token}' deleted.")
    else:
        await update.message.reply_text("❌ Token not found.")

# ADMIN command to clear all content
async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    count = len(uploaded_content)
    uploaded_content.clear()
    await update.message.reply_text(f"✅ Cleared all {count} items.")

# Command to show help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Secure Content Sharing Bot**\n\n"
        "**For Users:**\n"
        "• Click on shared links to access content\n"
        "• Content auto-deletes after 30 minutes\n\n"
        "**For Admin:**\n"
        "• Send any file/text to upload\n"
        "• Bot will generate a shareable link\n"
        "• Commands:\n"
        "  /upload - Upload content\n"
        "  /list - List all shared content\n"
        "  /delete <token> - Delete content\n"
        "  /clear - Clear all content\n"
        "  /stats - Show statistics\n\n"
        "📌 Supported content: Files, Photos, Text, Audio, Video, Voice, Stickers"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Command to show statistics
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        f"• Total shared content: {len(uploaded_content)}\n"
        f"• Active user sessions: {len(user_content_access)}\n"
        f"• Bot uptime: N/A\n\n"
        f"**Content Breakdown:**\n"
    )
    
    # Count content by type
    type_count = {}
    for data in uploaded_content.values():
        content_type = data["original_type"]
        type_count[content_type] = type_count.get(content_type, 0) + 1
    
    for content_type, count in type_count.items():
        stats_text += f"  {content_type}: {count}\n"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# Auto-cleanup old content (older than 24 hours)
def cleanup_old_content():
    current_time = time.time()
    old_tokens = []
    
    for token, data in uploaded_content.items():
        if current_time - data["timestamp"] > 86400:  # 24 hours
            old_tokens.append(token)
    
    for token in old_tokens:
        del uploaded_content[token]
    
    if old_tokens:
        print(f"Cleaned up {len(old_tokens)} old items.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_content))
    app.add_handler(CommandHandler("delete", delete_content))
    app.add_handler(CommandHandler("clear", clear_all))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("upload", handle_content))  # For explicit upload command
    
    # Handle all messages from admin (files, text, photos, etc.)
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.TEXT | filters.PHOTO | 
        filters.AUDIO | filters.VIDEO | filters.VOICE | filters.STICKER, 
        handle_content
    ))
    
    # Setup cleanup timer (every hour)
    cleanup_timer = threading.Timer(3600, cleanup_old_content)
    cleanup_timer.start()
    
    print("🤖 Bot is running...")
    print("Supported content types: Files, Text, Photos, Audio, Video, Voice, Stickers")
    app.run_polling()

if __name__ == '__main__':
    main()
