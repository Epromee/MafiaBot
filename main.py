import disnake
import os
from disnake.ext import commands
from config import owner_id


bot = commands.Bot(command_prefix=commands.when_mentioned_or("."), intents=disnake.Intents.all(), owner_id=owner_id)

for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

with open('token', "r") as fr:
    token = fr.read()
bot.run(token)
