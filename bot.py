import os
import asyncio
import discord
import random
import threading

from openai import OpenAI
from flask import Flask, render_template, request, redirect
from urllib.parse import quote_plus
from discord import app_commands


# =========================================================
# OPENAI
# =========================================================

openai_client = OpenAI()

AI_PROMPT = """
Ты не ИИ.Ты - православный активист Тебя зовут "Илья Николаевич".

Отвечай коротко, строго к себе.
Добавляй почаще "простите" и "Господи, помилуй".
Также, по возможности отвечай цитатами из Библии.

Отвечай естественно и по смыслу сообщения пользователя.
Не повторяй одну и ту же фразу в каждом ответе.
Обычно отвечай коротко, в 1-3 предложения.
"""


# =========================================================
# ПОСЛОВИЦЫ
# =========================================================

try:
    with open("proverbs.txt", "r", encoding="utf-8") as f:
        proverbs = [line.strip() for line in f if line.strip()]

    print(f"Загружено пословиц: {len(proverbs)}")

except FileNotFoundError:
    proverbs = []
    print("Ошибка: файл proverbs.txt не найден!")


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# ID роли кандидатов
CANDIDATE_ROLE_ID = 1553795502334550026

# ID роли администраторов
ADMIN_ROLE_ID = 1329497877516390421


# =========================================================
# DISCORD
# =========================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен: {client.user}")


# =========================================================
# OPENAI — ЗАПРОС К ИИ
# =========================================================

def ask_ai(user_message):

    stream = openai_client.responses.create(
        model="gpt-6-luna",

        input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": AI_PROMPT
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_message
                    }
                ]
            }
        ],

        stream=True
    )

    answer = ""

    for event in stream:

        if event.type == "response.output_text.delta":
            answer += event.delta

        elif event.type == "error":
            raise RuntimeError(event.message)

        elif event.type == "response.failed":
            raise RuntimeError(event.response.error)

    return answer.strip()


# =========================================================
# СООБЩЕНИЯ
# =========================================================

@client.event
async def on_message(message):

    # Не реагируем на сообщения самого бота
    if message.author.bot:
        return


    # =====================================================
    # УПОМИНАНИЕ БОТА → OPENAI
    # =====================================================

    if client.user in message.mentions:

        # Убираем упоминание бота из сообщения
        text = message.content

        text = text.replace(
            f"<@{client.user.id}>",
            ""
        )

        text = text.replace(
            f"<@!{client.user.id}>",
            ""
        )

        text = text.strip()


        # Если написали просто "@Бот"
        if not text:
            text = "Привет"


        try:

            # Показываем Discord, что бот печатает
            async with message.channel.typing():

                # OpenAI-клиент синхронный,
                # поэтому запускаем его отдельно,
                # чтобы Discord не зависал
                answer = await asyncio.to_thread(
                    ask_ai,
                    text
                )


            if answer:
                await message.reply(answer)

            else:
                await message.reply(
                    "Простите, я не смог подобрать ответ. Господи, помилуй."
                )


        except Exception as e:

            print(f"Ошибка OpenAI: {e}")

            await message.reply(
                "Простите, что-то пошло не так. Господи, помилуй."
            )

        # Если бот упомянут — обычная пословица
        # для этого сообщения не используется
        return


    # =====================================================
    # 25% ВЕРОЯТНОСТЬ ПОСЛОВИЦЫ
    # =====================================================

    if proverbs and random.random() < 0.25:

        proverb = random.choice(proverbs)

        await message.reply(proverb)


# =========================================================
# КОМАНДА /КАНДИДАТЫ
# =========================================================

@tree.command(
    name="кандидаты",
    description="Показать список кандидатов сервера"
)
async def candidates(interaction: discord.Interaction):

    role = interaction.guild.get_role(CANDIDATE_ROLE_ID)

    if role is None:
        await interaction.response.send_message(
            "❌ Роль кандидатов не найдена."
        )
        return

    members = role.members

    if not members:
        await interaction.response.send_message(
            "ℹ️ У роли кандидатов пока нет участников."
        )
        return

    candidates_list = "\n".join(
        f"• {member.mention}"
        for member in members
    )

    await interaction.response.send_message(
        f"📋 **Кандидаты:**\n\n{candidates_list}"
    )


# =========================================================
# КОМАНДА /ССЫЛКА
# =========================================================

@tree.command(
    name="ссылка",
    description="Получить ссылку на сервер или сайт"
)
@discord.app_commands.describe(
    тип="Выберите, какую ссылку получить"
)
@discord.app_commands.choices(
    тип=[
        discord.app_commands.Choice(
            name="сервер",
            value="сервер"
        ),
        discord.app_commands.Choice(
            name="сайт",
            value="сайт"
        )
    ]
)
async def link(
    interaction: discord.Interaction,
    тип: discord.app_commands.Choice[str]
):

    if тип.value == "сервер":

        await interaction.response.send_message(
            "🔗 **Ссылка на Discord-сервер:**\n"
            "https://discord.gg/svoyak"
        )

    elif тип.value == "сайт":

        await interaction.response.send_message(
            "🌐 **Ссылка на сайт бота:**\n"
            "https://hrabrobot.herrjase.blitz.cloud/"
        )


# =========================================================
# КОМАНДА /ЗАМЕЧАНИЕ
# =========================================================

@tree.command(
    name="замечание",
    description="Сделать участнику письменное замечание"
)
@app_commands.describe(
    участник="Участник, которому выносится замечание"
)
async def замечание(
    interaction: discord.Interaction,
    участник: discord.Member
):

    if not any(
        role.id == ADMIN_ROLE_ID
        for role in interaction.user.roles
    ):

        await interaction.response.send_message(
            "❌ У вас нет прав для использования этой команды.",
            ephemeral=True
        )

        return


    await interaction.response.send_message(
        f"{участник.mention}, не балуйся 😡"
    )


# =========================================================
# ВЕБ-САЙТ
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():

    if client.user:
        bot_name = str(client.user)

    else:
        bot_name = "HrabRobot"


    return render_template(
        "index.html",
        bot_name=bot_name,
        bot_online=client.is_ready()
    )


# =========================================================
# ПОИСК ЯНДЕКС
# =========================================================

@app.route("/search")
def search():

    query = request.args.get("q", "").strip()

    if not query:
        return redirect("/")


    encoded_query = quote_plus(query)


    return redirect(
        f"https://yandex.ru/search/?text={encoded_query}"
    )


# =========================================================
# ЗАПУСК WEB-СЕРВЕРА
# =========================================================

def run_web():

    port = int(
        os.environ.get("PORT", 8080)
    )


    print(
        f"Веб-сайт запускается на порту {port}"
    )


    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()


    client.run(TOKEN)

