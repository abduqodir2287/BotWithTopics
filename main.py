import asyncio
import aiohttp
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.configs.config import settings

# Твой токен
API_TOKEN = settings.TELEGRAM_BOT_TOKEN


async def delete_topic_via_http():
    # URL метода API
    url = f"https://api.telegram.org/bot{API_TOKEN}/deleteForumTopic"

    # Параметры запроса
    payload = {
        'chat_id': "ChatId",  # Твой chat_id
        'message_thread_id': 93189  # ID топика
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()

            if result.get("ok"):
                print("Успех: Топик удален.")
            else:
                print(f"Ошибка: {result.get('description')}")

# Запуск
if __name__ == "__main__":
    asyncio.run(delete_topic_via_http())