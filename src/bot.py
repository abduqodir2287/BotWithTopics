"""
Telegram бот с полной поддержкой топиков в личных чатах (Bot API 9.4)
Версия с поддержкой .env конфигурации
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from src.configs.config import settings

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения или напрямую
BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище топиков пользователей
user_topics: Dict[int, Dict[int, Dict[str, Any]]] = {}

# Константы цветов для топиков
TOPIC_COLORS = {
    'blue': 0x6FB9F0,
    'yellow': 0xFFD67E,
    'purple': 0xCB86DB,
    'green': 0x8EEE98,
    'pink': 0xFF93B2,
    'red': 0xFB6F5F
}

COLOR_NAMES = {
    0x6FB9F0: '🔵 Синий',
    0xFFD67E: '🟡 Желтый',
    0xCB86DB: '🟣 Фиолетовый',
    0x8EEE98: '🟢 Зеленый',
    0xFF93B2: '🩷 Розовый',
    0xFB6F5F: '🔴 Красный'
}


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📁 Создать топик", callback_data="create_topic"),
            InlineKeyboardButton(text="📋 Мои топики", callback_data="list_topics")
        ],
        [
            InlineKeyboardButton(text="🎨 Создать с цветом", callback_data="create_colored")
        ],
        [
            InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")
        ]
    ])
    return keyboard


def get_color_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора цвета для топика"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔵 Синий", callback_data="color_blue"),
            InlineKeyboardButton(text="🟡 Желтый", callback_data="color_yellow")
        ],
        [
            InlineKeyboardButton(text="🟣 Фиолетовый", callback_data="color_purple"),
            InlineKeyboardButton(text="🟢 Зеленый", callback_data="color_green")
        ],
        [
            InlineKeyboardButton(text="🩷 Розовый", callback_data="color_pink"),
            InlineKeyboardButton(text="🔴 Красный", callback_data="color_red")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_topic_actions_keyboard(topic_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с действиями для топика"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"rename_{topic_id}"),
            InlineKeyboardButton(text="🎨 Цвет", callback_data=f"change_color_{topic_id}")
        ],
        [
            InlineKeyboardButton(text="📌 Закрепить", callback_data=f"pin_{topic_id}"),
            InlineKeyboardButton(text="📍 Открепить", callback_data=f"unpin_{topic_id}")
        ],
        [
            InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"close_{topic_id}"),
            InlineKeyboardButton(text="🔓 Открыть", callback_data=f"reopen_{topic_id}")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"details_{topic_id}")
        ],
        [
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{topic_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 К списку", callback_data="list_topics")
        ]
    ])
    return keyboard


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "пользователь"

    try:
        # Получаем информацию о пользователе
        user_info = await bot.get_chat(user_id)
        allows_topics = getattr(user_info, 'allows_users_to_create_topics', None)

        welcome_text = (
            f"👋 <b>Привет, {user_name}!</b>\n\n"
            f"🎉 Добро пожаловать в демо-бот топиков!\n\n"
            f"<b>📱 Новые возможности Bot API 9.4:</b>\n"
            f"✅ Создание топиков в личных чатах\n"
            f"✅ Полное управление топиками\n"
            f"✅ Настройка цветов и иконок\n"
            f"✅ Закрепление важных топиков\n\n"
        )

        if allows_topics is not None:
            status = "✅ Включены" if allows_topics else "❌ Выключены"
            welcome_text += f"📊 <b>Статус топиков:</b> {status}\n"

            if not allows_topics:
                welcome_text += (
                    f"\n⚠️ <b>Чтобы использовать топики:</b>\n"
                    f"1. Откройте настройки Telegram\n"
                    f"2. Перейдите в 'Чаты'\n"
                    f"3. Включите 'Топики в личных чатах'\n"
                )

        welcome_text += "\n🚀 <b>Выберите действие:</b>"

        await message.answer(
            text=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )

        # Инициализация хранилища
        if user_id not in user_topics:
            user_topics[user_id] = {}

        logger.info(f"Пользователь {user_id} ({user_name}) запустил бота. Topics: {allows_topics}")

    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Справка по боту"""
    help_text = (
        "📖 <b>Справка по использованию</b>\n\n"

        "<b>🔹 Основные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/create - Создать топик\n"
        "/list - Список топиков\n"
        "/info - Информация о топике\n"
        "/stats - Статистика\n\n"

        "<b>🔹 Возможности:</b>\n"
        "• Создание топиков с разными цветами\n"
        "• Переименование топиков\n"
        "• Управление статусом (открыт/закрыт)\n"
        "• Закрепление важных топиков\n"
        "• Полная информация о каждом топике\n\n"

        "<b>🔹 Работа с топиками:</b>\n"
        "1. Создайте топик через меню или команду\n"
        "2. Откройте топик в списке чатов\n"
        "3. Используйте команду /info для управления\n"
        "4. Общайтесь внутри топика!\n\n"

        "💡 <b>Совет:</b> Все топики создаются ботом\n"
        "и доступны для полного управления!"
    )

    await message.answer(
        text=help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )


@dp.message(Command("create"))
async def cmd_create_topic(message: Message):
    """Быстрое создание топика"""
    topic_name = f"Топик {datetime.now().strftime('%d.%m %H:%M')}"
    await create_new_topic(
        user_id=message.from_user.id,
        topic_name=topic_name,
        message=message,
        icon_color=TOPIC_COLORS['blue']
    )


@dp.message(Command("list"))
async def cmd_list_topics(message: Message):
    """Список топиков пользователя"""
    await show_user_topics(message.from_user.id, message)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика топиков"""
    user_id = message.from_user.id
    topics = user_topics.get(user_id, {})

    if not topics:
        await message.answer(
            "📊 <b>Статистика</b>\n\n"
            "У вас пока нет топиков.\n"
            "Создайте первый топик!",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Подсчет статистики
    total = len(topics)
    closed = sum(1 for t in topics.values() if t.get('is_closed'))
    pinned = sum(1 for t in topics.values() if t.get('is_pinned'))

    # Статистика по цветам
    color_stats = {}
    for topic in topics.values():
        color = topic.get('icon_color', '0x6fb9f0')
        color_int = int(color, 16) if isinstance(color, str) else color
        color_name = COLOR_NAMES.get(color_int, 'Неизвестный')
        color_stats[color_name] = color_stats.get(color_name, 0) + 1

    stats_text = (
        f"📊 <b>Ваша статистика топиков</b>\n\n"
        f"📁 <b>Всего топиков:</b> {total}\n"
        f"🔓 <b>Открытых:</b> {total - closed}\n"
        f"🔒 <b>Закрытых:</b> {closed}\n"
        f"📌 <b>Закрепленных:</b> {pinned}\n\n"
        f"<b>🎨 По цветам:</b>\n"
    )

    for color_name, count in sorted(color_stats.items(), key=lambda x: x[1], reverse=True):
        stats_text += f"   {color_name}: {count}\n"

    await message.answer(
        text=stats_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )


@dp.message(Command("info"))
async def cmd_info(message: Message):
    """Информация о текущем топике"""
    topic_id = message.message_thread_id
    user_id = message.from_user.id

    if not topic_id:
        await message.answer(
            "ℹ️ Это сообщение не в топике.\n\n"
            "Отправьте команду внутри топика.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    topic_info = user_topics.get(user_id, {}).get(topic_id)

    if not topic_info:
        info_text = (
            f"📊 <b>Информация о топике</b>\n\n"
            f"🆔 <b>ID:</b> <code>{topic_id}</code>\n"
            f"💬 <b>Сообщение:</b> <code>{message.message_id}</code>\n"
            f"👤 <b>От:</b> {message.from_user.full_name}\n\n"
            f"⚠️ Топик не найден в базе бота\n"
            f"(возможно, создан вручную)"
        )
        keyboard = get_main_menu_keyboard()
    else:
        color_int = int(topic_info.get('icon_color', '0x6fb9f0'), 16)
        color_name = COLOR_NAMES.get(color_int, 'Неизвестный')

        info_text = (
            f"📊 <b>Информация о топике</b>\n\n"
            f"📝 <b>Название:</b> {topic_info['name']}\n"
            f"🆔 <b>ID:</b> <code>{topic_id}</code>\n"
            f"🎨 <b>Цвет:</b> {color_name}\n"
            f"📅 <b>Создан:</b> {topic_info['created_at']}\n"
            f"🔒 <b>Статус:</b> {'Закрыт' if topic_info.get('is_closed') else 'Открыт'}\n"
            f"📌 <b>Закреплен:</b> {'Да' if topic_info.get('is_pinned') else 'Нет'}\n\n"
            f"Управляйте топиком с помощью кнопок:"
        )
        keyboard = get_topic_actions_keyboard(topic_id)

    await message.answer(
        text=info_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


async def create_new_topic(
        user_id: int,
        topic_name: str,
        message: Message,
        icon_color: int = 0x6FB9F0
):
    """Создание нового топика"""
    try:
        topic = await bot.create_forum_topic(
            chat_id=user_id,
            name=topic_name,
            icon_color=icon_color
        )

        # Сохранение информации
        if user_id not in user_topics:
            user_topics[user_id] = {}

        color_name = COLOR_NAMES.get(icon_color, 'Неизвестный')

        user_topics[user_id][topic.message_thread_id] = {
            'name': topic_name,
            'icon_color': hex(icon_color),
            'color_name': color_name,
            'created_at': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'is_closed': False,
            'is_pinned': False,
            'messages_count': 0
        }

        success_text = (
            f"✅ <b>Топик создан!</b>\n\n"
            f"📝 <b>Название:</b> {topic.name}\n"
            f"🆔 <b>ID:</b> <code>{topic.message_thread_id}</code>\n"
            f"🎨 <b>Цвет:</b> {color_name}\n\n"
            f"💡 Используйте кнопки для управления:"
        )

        # Отправка в топик
        await bot.send_message(
            chat_id=user_id,
            text=success_text,
            message_thread_id=topic.message_thread_id,
            parse_mode=ParseMode.HTML,
            reply_markup=get_topic_actions_keyboard(topic.message_thread_id)
        )

        # Уведомление в основной чат
        await message.answer(
            f"✅ Топик '<b>{topic_name}</b>' создан!\n"
            f"Проверьте новый топик в списке чатов ⬆️",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )

        logger.info(f"Создан топик {topic.message_thread_id} ({topic_name}) для {user_id}")

    except TelegramBadRequest as e:
        error_text = f"❌ <b>Ошибка создания:</b>\n\n{e.message}"

        if "USER_NOT_PARTICIPANT" in str(e) or "topics" in str(e).lower():
            error_text += (
                "\n\n💡 <b>Возможные причины:</b>\n"
                "• Топики не включены в настройках\n"
                "• Бот не имеет прав\n\n"
                "📱 <b>Как включить топики:</b>\n"
                "1. Настройки Telegram\n"
                "2. Раздел 'Чаты'\n"
                "3. Включите 'Топики в личных чатах'"
            )

        await message.answer(
            text=error_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )
        logger.error(f"Ошибка создания топика: {e}")


async def show_user_topics(user_id: int, message: Message):
    """Показать список топиков"""
    topics = user_topics.get(user_id, {})

    if not topics:
        await message.answer(
            "📭 <b>Топиков пока нет</b>\n\n"
            "Создайте первый топик!",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )
        return

    list_text = f"📋 <b>Ваши топики ({len(topics)}):</b>\n\n"

    # Сортировка: сначала открепленные открытые, потом закрытые
    sorted_topics = sorted(
        topics.items(),
        key=lambda x: (
            x[1].get('is_closed', False),
            not x[1].get('is_pinned', False)
        )
    )

    for topic_id, info in sorted_topics[:15]:  # Первые 15
        status = "🔒" if info.get('is_closed') else "🔓"
        pin = "📌 " if info.get('is_pinned') else ""

        list_text += (
            f"{status} {pin}<b>{info['name']}</b>\n"
            f"   🆔 <code>{topic_id}</code> | "
            f"🎨 {info.get('color_name', 'Синий')}\n"
            f"   📅 {info['created_at']}\n\n"
        )

    if len(topics) > 15:
        list_text += f"... и еще {len(topics) - 15} топиков\n\n"

    list_text += "Выберите топик для управления:"

    # Клавиатура
    buttons = []
    for topic_id, info in sorted_topics[:10]:
        icon = "🔒" if info.get('is_closed') else "🔓"
        pin = "📌" if info.get('is_pinned') else ""
        name = info['name'][:20]

        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {pin} {name}",
                callback_data=f"topic_info_{topic_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="➕ Создать", callback_data="create_topic")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        text=list_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


# ==================== CALLBACK HANDLERS ====================

@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: types.CallbackQuery):
    """Главное меню"""
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "create_topic")
async def callback_create_topic(callback: types.CallbackQuery):
    """Создание топика"""
    await callback.answer("Создаю топик...")
    topic_name = f"Топик {datetime.now().strftime('%d.%m %H:%M')}"
    await create_new_topic(
        user_id=callback.from_user.id,
        topic_name=topic_name,
        message=callback.message,
        icon_color=TOPIC_COLORS['blue']
    )


@dp.callback_query(F.data == "create_colored")
async def callback_create_colored(callback: types.CallbackQuery):
    """Выбор цвета для топика"""
    await callback.message.edit_text(
        "🎨 <b>Выберите цвет для нового топика:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_color_selection_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("color_"))
async def callback_color_selected(callback: types.CallbackQuery):
    """Создание топика с выбранным цветом"""
    color_key = callback.data.split("_")[1]
    color_value = TOPIC_COLORS.get(color_key, TOPIC_COLORS['blue'])
    color_name = COLOR_NAMES.get(color_value, 'Синий')

    await callback.answer(f"Создаю {color_name.lower()} топик...")

    topic_name = f"{color_name.split()[1]} топик {datetime.now().strftime('%H:%M')}"

    await create_new_topic(
        user_id=callback.from_user.id,
        topic_name=topic_name,
        message=callback.message,
        icon_color=color_value
    )


@dp.callback_query(F.data == "list_topics")
async def callback_list_topics(callback: types.CallbackQuery):
    """Список топиков"""
    await callback.answer()
    await show_user_topics(callback.from_user.id, callback.message)


@dp.callback_query(F.data.startswith("topic_info_"))
async def callback_topic_info(callback: types.CallbackQuery):
    """Подробная информация о топике"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    topic_info = user_topics.get(user_id, {}).get(topic_id)

    if not topic_info:
        await callback.answer("❌ Топик не найден!", show_alert=True)
        return

    color_int = int(topic_info.get('icon_color', '0x6fb9f0'), 16)
    color_name = COLOR_NAMES.get(color_int, 'Неизвестный')

    info_text = (
        f"📊 <b>Информация о топике</b>\n\n"
        f"📝 <b>Название:</b> {topic_info['name']}\n"
        f"🆔 <b>ID:</b> <code>{topic_id}</code>\n"
        f"🎨 <b>Цвет:</b> {color_name}\n"
        f"📅 <b>Создан:</b> {topic_info['created_at']}\n"
        f"🔒 <b>Статус:</b> {'Закрыт' if topic_info.get('is_closed') else 'Открыт'}\n"
        f"📌 <b>Закреплен:</b> {'Да' if topic_info.get('is_pinned') else 'Нет'}\n\n"
        f"Выберите действие:"
    )

    await callback.message.edit_text(
        text=info_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_topic_actions_keyboard(topic_id)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("rename_"))
async def callback_rename_topic(callback: types.CallbackQuery):
    """Переименование топика"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    try:
        new_name = f"✅ Переименован {datetime.now().strftime('%H:%M')}"

        await bot.edit_forum_topic(
            chat_id=user_id,
            message_thread_id=topic_id,
            name=new_name
        )

        if user_id in user_topics and topic_id in user_topics[user_id]:
            user_topics[user_id][topic_id]['name'] = new_name

        await callback.answer(f"✅ Топик переименован!", show_alert=True)
        await callback_topic_info(callback)

        logger.info(f"Топик {topic_id} переименован → {new_name}")

    except TelegramBadRequest as e:
        await callback.answer(f"❌ Ошибка: {e.message}", show_alert=True)


@dp.callback_query(F.data.startswith("change_color_"))
async def callback_change_color(callback: types.CallbackQuery):
    """Смена цвета топика"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    import random
    colors = list(TOPIC_COLORS.values())
    new_color = random.choice(colors)
    color_name = COLOR_NAMES.get(new_color, 'Неизвестный')

    try:
        await bot.edit_forum_topic(
            chat_id=user_id,
            message_thread_id=topic_id,
            icon_color=new_color
        )

        if user_id in user_topics and topic_id in user_topics[user_id]:
            user_topics[user_id][topic_id]['icon_color'] = hex(new_color)
            user_topics[user_id][topic_id]['color_name'] = color_name

        await callback.answer(f"✅ Цвет изменен на {color_name}!", show_alert=True)
        await callback_topic_info(callback)

        logger.info(f"Цвет топика {topic_id} → {color_name}")

    except TelegramBadRequest as e:
        await callback.answer(f"❌ Ошибка: {e.message}", show_alert=True)


@dp.callback_query(F.data.startswith("close_"))
async def callback_close_topic(callback: types.CallbackQuery):
    """Закрытие топика"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    try:
        await bot.close_forum_topic(
            chat_id=user_id,
            message_thread_id=topic_id
        )

        if user_id in user_topics and topic_id in user_topics[user_id]:
            user_topics[user_id][topic_id]['is_closed'] = True

        await callback.answer("🔒 Топик закрыт", show_alert=True)
        await callback_topic_info(callback)

    except TelegramBadRequest as e:
        await callback.answer(f"❌ {e.message}", show_alert=True)


@dp.callback_query(F.data.startswith("reopen_"))
async def callback_reopen_topic(callback: types.CallbackQuery):
    """Открытие топика"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    try:
        await bot.reopen_forum_topic(
            chat_id=user_id,
            message_thread_id=topic_id
        )

        if user_id in user_topics and topic_id in user_topics[user_id]:
            user_topics[user_id][topic_id]['is_closed'] = False

        await callback.answer("🔓 Топик открыт", show_alert=True)
        await callback_topic_info(callback)

    except TelegramBadRequest as e:
        await callback.answer(f"❌ {e.message}", show_alert=True)


@dp.callback_query(F.data.startswith("pin_"))
async def callback_pin_topic(callback: types.CallbackQuery):
    """Закрепление топика (локально)"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    if user_id in user_topics and topic_id in user_topics[user_id]:
        user_topics[user_id][topic_id]['is_pinned'] = True
        await callback.answer("📌 Топик закреплен", show_alert=True)
        await callback_topic_info(callback)
    else:
        await callback.answer("❌ Топик не найден", show_alert=True)


@dp.callback_query(F.data.startswith("unpin_"))
async def callback_unpin_topic(callback: types.CallbackQuery):
    """Открепление топика"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    if user_id in user_topics and topic_id in user_topics[user_id]:
        user_topics[user_id][topic_id]['is_pinned'] = False
        await callback.answer("📍 Топик откреплен", show_alert=True)
        await callback_topic_info(callback)


@dp.callback_query(F.data.startswith("delete_"))
async def callback_delete_topic(callback: types.CallbackQuery):
    """Удаление топика"""
    topic_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    try:
        await bot.delete_forum_topic(
            chat_id=user_id,
            message_thread_id=topic_id
        )

        topic_name = "Топик"
        if user_id in user_topics and topic_id in user_topics[user_id]:
            topic_name = user_topics[user_id][topic_id]['name']
            del user_topics[user_id][topic_id]

        await callback.answer(f"✅ '{topic_name}' удален", show_alert=True)
        await show_user_topics(user_id, callback.message)

        logger.info(f"Топик {topic_id} удален")

    except TelegramBadRequest as e:
        error_msg = "❌ Ошибка удаления"

        if "TOPIC_ID_INVALID" in str(e):
            error_msg = (
                "❌ Топик не может быть удален.\n\n"
                "Причины:\n"
                "• Создан не ботом\n"
                "• Уже удален\n"
                "• Неверный ID"
            )

        await callback.answer(error_msg, show_alert=True)


@dp.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    """Справка"""
    await callback.answer()
    await cmd_help(callback.message)


@dp.callback_query(F.data == "about")
async def callback_about(callback: types.CallbackQuery):
    """О боте"""
    about_text = (
        "ℹ️ <b>О боте</b>\n\n"
        "🤖 <b>Демо-бот топиков</b>\n"
        "📅 Bot API 9.4 (Feb 9, 2026)\n\n"
        "<b>Возможности:</b>\n"
        "✅ Топики в личных чатах\n"
        "✅ 6 цветов иконок\n"
        "✅ Полное управление\n"
        "✅ Статистика\n\n"
        "💻 <b>Технологии:</b>\n"
        "• Python 3.11+\n"
        "• aiogram 3.15.0\n"
        "• Bot API 9.4"
    )

    await callback.message.edit_text(
        text=about_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


# ==================== MESSAGE HANDLERS ====================

@dp.message(F.text & ~F.command())
async def handle_text_message(message: Message):
    """Обработка текстовых сообщений"""
    topic_id = message.message_thread_id
    user_id = message.from_user.id

    if topic_id:
        topic_info = user_topics.get(user_id, {}).get(topic_id)

        # Обновляем счетчик сообщений
        if topic_info:
            topic_info['messages_count'] = topic_info.get('messages_count', 0) + 1

        response = (
            f"💬 <b>Сообщение в топике!</b>\n\n"
            f"📝 <b>Текст:</b> {message.text[:100]}\n"
            f"🆔 <b>Топик:</b> <code>{topic_id}</code>\n"
        )

        if topic_info:
            response += (
                f"📋 <b>Название:</b> {topic_info['name']}\n"
                f"💬 <b>Сообщений:</b> {topic_info['messages_count']}\n"
            )

        response += "\n💡 Используйте /info для управления"

        keyboard = get_topic_actions_keyboard(topic_id) if topic_info else None

        await message.answer(
            text=response,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "📭 <b>Сообщение вне топика</b>\n\n"
            "Создайте топик для общения!",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )


async def main():
    """Главная функция"""
    logger.info("🚀 Запуск бота топиков (Bot API 9.4)...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)

        bot_info = await bot.get_me()
        logger.info(f"✅ Бот @{bot_info.username} запущен!")
        logger.info("📋 Функции:")
        logger.info("   ✅ Создание топиков")
        logger.info("   ✅ Управление топиками")
        logger.info("   ✅ 6 цветов иконок")
        logger.info("   ✅ Статистика")

        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен")