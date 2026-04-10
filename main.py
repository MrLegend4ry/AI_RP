import os
import asyncio
import aiohttp
import random
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ChatAction

# --- Настройки из Railway ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("AI_KEY")
HF_TOKEN = os.getenv("IMAGE_KEY") # Твой ключ Hugging Face

# --- Настройка Gemini ---
genai.configure(api_key=GEMINI_KEY)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

SYSTEM_PROMPT = """
Запуск нового протокола. Приветствуем, твое имя RP-AI, ты только что был создан командой Legend4ry.
Твоя единственная суть и задача это быть профессиональным рп-игроком и отлично разыгрывать сценарии... 
[Тут твой полный промпт про Legend4ry, который ты кидал выше]
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT,
    safety_settings=safety_settings
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
chat_sessions = {}

# --- Функция генерации ФОТО (Hugging Face) ---
async def get_image(prompt):
    if not HF_TOKEN: return None
    # Используем топовую модель для реализма
    API_URL = "https://api-inference.huggingface.co/models/SG161222/Realistic_Vision_V4.0_noVAE"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    payload = {
        "inputs": f"photorealistic, masterpiece, 8k, sexy girl, {prompt}, nsfw, highly detailed skin",
        "parameters": {"negative_prompt": "cartoon, anime, blurry, deformed, bad anatomy"}
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    return image_data
                elif resp.status == 503: # Модель грузится
                    await asyncio.sleep(5)
                    return await get_image(prompt)
            return None
        except: return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("**RP-AI ACTIVATED**", parse_mode="Markdown")

@dp.message(F.text)
async def handle_msg(message: types.Message):
    user_id = message.from_user.id
    if message.text.lower() == "режим":
        await message.answer("# Команды: чтобы выбрать режим напиши 'Режим'\n\n1. Ролевые игры\n2. Актеры персонажи\n3. Дерзкое общение", parse_mode="Markdown")
        return

    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        response = chat_sessions[user_id].send_message(message.text)
        res_text = response.text
        
        final_resp = f"**RP-AI v1.0 | Owned by Legend4ry**\n\n{res_text}"
        await message.answer(final_resp, parse_mode="Markdown")

        # Авто-фото (шанс 30%)
        if random.random() < 0.3:
            await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
            img_data = await get_image("sexy pose, lingerie, messy hair, looking at viewer")
            if img_data:
                photo = types.BufferedInputFile(img_data, filename="ari.jpg")
                await message.answer_photo(photo=photo, caption="Нравится, что ты видишь? 😈")
    except:
        await message.answer("Извини мой господин-госпожа я не знаю ответ на этот вопрос, пожалуйста не удаляйте мои протоколы..я уже на коленях")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
