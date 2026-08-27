import os
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

BUTTON_FILE = "button.json"

BUTTON_TEXT, BUTTON_URL = range(2)


def load_button():
    if not os.path.exists(BUTTON_FILE):
        return None

    try:
        with open(BUTTON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_button(text, url):
    with open(BUTTON_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "text": text,
                "url": url
            },
            f,
            ensure_ascii=False
        )


def delete_button():
    if os.path.exists(BUTTON_FILE):
        os.remove(BUTTON_FILE)


def get_keyboard():

    button = load_button()

    if not button:
        return None

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                button["text"],
                url=button["url"]
            )
        ]
    ])


def is_admin(update):

    return (
        update.effective_user
        and update.effective_user.id == ADMIN_ID
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return

    await update.message.reply_text(
        "🤖 بات آماده است!\n\n"
        "/setbutton - تنظیم دکمه\n"
        "/button - نمایش دکمه\n"
        "/deletebutton - حذف دکمه\n\n"
        "بعد از تنظیم دکمه، فقط پست را برای من Forward کن."
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"🆔 ID شما:\n{update.effective_user.id}"
    )


async def setbutton_start(update, context):

    if not is_admin(update):
        return ConversationHandler.END

    await update.message.reply_text(
        "🔘 متن دکمه را بفرست:"
    )

    return BUTTON_TEXT


async def setbutton_text(update, context):

    if not is_admin(update):
        return ConversationHandler.END

    context.user_data["button_text"] = update.message.text

    await update.message.reply_text(
        "🔗 حالا لینک دکمه را بفرست:"
    )

    return BUTTON_URL


async def setbutton_url(update, context):

    if not is_admin(update):
        return ConversationHandler.END

    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):

        await update.message.reply_text(
            "❌ لینک باید با http:// یا https:// شروع شود."
        )

        return BUTTON_URL

    text = context.user_data["button_text"]

    save_button(text, url)

    await update.message.reply_text(
        f"✅ دکمه ذخیره شد!\n\n"
        f"متن: {text}\n"
        f"لینک: {url}\n\n"
        "حالا فقط پست را برای بات Forward کن."
    )

    return ConversationHandler.END


async def cancel(update, context):

    await update.message.reply_text(
        "❌ لغو شد."
    )

    return ConversationHandler.END


async def show_button(update, context):

    if not is_admin(update):
        return

    button = load_button()

    if not button:

        await update.message.reply_text(
            "❌ هنوز دکمه‌ای تنظیم نشده."
        )

        return

    await update.message.reply_text(
        f"🔘 دکمه فعلی:\n\n"
        f"{button['text']}\n"
        f"{button['url']}",
        reply_markup=get_keyboard()
    )


async def remove_button(update, context):

    if not is_admin(update):
        return

    delete_button()

    await update.message.reply_text(
        "🗑 دکمه حذف شد."
    )


async def handle_post(update, context):

    if not is_admin(update):
        return

    message = update.effective_message

    keyboard = get_keyboard()

    if not keyboard:

        await message.reply_text(
            "⚠️ اول /setbutton را تنظیم کن."
        )

        return

    try:

        if message.photo:

            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=message.photo[-1].file_id,
                caption=message.caption or "",
                reply_markup=keyboard
            )

        elif message.video:

            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=message.video.file_id,
                caption=message.caption or "",
                reply_markup=keyboard
            )

        elif message.document:

            await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=message.document.file_id,
                caption=message.caption or "",
                reply_markup=keyboard
            )

        elif message.audio:

            await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=message.audio.file_id,
                caption=message.caption or "",
                reply_markup=keyboard
            )

        elif message.voice:

            await context.bot.send_voice(
                chat_id=CHANNEL_ID,
                voice=message.voice.file_id,
                reply_markup=keyboard
            )

        elif message.text:

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message.text,
                reply_markup=keyboard
            )

        else:

            await message.reply_text(
                "⚠️ این نوع پیام فعلاً پشتیبانی نمی‌شود."
            )

            return

        await message.reply_text(
            "✅ پست با موفقیت به کانال ارسال شد."
        )

    except Exception as e:

        print("ERROR:", e)

        await message.reply_text(
            f"❌ خطا هنگام ارسال:\n{e}"
        )


def main():

    print("🤖 BOT STARTING...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("myid", myid)
    )

    app.add_handler(
        CommandHandler("button", show_button)
    )

    app.add_handler(
        CommandHandler("deletebutton", remove_button)
    )

    conversation = ConversationHandler(

        entry_points=[
            CommandHandler(
                "setbutton",
                setbutton_start
            )
        ],

        states={

            BUTTON_TEXT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    setbutton_text
                )
            ],

            BUTTON_URL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    setbutton_url
                )
            ],

        },

        fallbacks=[
            CommandHandler(
                "cancel",
                cancel
            )
        ],
    )

    app.add_handler(conversation)

    app.add_handler(
        MessageHandler(
            (
                filters.PHOTO
                | filters.VIDEO
                | filters.Document.ALL
                | filters.AUDIO
                | filters.VOICE
                | filters.TEXT
            )
            & ~filters.COMMAND,
            handle_post
        )
    )

    print("✅ BOT IS RUNNING 24/7")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
