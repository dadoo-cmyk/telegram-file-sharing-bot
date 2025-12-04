import time, uuid, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "enter your token here"
ADMIN_ID =  # Replace with your Telegram user ID

uploaded_files = {}  # token: {file_id, timestamp}
user_file_access = {}  # user_id: {file_id, expiry}

def remove_user_file(user_id):
    user_file_access.pop(user_id, None)

# ADMIN uploads a document
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not allowed to upload files.")
        return

    document = update.message.document
    file_id = document.file_id
    token = str(uuid.uuid4())

    uploaded_files[token] = {"file_id": file_id, "timestamp": time.time()}

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={token}"
    await update.message.reply_text(f"✅ File saved.\n🔗 Share this link:\n{link}")

# USER uses start with token
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Use a valid link to access the file.")
        return

    token = args[0]
    file_data = uploaded_files.get(token)
    if not file_data:
        await update.message.reply_text("❌ File not found or expired.")
        return

    user_id = update.message.from_user.id
    file_id = file_data["file_id"]

    # Send file
    await update.message.reply_document(file_id)
    await update.message.reply_text("⚠️ This file will be deleted in 30 minutes. Save it now.")

    # Set timer
    user_file_access[user_id] = {"file_id": file_id, "expiry": time.time() + 1800}
    threading.Timer(1800, remove_user_file, args=(user_id,)).start()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

