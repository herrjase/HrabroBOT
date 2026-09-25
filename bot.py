import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Бот запущен: {client.user}")

    for guild in client.guilds:
        print(f"Сервер: {guild.name}")

        for role in guild.roles:
            print(f"РОЛЬ: {role.name} | ID: {role.id}")


client.run(TOKEN)
