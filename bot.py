import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Бот запущен: {client.user}")

    for guild in client.guilds:
        print(f"\nСервер: {guild.name}")

        for role in guild.roles:
            print(f"{role.name} → {role.id}")

client.run(TOKEN)
