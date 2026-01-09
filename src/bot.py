"""
Telegram бот с поддержкой топиков (threaded mode) и Telegram Streaming API
"""

import asyncio
import logging
from weakref import finalize

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

from src.configs.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище для топиков пользователей
user_topics = {}


async def send_streaming_message(message: Message, text: str, chunk_size: int = 20):
    """
    Отправка сообщения с использованием Telegram Streaming API

    Args:
        message: Исходное сообщение
        text: Текст для отправки
        chunk_size: Размер чанка для streaming
    """
    words = text.split()
    current_text = ""

    # Показываем streaming эффект
    for i, word in enumerate(words):
        current_text += word
        if i < len(words) - 1:
            current_text += " "

        # Отправляем промежуточные чанки через send_message_draft
        if (i + 1) % chunk_size == 0 and i < len(words) - 1:
            await message.bot.send_message_draft(
                chat_id=message.chat.id,
                text=current_text,
                draft_id=message.message_id,
                message_thread_id=message.message_thread_id,
            )

    # ВАЖНО: Финальное сообщение отправляем обычным способом для сохранения в истории
    await message.answer(text=current_text)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    Отправляет приветственное сообщение
    """
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "пользователь"

    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        "Я бот с поддержкой топиков (threaded mode).\n\n"
        "📝 Каждое твое сообщение будет создавать новый топик, "
        "и я буду отвечать в том же топике!\n\n"
        "Просто напиши мне что-нибудь, и я создам топик для нашей беседы.\n\n"
        "✨ Все мои ответы отправляются с использованием Telegram Streaming API!"
    )

    await send_streaming_message(message, welcome_text, chunk_size=15)
    logger.info(f"Пользователь {user_id} ({user_name}) запустил бота")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help
    """
    help_text = (
        "ℹ️ Помощь по боту\n\n"
        "🔹 /start - Запустить бота\n"
        "🔹 /help - Показать эту справку\n"
        "🔹 /info - Информация о текущем топике\n\n"
        "📌 Как работает бот:\n"
        "Отправьте любое сообщение, и бот ответит в том же топике, "
        "предоставив информацию о нем.\n\n"
        "✨ Все ответы используют Telegram Streaming API!"
    )

    await send_streaming_message(message, help_text, chunk_size=15)


@dp.message(Command("info"))
async def cmd_info(message: Message):
    """
    Обработчик команды /info
    Показывает информацию о текущем топике
    """
    topic_id = message.message_thread_id
    user_id = message.from_user.id

    if topic_id:
        info_text = (
            f"📊 Информация о топике:\n\n"
            f"🆔 ID топика: {topic_id}\n"
            f"👤 Пользователь: {message.from_user.full_name}\n"
            f"🔢 ID пользователя: {user_id}\n"
            f"💬 ID сообщения: {message.message_id}\n"
            f"📅 Дата: {message.date.strftime('%d.%m.%Y %H:%M:%S')}"
        )
    else:
        info_text = (
            "ℹ️ Это сообщение не находится в топике.\n"
            "Отправьте обычное сообщение, чтобы создать топик."
        )

    await send_streaming_message(message, info_text, chunk_size=10)


@dp.message(F.text)
async def handle_message(message: Message):
    """
    Обработчик всех текстовых сообщений
    Отвечает в том же топике и предоставляет информацию
    """
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    topic_id = message.message_thread_id
    message_text = message.text

    logger.info(
        f"Получено сообщение от {user_name} (ID: {user_id}), "
        f"Топик: {topic_id}, Текст: {message_text[:50]}"
    )

    # Формируем ответ с информацией о топике
    if topic_id:
        response = (
            f"✅ Получил твое сообщение в топике!\n\n"
            f"📝 Твой текст: {message_text}\n\n"
            f"📊 Информация о топике:\n"
            f"🆔 ID топика: {topic_id}\n"
            f"👤 От: {user_name}\n"
            f"💬 ID сообщения: {message.message_id}\n"
            f"⏰ Время: {message.date.strftime('%H:%M:%S')}\n\n"
            f"Я отвечаю в том же топике! 🎯"
        )

        # Сохраняем информацию о топике
        if user_id not in user_topics:
            user_topics[user_id] = []

        user_topics[user_id].append({
            'topic_id': topic_id,
            'message_id': message.message_id,
            'text': message_text[:100],
            'timestamp': message.date
        })
    else:
        response = (
            f"✅ Получил твое сообщение!\n\n"
            f"📝 Твой текст: {message_text}\n\n"
            f"ℹ️ Это сообщение не в топике.\n"
            f"Если у тебя включен threaded mode, "
            f"каждое новое сообщение должно создавать топик автоматически."
        )

    # Отправляем ответ с использованием streaming
    await send_streaming_message(message, response, chunk_size=20)


@dp.message(F.photo)
async def handle_photo(message: Message):
    """
    Обработчик фотографий
    """
    topic_id = message.message_thread_id

    response = (
        f"📷 Получил фото!\n\n"
        f"Информация:\n"
        f"🆔 ID топика: {topic_id or 'Нет'}\n"
        f"👤 От: {message.from_user.full_name}\n"
        f"💬 ID сообщения: {message.message_id}"
    )

    if message.caption:
        response += f"\n📝 Подпись: {message.caption}"

    await send_streaming_message(message, response, chunk_size=15)
    await message.topic


@dp.message(F.document)
async def handle_document(message: Message):
    """
    Обработчик документов
    """
    topic_id = message.message_thread_id
    doc = message.document

    response = (
        f"📄 Получил документ!\n\n"
        f"Информация:\n"
        f"📎 Файл: {doc.file_name}\n"
        f"📏 Размер: {doc.file_size / 1024:.2f} KB\n"
        f"🆔 ID топика: {topic_id or 'Нет'}\n"
        f"👤 От: {message.from_user.full_name}"
    )

    await send_streaming_message(message, response, chunk_size=15)


@dp.message(F.video)
async def handle_video(message: Message):
    """
    Обработчик видео
    """
    topic_id = message.message_thread_id
    video = message.video

    response = (
        f"🎥 Получил видео!\n\n"
        f"Информация:\n"
        f"⏱ Длительность: {video.duration} сек\n"
        f"📏 Размер: {video.file_size / (1024 * 1024):.2f} MB\n"
        f"🆔 ID топика: {topic_id or 'Нет'}\n"
        f"👤 От: {message.from_user.full_name}"
    )

    if message.caption:
        response += f"\n📝 Подпись: {message.caption}"

    await send_streaming_message(message, response, chunk_size=15)


@dp.message(F.voice)
async def handle_voice(message: Message):
    """
    Обработчик голосовых сообщений
    """
    topic_id = message.message_thread_id
    voice = message.voice

    response = (
        f"🎤 Получил голосовое сообщение!\n\n"
        f"Информация:\n"
        f"⏱ Длительность: {voice.duration} сек\n"
        f"📏 Размер: {voice.file_size / 1024:.2f} KB\n"
        f"🆔 ID топика: {topic_id or 'Нет'}\n"
        f"👤 От: {message.from_user.full_name}"
    )

    await send_streaming_message(message, response, chunk_size=15)


@dp.message(F.sticker)
async def handle_sticker(message: Message):
    """
    Обработчик стикеров
    """
    topic_id = message.message_thread_id
    sticker = message.sticker

    response = (
        f"🎨 Получил стикер!\n\n"
        f"Информация:\n"
        f"😀 Emoji: {sticker.emoji or 'Нет'}\n"
        f"📦 Набор: {sticker.set_name or 'Неизвестно'}\n"
        f"🆔 ID топика: {topic_id or 'Нет'}\n"
        f"👤 От: {message.from_user.full_name}"
    )

    await send_streaming_message(message, response, chunk_size=15)


@dp.message()
async def handle_other(message: Message):
    """
    Обработчик остальных типов сообщений
    """
    topic_id = message.message_thread_id
    content_type = message.content_type

    response = (
        f"📩 Получил сообщение типа: {content_type}\n\n"
        f"Информация о топике:\n"
        f"🆔 ID топика: {topic_id or 'Нет'}\n"
        f"👤 От: {message.from_user.full_name}\n"
        f"💬 ID сообщения: {message.message_id}"
    )

    await send_streaming_message(message, response, chunk_size=15)


async def main():
    """
    Главная функция запуска бота
    """
    logger.info("🚀 Запуск бота с Telegram Streaming API...")

    try:
        # Удаляем webhook (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)

        # Запускаем polling
        logger.info("✅ Бот успешно запущен с поддержкой streaming!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен пользователем")