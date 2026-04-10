import asyncio

import os

import aiohttp

import logging

from aiogram import Bot, Dispatcher, types

from aiogram.filters import Command



# Логирование только для консоли (в чат это не пойдет)

logging.basicConfig(level=logging.INFO)



# КЛЮЧИ

TOKEN = os.getenv("BOT_TOKEN", "8602166249:AAHLWwctXJnd6FwHtda7gcIjobKPkOjoF-g")

AI_KEY = os.getenv("AI_KEY", "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")



bot = Bot(token=TOKEN)

dp = Dispatcher()



@dp.message(Command("start"))

async def start_cmd(message: types.Message):

    await message.answer("💜 RP-AI готов к работе.")



@dp.message()

async def chat_handler(message: types.Message):

    # Визуальный статус "печатает" в Telegram

    await bot.send_chat_action(message.chat.id, "typing")

    

    headers = {

        "Authorization": f"Bearer {AI_KEY}",

        "Content-Type": "application/json"

    }

    

    payload = {

        "model": "mistralai/pixtral-12b",

        "messages": [

            {"role": "system", "content": "Ты RP-AI, игривая и милая девушка-помощница. Используй *действия* в звездочках."},

            {"role": "user", "content": message.text}

        ]

    }

    

    try:

        async with aiohttp.ClientSession() as session:

            async with session.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as resp:

                if resp.status == 200:

                    data = await resp.json()

                    reply = data['choices'][0]['message']['content']

                    await message.answer(reply)

                else:

                    print(f"Ошибка API: {resp.status}")

    except Exception as e:

        print(f"Ошибка: {e}")



async def main():

    print("🚀 Запуск RP-AI...")

    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())
