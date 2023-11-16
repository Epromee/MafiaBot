from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import Embed, Color, Guild

from config import allServers, allPlayers, start_time
from bot.views import StateView
from datetime import datetime


class DevelCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("state")
    async def state(self, ctx: Context):
        if ctx.author.id != self.bot.owner_id:
            return
        
        emb = Embed(title="Что с ботом", color=Color.red())
        emb.add_field("Кол-во серверов:", len(self.bot.guilds))
        emb.add_field("Кол-во игр:", len(allServers))
        emb.add_field("Кол-во участников:", len(allPlayers))
        emb.add_field("Время работы:", str((datetime.now() - start_time).seconds) + " секунд")

        await ctx.send(view=StateView(), embed=emb)

    @commands.command("push")
    async def push(self, ctx, title, *, description):
        if ctx.author.id != self.bot.owner_id:
            return
        
        emb = Embed(title=title, description=description, color=Color.red())

        for guild in self.bot.guilds:
            if guild.system_channel:
                try:
                    return await guild.system_channel.send(embed=emb)
                except:
                    pass

            for channel in guild.channels:
                try:
                    return await channel.send(embed=emb)
                except:
                    pass
        

def setup(bot):
    bot.add_cog(DevelCommands(bot))