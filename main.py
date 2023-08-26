import disnake
import os
from disnake.ext import commands 


bot = commands.Bot(command_prefix=commands.when_mentioned, intents=disnake.Intents.all())


for filename in os.listdir("cogs"):
    if filename.endswith(".py") and filename != "general.py":
        bot.load_extension(f"cogs.{filename[:-3]}")


with open('token', "r") as fr:
    token = fr.read()
bot.run(token)
