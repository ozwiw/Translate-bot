import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from deep_translator import GoogleTranslator
from aiohttp import web

# --- НАСТРОЙКИ ---
TOKEN = '8619392171:AAGP3xl8kApyOwU8Bl-_d3PtgQ4CefxoQmI'
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = GoogleTranslator(source='auto', target='ru')

# --- МИКРО-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ НЕ УСНУЛ) ---
async def handle(request):
    return web.Response(text="Бот работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080)) # Порт от Render
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")

# --- ЛОГИКА ПЕРЕВОДЧИКА ---
@dp.message(F.text)
async def translate_message(message: types.Message):
    # Не переводим сами себя
    me = await bot.get_me()
    if message.from_user.id == me.id:
        return

    try:
        translated_text = translator.translate(message.text)

        # Если текст уже русский — игнорируем
        if translated_text.strip().lower() == message.text.strip().lower():
            return

        # Кнопка удаления
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(
            text="🗑 Скрыть перевод", 
            callback_data="delete_translate")
        )

        response = (
            f"<b>✨ Перевод на русский:</b>\n"
            f"«<code>{translated_text}</code>»"
        )

        await message.reply(
            response, 
            parse_mode="HTML", 
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        print(f"Ошибка: {e}")

@dp.callback_query(F.data == "delete_translate")
async def delete_callback(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except:
        await callback.answer("Ошибка удаления")

async def main():
    # Запускаем фоном веб-сервер и основную работу бота
    asyncio.create_task(start_web_server())
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())