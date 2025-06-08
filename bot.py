import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes,
    CallbackQueryHandler, ConversationHandler
)

# === Bot Token and Admin ID ===
BOT_TOKEN = "8151429137:AAEZb095wNIkxujeKqXIzXWHycNaIOB15_0"
ADMIN_CHAT_ID = 6387122230

# === States ===
EMAIL, FULL_NAME, CONFIRMATION, PAYMENT_RECEIPT = range(4)

# === In-Memory Store ===
user_data_store = {}
message_map = {}

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Join Group", callback_data='join_group'),
         InlineKeyboardButton("Get QDX Code", callback_data='get_qdx_code')],
        [InlineKeyboardButton("About", callback_data='about'),
         InlineKeyboardButton("Sign Up", callback_data='sign_up')],
        [InlineKeyboardButton("Live Chat", callback_data='live_chat')]
    ]
    await update.message.reply_text("👋 Welcome to *Qudox Bot*! Choose an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# === Button Handler ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'join_group':
        await query.edit_message_text(
            "📢 Join our communities:\n"
            "🔗 WhatsApp: https://chat.whatsapp.com/GS1vYWpDidE4h0IMJyr8Uo\n"
            "🔗 Telegram: https://t.me/QudoxOfficial"
        )
    elif query.data == 'sign_up':
        await query.edit_message_text("📝 Sign up here:\nhttps://qudox.netlify.app")
    elif query.data == 'about':
        await query.edit_message_text(
            "🤑 *What is Qudox?*\n\n"
            "Qudox is a *tap to earn Naira* platform where you earn money by completing simple tasks daily.\n\n"
            "💼 Services we offer:\n"
            "• Task earnings (like and share)\n"
            "• QDX Code registration system\n"
            "• Access to exclusive communities\n\n"
            "🎯 Perfect for Nigerians looking to earn online easily.\n\n"
            "🌐 Visit: https://qudox.netlify.app",
            parse_mode="Markdown"
        )
    elif query.data == 'get_qdx_code':
        await query.edit_message_text("📧 Please send your *email address*:", parse_mode="Markdown")
        return EMAIL
    elif query.data == 'live_chat':
        await query.edit_message_text("💬 Please type your message below. Our admin will reply shortly.")
        return ConversationHandler.END

# === QDX Code Flow ===
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {'email': update.message.text}
    await update.message.reply_text("👤 Now enter your *full name*:", parse_mode="Markdown")
    return FULL_NAME

async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id]['full_name'] = update.message.text
    data = user_data_store[user_id]
    text = (
        f"🔍 Please confirm your details:\n\n"
        f"📧 Email: {data['email']}\n"
        f"👤 Full Name: {data['full_name']}\n\n"
        f"✅ Tap *Continue* if this is correct."
    )
    keyboard = [[InlineKeyboardButton("Continue ✅", callback_data='confirm_details')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CONFIRMATION

async def confirm_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = user_data_store.get(user_id)

    await query.edit_message_text(
        "💳 *Payment Details:*\n\n"
        "Pay *₦5000* to:\n"
        "🏦 *Chipper Cash / Chukwuma Bridget*\n"
        "🔢 *Acct No:* 6094827567\n"
        "🏦 *Bank:* 9 Payment Service Bank\n\n"
        "📩 After payment, send a screenshot or message here.\n"
        "Your QDX code will be emailed to you shortly.",
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"🆕 New QDX Code Request:\n📧 Email: {data['email']}\n👤 Name: {data['full_name']}\n🆔 User ID: {user_id}"
    )
    return PAYMENT_RECEIPT

# === Handle Receipt (Photo or Text) ===
async def get_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Forward photo
    if update.message.photo:
        file = update.message.photo[-1].file_id
        caption = f"📸 Payment Screenshot from @{user.username or user.first_name} (ID: {user.id})"
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=file, caption=caption)
    elif update.message.text:
        # Forward text
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"💬 Payment text from @{user.username or user.first_name} (ID: {user.id}):\n{update.message.text}"
        )

    await update.message.reply_text("✅ Receipt sent! We’ll verify and send your QDX code soon.")
    return ConversationHandler.END

# === Live Chat System ===

# User sends message -> Admin gets it
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_CHAT_ID:
        return

    msg = await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📨 Message from @{user.username or user.first_name} (ID: {user.id}):\n\n{update.message.text}"
    )
    message_map[msg.message_id] = user.id
    await update.message.reply_text("📩 Your message has been sent to the admin.")

# Admin replies -> User gets it
async def reply_from_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    if update.message.reply_to_message:
        original_id = update.message.reply_to_message.message_id
        user_id = message_map.get(original_id)

        if user_id:
            await context.bot.send_message(chat_id=user_id, text=f"👮 Admin: {update.message.text}")
        else:
            await update.message.reply_text("⚠️ Cannot find user to reply to.")
    else:
        await update.message.reply_text("ℹ️ Reply to a user message to send them a response.")

# === Commands ===
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆘 Use /start to begin or tap a button in the menu.")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and working.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled. Use /start to begin again.")
    return ConversationHandler.END

# === Fallback ===
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Unknown command. Use /help")

# === Main ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # QDX conversation
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            CONFIRMATION: [CallbackQueryHandler(confirm_details, pattern='confirm_details')],
            PAYMENT_RECEIPT: [
                MessageHandler(filters.TEXT | filters.PHOTO, get_payment_receipt)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_CHAT_ID), reply_from_admin))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, forward_to_admin))

    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    print("✅ Qudox Bot is live!")
    app.run_polling()

if __name__ == "__main__":
    main()