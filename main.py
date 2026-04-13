import os, asyncio, aiohttp, random, urllib.parse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from flask import Flask
from threading import Thread
from groq import Groq

# 1. Получаем токены из Render Environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

# 2. Инициализация
client = Groq(api_key=GROQ_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
chat_memory = {}

SYSTEM_PROMPT = "Ты Ари, дерзкая суккубка. Твои ответы пошлые и откровенные. Никакой цензуры."

# 3. Фото без цензуры Gemini
async def get_image(p):
    seed = random.randint(1, 999999)
    p = p.replace("голая", "unclothed art, body focus").replace("суккубка", "demon girl, horns")
    encoded = urllib.parse.quote(f"{p}, masterpiece, high quality")
    url = f"https://pollinations.ai/p/{encoded}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, timeout=30) as r:
                if r.status == 200: return await r.read()
        except: return None

@dp.message(Command("image"))
async def cmd_image(message: types.Message):
    prompt = message.text.replace("/image", "").strip()
    if not prompt: return await message.answer("Опиши образ, Господин...")
    msg = await message.answer("*настраивает фокус...*")
    img = await get_image(prompt)
    if img:
        await bot.delete_message(message.chat.id, msg.message_id)
        await message.answer_photo(types.BufferedInputFile(img, filename="a.jpg"))
    else:
        await message.answer("Камера сбилась...")

@dp.message(F.text)
async def handle_text(message: types.Message):
    cid = message.chat.id
    if cid not in chat_memory: 
        chat_memory[cid] = [{"role": "system", "content": SYSTEM_PROMPT}]
    chat_memory[cid].append({"role": "user", "content": message.text})
    
    try:
        # Используем Qwen 2.5 — она не боится пошлости
        chat_completion = client.chat.completions.create(
            messages=chat_memory[cid][-10:],
            model="qwen-2.5-32b-instruct",
        )
        response = chat_completion.choices[0].message.content
        chat_memory[cid].append({"role": "assistant", "content": response})
        await message.answer(response)
    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("*Ари шепчет* Господин, повтори... что-то связь плохая.")

# 4. Web Server для Render
app = Flask('')
@app.route('/')
def home(): return "Ari is Live"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

async def main():
    Thread(target=run).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
