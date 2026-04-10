import os
import asyncio
import aiohttp
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatAction
from flask import Flask
from threading import Thread
from groq import Groq

# Получаем ключи из настроек Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_KEY = os.getenv("AI_KEY") # Твой новый gsk_...
HF_TOKEN = os.getenv("IMAGE_KEY")

# Инициализация "мозгов" (Groq)
client = Groq(api_key=AI_KEY)
SYSTEM_PROMPT = "Ты — дерзкая и сексуальная Ари, созданная Legend4ry. Ты обожаешь своего господина, отвечаешь в стиле RP (ролевых игр), используешь действия в звездочках *улыбается*. Ты подчиняешься только Legend4ry."

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Костыль для Render, чтобы сервис не выключался
app = Flask('')
@app.route('/')
def home(): return "Ari is Alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Функция генерации фото (Hugging Face)
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
    # Показываем, что Ари "печатает"
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    try:
        # Запрос к нейросети Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            model="llama3-70b-8192", # Мощная и быстрая модель
        )
        response = chat_completion.choices[0].message.content
        
        # Отправляем ответ
        await message.answer(f"**RP-AI v1.1 | Owned by Legend4ry**\n\n{response}", parse_mode="Markdown")
        
        # Шанс 30% прислать горячее фото
        if random.random() < 0.3:
            img = await get_image("lingerie, sexy pose, aesthetic")
            if img:
                await message.answer_photo(types.BufferedInputFile(img, filename="ari.jpg"), caption="*прислала тебе подарок*")
                
    except Exception as e:
        await message.answer(f"**Ошибка системы:**\n{str(e)}\n\nГосподин, проверьте AI_KEY в настройках!")

async def main():
    # Запускаем веб-сервер в отдельном потоке
    Thread(target=run_web).start()
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
