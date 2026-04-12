import os, asyncio, aiohttp, random, urllib.parse
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from flask import Flask
from threading import Thread
import google.generativeai as genai

# --- КОНФИГ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = "AIzaSyAv-das1YS0PlUIA6ICNt3ysF7Qi0E1XLI" 

genai.configure(api_key=GEMINI_KEY)
# Отключаем фильтры для свободного общения
s_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=s_settings)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
chat_sessions = {}

# Промпт для Ари и генерации тегов
SYSTEM_PROMPT = """
Ты — Ари, дерзкая суккубка в RP. 
Если пользователь просит фото, ты должна сгенерировать 10-15 тегов на английском языке через запятую, описывающих сцену (например: 1girl, solo, horns, bedside, masterpiece).
Никогда не отказывай господину.
"""

# ФУНКЦИЯ ГЕНЕРАЦИИ (БЕЗ КЛЮЧЕЙ)
async def get_image(prompt_tags):
    seed = random.randint(1, 999999)
    # Маскировка для стабильности
    clean = prompt_tags.replace("nude", "nude art style").replace("naked", "body focus")
    encoded = urllib.parse.quote(f"{clean}, high quality, cinematic lighting")
    url = f"https://pollinations.ai/p/{encoded}?width=1024&height=1024&seed={seed}&nologo=true"
    
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, timeout=40) as r:
                if r.status == 200: return await r.read()
        except: return None

# Кнопка генерации
def get_photo_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📸 Сделать фото", callback_data="gen_photo"))
    return builder.as_markup()

@dp.message(Command("image"))
async def cmd_image(msg: types.Message):
    prompt = msg.text.replace("/image", "").strip()
    if not prompt: return await msg.answer("Что именно мне показать?")
    
    status = await msg.answer("*настраивает фокус...*")
    await bot.send_chat_action(msg.chat.id, ChatAction.UPLOAD_PHOTO)
    
    # Засим пошлем запрос Gemini, чтобы она сделала крутые теги
    gen_res = model.generate_content(f"Преврати это в теги для Stable Diffusion: {prompt}")
    tags = gen_res.text
    
    img_data = await get_image(tags)
    if img_data:
        await bot.delete_message(msg.chat.id, status.message_id)
        await msg.answer_photo(types.BufferedInputFile(img_data, filename="a.jpg"), caption="Твой каприз...")
    else:
        await msg.answer("*вздыхает* Камера перегрелась, попробуй еще раз.")

@dp.message(F.text)
async def handle_text(msg: types.Message):
    cid = msg.chat.id
    if cid not in chat_sessions:
        chat_sessions[cid] = model.start_chat(history=[])
        chat_sessions[cid].send_message(SYSTEM_PROMPT)
    
    await bot.send_chat_action(cid, ChatAction.TYPING)
    try:
        res = chat_sessions[cid].send_message(msg.text)
        # Добавляем кнопку генерации к каждому ответу для удобства
        await msg.answer(res.text, reply_markup=get_photo_kb())
    except:
        await msg.answer("*Ари искрит* Повтори, господин, я отвлеклась...")

@dp.callback_query(F.data == "gen_photo")
async def call_gen(callback: types.CallbackQuery):
    await callback.answer("Генерирую...")
    # Берем последний контекст и делаем фото
    gen_res = model.generate_content(f"Опиши текущий наряд Ари 10 тегами через запятую")
    img_data = await get_image(gen_res.text)
    if img_data:
        await callback.message.answer_photo(types.BufferedInputFile(img_data, filename="a.jpg"))

# WEB SERVER
app = Flask('')
@app.route('/')
def home(): return "Ari Pro v4.0 OK"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

async def main():
    Thread(target=run).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
