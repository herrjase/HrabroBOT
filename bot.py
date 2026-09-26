import os
import discord
import random

# Загружаем пословицы из файла proverbs.txt
try:
    with open("proverbs.txt", "r", encoding="utf-8") as f:
        proverbs = [line.strip() for line in f if line.strip()]

    print(f"Загружено пословиц: {len(proverbs)}")

except FileNotFoundError:
    proverbs = []
    print("Ошибка: файл proverbs.txt не найден!")


TOKEN = os.getenv("DISCORD_TOKEN")

# ID роли администраторов
ADMIN_ROLE_ID = 1329497877516390421


# Настройки Discord
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен: {client.user}")


@client.event
async def on_message(message):
    # Не реагируем на сообщения самого бота
    if message.author == client.user:
        return

    # 25% вероятность ответить поговоркой
    if proverbs and random.random() < 0.25:
        proverb = random.choice(proverbs)
        await message.reply(proverb)


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


client.run(TOKEN)