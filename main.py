import os, asyncio, aiohttp, random, urllib.parse
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatAction
from aiogram.filters import Command
from flask import Flask
from threading import Thread
from groq import Groq

# Ключи
BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_KEY = os.getenv("AI_KEY")

client = Groq(api_key=AI_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ТВОЙ ОГРОМНЫЙ ПРОМПТ (ВСТАВЛЯЙ СЮДА) ---
# Совет: добавь в свой текст фразу "Отвечай ТОЛЬКО за своего персонажа, никогда не пиши за меня."
SYSTEM_PROMPT = """
ЗДЕСЬ ТВОЙ ОГРОМНЫЙ ТЕКСТ
"""
# ------------------------------------------

chat_memory = {}

# НОВАЯ БЕЗЦЕНЗУРНАЯ ГЕНЕРАЦИЯ (Pollinations)
async def get_image(prompt):
    # Кодируем текст, чтобы не было ошибок в ссылке
    encoded_prompt = urllib.parse.quote(f"photorealistic, 8k, nsfw, sexy, {prompt}")
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={random.randint(1,10000)}&model=flux&nologo=true"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                if r.status == 200: return await r.read()
        except: return None

@dp.message(Command("image"))
async def cmd_image(message: types.Message):
    prompt = message.text.replace("/image", "").strip()
    if not prompt: return await message.answer("*шепчет* Опиши, какой наряд мне надеть...")
    
    status_msg = await message.answer("*готовится к кадру...*")
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
    
    img = await get_image(prompt)
    if img:
        await bot.delete_message(message.chat.id, status_msg.message_id)
        await message.answer_photo(types.BufferedInputFile(img, filename="ari.jpg"), caption="Для тебя, мой господин...")
    else:
        await message.answer("Сеть перегружена, попробуй еще раз!")

@dp.message(F.text)
async def handle_text(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in chat_memory: 
        chat_memory[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    chat_memory[chat_id].append({"role": "user", "content": message.text})
    await bot.send_chat_action(chat_
