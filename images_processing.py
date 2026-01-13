import asyncio
import heapq
import urllib.parse
from io import BytesIO
from typing import List, Union

import aiohttp
from PIL import Image

from secrets import PIXABAY_API_KEY


class ImagesDownloader:
    BASE_URL = "https://pixabay.com/api/"

    def __init__(self, api_key: str = PIXABAY_API_KEY):
        self.api_key = api_key
        self.session: aiohttp.ClientSession | None = None

    async def fetch_image_urls(self, query: str, n: int = 16) -> list[str]:
        """Получаем URLs n картинок в минимальном качестве"""
        encoded_query = urllib.parse.quote(query)
        if n > 200:
            raise Exception(
                f"Запросить можно только 200 картинок за раз (было запрошено: {n})"
            )
        url = f"{self.BASE_URL}?key={self.api_key}&q={encoded_query}&per_page={n}"

        async with self.session.get(url) as resp:
            data = await resp.json()
            return [hit["previewURL"] for hit in data["hits"]]

    async def download_image(self, url: str) -> BytesIO | None:
        """Скачиваем картинку и возвращаем как BytesIO."""
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            img_bytes = await resp.read()
            bio = BytesIO(img_bytes)
            bio.seek(0)
            return bio

    async def download_images(self, query: str, n: int = 16) -> list[BytesIO]:
        """Асинхронно скачиваем n картинок в память."""
        urls = await self.fetch_image_urls(query, n)
        tasks = [self.download_image(url) for url in urls]
        results = await asyncio.gather(*tasks)
        # фильтруем None (если что-то не скачалось)
        images = [img for img in results if img is not None]
        return images

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()


class ImagesFormatter:
    def __init__(
        self,
        columns_count=4,
        column_width=300,
        gap=10,
        background_color=(255, 255, 255),
    ):
        self.columns_count = columns_count
        self.column_width = column_width
        self.gap = gap
        self.background_color = background_color

    def make_collage(self, images: List[BytesIO]) -> Image.Image:
        """Формирует коллаж с минимальной разницей высот столбцов"""
        prepared = [
            self._resize_to_column_width(Image.open(img).convert("RGB"))
            for img in images
        ]

        min_columns_heap = [
            (0, i) for i in range(self.columns_count)
        ]  # хранит пары (current_height, column_index)
        heapq.heapify(min_columns_heap)

        column_images = [[] for _ in range(self.columns_count)]

        for img in prepared:
            height, idx = heapq.heappop(min_columns_heap)
            column_images[idx].append(img)
            new_height = height + img.height + self.gap
            heapq.heappush(min_columns_heap, (new_height, idx))

        column_heights = [
            sum(img.height for img in col) + self.gap * max(len(col) + 1, 0)
            for col in column_images
        ]
        total_height = max(column_heights)

        total_width = self.columns_count * self.column_width + self.gap * (
            self.columns_count + 1
        )

        canvas = Image.new(
            "RGB",
            (total_width, total_height),
            self.background_color,
        )

        # Отрисовка
        for col_idx, col in enumerate(column_images):
            x = col_idx * (self.column_width + self.gap) + self.gap
            y = self.gap
            for img in col:
                canvas.paste(img, (x, y))
                y += img.height + self.gap

        return canvas

    def _resize_to_column_width(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        scale = self.column_width / w
        new_height = int(h * scale)
        return img.resize((self.column_width, new_height), Image.LANCZOS)


async def example():
    async with ImagesDownloader() as downloader:
        images = await downloader.download_images("cats", 20)
        print(f"Скачано {len(images)} картинок в память")

    formatter = ImagesFormatter(
        columns_count=4,
        column_width=300,
        gap=16,
    )

    collage = formatter.make_collage(images)
    collage.show()


# Запуск
if __name__ == "__main__":
    asyncio.run(example())
