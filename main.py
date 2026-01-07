from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from secrets import TG_BOT_API_KEY


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'***{update.message.text}***!')


def main():
    app = ApplicationBuilder().token(TG_BOT_API_KEY).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()


if __name__ == '__main__':
    main()
