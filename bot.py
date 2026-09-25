import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

# ID роли администраторов
ADMIN_ROLE_ID = 1329497877516390421

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен: {client.user}")


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
