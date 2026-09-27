import os
import discord
import random
import threading

from flask import Flask, render_template, request, redirect
from urllib.parse import quote_plus


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
# ПОГОВОРКИ
# =========================================================

@client.event
async def on_message(message):

    # Не отвечаем самому себе
    if message.author == client.user:
        return

    # 25% вероятность ответить поговоркой
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

    print(f"Веб-сайт запускается на порту {port}")

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