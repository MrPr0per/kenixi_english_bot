from io import BytesIO

from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, Application

from images_processing import ImagesDownloader, ImagesFormatter
from secrets import TG_BOT_API_KEY


class TgBot:
    def __init__(self):
        self.app: Application | None = None
        self.downloader: ImagesDownloader | None = None
        self.formatter = ImagesFormatter()

    async def start(self):
        self.downloader = ImagesDownloader()
        await self.downloader.__aenter__()
        return self

    async def stop(self):
        if self.downloader is not None:
            await self.downloader.__aexit__(None, None, None)
            self.downloader = None

    def run(self):
        async def post_init(app):
            await self.start()

        async def post_shutdown(app):
            await self.stop()

        self.app = (
            ApplicationBuilder()
            .token(TG_BOT_API_KEY)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self.app.run_polling()

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query_text = update.message.text
        reply_text = f'***{query_text}***!'

        images = await self.downloader.download_images(query_text)

        if images:
            collage = self.formatter.make_collage(images)
        else:
            collage = Image.open('images_not_found.png')

        bio = BytesIO()
        collage.save(bio, format='JPEG', quality=90)
        bio.seek(0)

        await update.message.reply_photo(photo=bio, caption=reply_text)


def main():
    TgBot().run()


if __name__ == '__main__':
    main()
