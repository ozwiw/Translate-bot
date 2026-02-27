import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from pyaspeller import YandexSpeller # Для проверки ошибок
from aiohttp import web

DetectorFactory.seed = 0
speller = YandexSpeller()

# --- НАСТРОЙКИ ---
TOKEN = '8619392171:AAGP3xl8kApyOwU8Bl-_d3PtgQ4CefxoQmI'
bot = Bot(token=TOKEN)
dp = Dispatcher()
to_russian = GoogleTranslator(source='auto', target='ru')

# --- МИКРО-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Бот работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ФУНКЦИЯ ПРОВЕРКИ ОШИБОК ---
def has_errors(text):
    # Проверяем текст через Яндекс.Спеллер
    check = speller.spelled(text)
    return check != text # Если исправленный текст не равен оригиналу — значит были ошибки

# --- ЛОГИКА ОБРАБОТКИ СООБЩЕНИЙ ---
@dp.message(F.text)
async def handle_message(message: types.Message):
    if message.text.startswith('/') or message.from_user.is_bot:
        return

    try:
        lang = detect(message.text)
        
        builder = InlineKeyboardBuilder()
        
        if lang != 'ru':
            # ИНОСТРАННЫЙ: предлагаем перевод ВСЕГДА
            builder.row(types.InlineKeyboardButton(text="Перевести 🇷🇺", callback_data="action_translate"))
            await message.reply("🌐 Вижу иностранный текст:", reply_markup=builder.as_markup())
        
        elif lang == 'ru':
            # РУССКИЙ: Проверяем на наличие ошибок
            if has_errors(message.text):
                builder.row(types.InlineKeyboardButton(text="Поправить ✨", callback_data="action_fix"))
                await message.reply("📝 Кажется, в тексте ошибки. Поправить?", reply_markup=builder.as_markup())
            else:
                # Если ошибок нет — просто молчим
                return

    except Exception as e:
        print(f"Ошибка: {e}")

# --- ОБРАБОТКА КНОПОК ---
@dp.callback_query(F.data.startswith("action_"))
async def process_callback(callback: types.CallbackQuery):
    original_text = callback.message.reply_to_message.text
    action = callback.data.split("_")[1]

    try:
        if action == "translate":
            result = to_russian.translate(original_text)
            header = "✨ <b>Перевод:</b>"
        elif action == "fix":
            # Спеллер возвращает уже исправленный текст
            result = speller.spelled(original_text)
            header = "💎 <b>Исправлено:</b>"

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🗑 Скрыть", callback_data="delete_translate"))

        await callback.message.edit_text(
            f"{header}\n\n«<code>{result}</code>»",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        await callback.answer(f"Ошибка: {e}")

@dp.callback_query(F.data == "delete_translate")
async def delete_callback(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except:
        await callback.answer("Ошибка удаления")

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
