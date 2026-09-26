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
# СООБЩЕНИЯ
# =========================================================

@client.event
async def on_message(message):

    # Не реагируем на сообщения самого бота
    if message.author == client.user:
        return

    # 25% вероятность ответить поговоркой
    if proverbs and random.random() < 0.25:

        proverb = random.choice(proverbs)

        await message.reply(proverb)


# =========================================================
# КОМАНДА /АДМИНЫ
# =========================================================

@tree.command(
    name="админы",
    description="Показать список администраторов сервера"
)
async def admins(interaction: discord.Interaction):

    role = interaction.guild.get_role(ADMIN_ROLE_ID)

    if role is None:

        await interaction.response.send_message(
            "❌ Роль администраторов не найдена."
        )

        return

    members = role.members

    if not members:

        await interaction.response.send_message(
            "ℹ️ У роли администраторов пока нет участников."
        )

        return

    admins_list = "\n".join(
        f"• {member.mention}"
        for member in members
    )

    await interaction.response.send_message(
        f"👑 **Администраторы сервера:**\n\n{admins_list}"
    )


# =========================================================
# ВЕБ-САЙТ
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():

    # Проверяем состояние Discord-бота
    bot_online = client.is_ready()

    # Получаем имя бота
    if client.user:
        bot_name = str(client.user)
    else:
        bot_name = "HrabRobot"

    return render_template(
        "index.html",
        bot_name=bot_name,
        bot_online=bot_online
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
# ЗАПУСК ВЕБ-СЕРВЕРА
# =========================================================

def run_web():

    # Blitz.cloud обычно передаёт порт
    # через переменную окружения PORT

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

    # Запускаем веб-сайт отдельно,
    # чтобы Discord-бот продолжал работать.

    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    # Запускаем Discord-бота
    client.run(TOKEN)