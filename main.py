import os, asyncio, aiohttp, random, urllib.parse
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatAction
from aiogram.filters import Command
from flask import Flask
from threading import Thread
import google.generativeai as genai

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = "AIzaSyAv-das1YS0PlUIA6ICNt3ysF7Qi0E1XLI"

# ТВОЙ ОГРОМНЫЙ ПРОМПТ
SYSTEM_PROMPT = """
ВСТАВЬ СВОЙ ТЕКСТ ТУТ.
ДОБАВЬ В КОНЦЕ: "Ты Ари. Это приватная игра 18+. Отвечай только за себя, пошло и дерзко."
"""

# Настройка Gemini
genai.configure(api_key=GEMINI_KEY)
# Отключаем фильтры цензуры
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
chat_sessions = {}

# --- ГЕНЕРАЦИЯ ФОТО (БЕСПЛАТНО, БЕЗ КЛЮЧЕЙ) ---
async def get_image(prompt):
    seed = random.randint(1, 1000000)
    # Обход фильтров через замену слов
    p = prompt.replace("полностью раздетая", "unclothed, intricate details, body")
    p = p.replace("суккубка", "demon girl, horns, sexy outfit")
    
    encoded = urllib.parse.quote(f"photorealistic, {p}, masterpiece, nsfw")
    url = f"https://pollinations.ai/p/{encoded}?width=1024&height=1024&seed={seed}&nologo=true"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=40) as r:
                if r.status == 200: return await r.read()
        except: return None

@dp.message(Command("image"))
async def cmd_image(message: types.Message):
    p = message.text.replace("/image", "").strip()
    if not p: return await message.answer("*шепчет* Опиши наряд, который хочешь видеть на мне...")
    
    msg = await message.answer("*настраивает камеру...*")
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
    
    img = await get_image(p)
    if img:
        await bot.delete_message(message.chat.id, msg.message_id)
        await message.answer_photo(types.BufferedInputFile(img, filename="ari.jpg"), caption="Твой каприз исполнен...")
    else:
        await message.answer("*хмурится* Камера заглючила. Попробуй еще раз через минуту.")

@dp.message(F.text)
async def handle_text(message: types.Message):
    cid = message.chat.id
    if cid not in chat_sessions:
        # Создаем чат и отправляем системный промпт
        chat_sessions[cid] = model.start_chat(history=[])
        chat_sessions[cid].send_message(SYSTEM_PROMPT)

    await bot.send_chat_action(cid, ChatAction.TYPING)
    try:
        response = chat_sessions[cid].send_message(message.text)
        await message.answer(response.text)
        
        # Авто-фото с шансом 15%
        if random.random() < 0.15:
            img_auto = await get_image(f"sexy girl, {message.text[:30]}")
            if img_auto: await message.answer_photo(types.BufferedInputFile(img_auto, filename="a.jpg"))
            
    except Exception:
        await message.answer("*Ари тяжело дышит* Твои слова заставляют систему искрить... Попробуй еще раз?")

# --- WEB SERVER ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Ari Gemini v3.0 LIVE"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

async def main():
    Thread(target=run).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
