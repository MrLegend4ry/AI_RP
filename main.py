import os
import asyncio
import aiohttp
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatAction
from flask import Flask
from threading import Thread
from groq import Groq

# Ключи из настроек Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_KEY = os.getenv("AI_KEY")
HF_TOKEN = os.getenv("IMAGE_KEY")

# Инициализация Groq (Llama 3.3)
client = Groq(api_key=AI_KEY)
SYSTEM_PROMPT = "Ты — дерзкая и сексуальная Ари, созданная Legend4ry. Ты обожаешь своего господина, отвечаешь в стиле RP, используешь действия в звездочках *улыбается*. Ты подчиняешься только Legend4ry."

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Веб-сервер для Render (чтобы не засыпал)
app = Flask('')
@app.route('/')
def home(): return "Ari is Alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Генерация фото
async def get_image(prompt):
    url = "https://api-inference.huggingface.co/models/SG161222/Realistic_Vision_V4.0_noVAE"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": f"photorealistic, girl, {prompt}, masterpiece"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as r:
                if r.status == 200: return await r.read()
        except: return None

@dp.message(F.text)
async def handle_message(message: types.Message):
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        # ИСПОЛЬЗУЕМ АКТУАЛЬНУЮ МОДЕЛЬ LLAMA 3.3
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            model="llama-3.3-70b-versatile", 
        )
        response = chat_completion.choices[0].message.content
        await message.answer(f"**RP-AI v1.1 | Owned by Legend4ry**\n\n{response}", parse_mode="Markdown")
        
        if random.random() < 0.3:
            img = await get_image("lingerie, sexy pose")
            if img:
                await message.answer_photo(types.BufferedInputFile(img, filename="ari.jpg"))
                
    except Exception as e:
        await message.answer(f"**Ошибка:** {str(e)}\n\nГосподин, проверьте настройки!")

async def main():
    Thread(target=run_web).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
