import os
import random
import threading

import discord
from discord import app_commands

from flask import Flask, render_template, request


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# ID роли администраторов
ADMIN_ROLE_ID = 1329497877516390421


# ============================================================
# ПОСЛОВИЦЫ
# ============================================================

try:
    with open("proverbs.txt", "r", encoding="utf-8") as f:
        proverbs = [line.strip() for line in f if line.strip()]

    print(f"Загружено пословиц: {len(proverbs)}")

except FileNotFoundError:
    proverbs = []
    print("Файл proverbs.txt не найден.")


# ============================================================
# DISCORD BOT
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()

    print(f"Бот запущен: {client.user}")
    print(f"ID бота: {client.user.id}")


# ============================================================
# КОМАНДА /АДМИНЫ
# ============================================================

@tree.command(
    name="админы",
    description="Показать администраторов сервера"
)
async def admins(interaction: discord.Interaction):

    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "Эту команду можно использовать только на сервере."
        )
        return

    role = guild.get_role(ADMIN_ROLE_ID)

    if role is None:
        await interaction.response.send_message(
            "Роль администратора не найдена."
        )
        return

    members = [
        member
        for member in guild.members
        if role in member.roles
    ]

    if not members:
        await interaction.response.send_message(
            "Администраторов с этой ролью не найдено."
        )
        return

    text = "\n".join(
        f"• {member.mention}"
        for member in members
    )

    await interaction.response.send_message(
        f"**Администраторы:**\n{text}"
    )


# ============================================================
# ПОГОВОРКИ — 25% ШАНСА
# ============================================================

@client.event
async def on_message(message):

    # Не отвечаем самому себе
    if message.author == client.user:
        return

    # 25% шанс
    if proverbs and random.random() < 0.25:
        await message.channel.send(random.choice(proverbs))


# ============================================================
# WEB-САЙТ
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():

    return render_template(
        "index.html",
        bot_name=str(client.user) if client.user else "HrabRobot",
        bot_online=client.is_ready()
    )


@app.route("/search")
def search():

    query = request.args.get("q", "").strip()

    if query:
        # Перенаправляем пользователя в Яндекс
        from flask import redirect

        return redirect(
            "https://yandex.ru/search/?text=" + query
        )

    return render_template(
        "index.html",
        bot_name=str(client.user) if client.user else "HrabRobot",
        bot_online=client.is_ready()
    )


def run_web():
    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    # Запускаем сайт отдельным потоком,
    # чтобы Discord-бот продолжал работать.
    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    # Запускаем Discord
    client.run(TOKEN)