from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Embed, Color

from bot.classes import Server, Player

from config import allServers
from bot.functions import get_embed_mafia, format_buttons_selected_ative_roles, get_embed_voiting, format_buttons_voiting, edit_embed_voiting, clear_server_and_players
from bot.views import PreStartMafiaView


class Mafia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="start-mafia", description="Запустить помощника по мафии", dm_permission=False)
    async def start_mafia(self, inter: ApplicationCommandInteraction):
        if allServers.get(inter.guild_id) != None:
            return await inter.response.send_message("Игра уже запущена!")
        
        server = Server(inter.author)
        allServers[inter.guild_id] = server

        embed = get_embed_mafia(inter.guild_id, "Нажмите на кнопку, чтобы принять участие в игре", inter.author)

        await inter.response.send_message(
            embed=embed,
            view=PreStartMafiaView(),
        )

    @commands.slash_command(name="night", description="Наступает ночь (работает при запущенном сервере мафии)", dm_permission=False)
    async def night(self, inter: ApplicationCommandInteraction):
        server = allServers.get(inter.guild_id)
        if server == None or server.status == 0:
            return await inter.response.send_message("Игра не запущена")
        elif inter.author != server.leader:
            return await inter.response.send_message("Управлять игровым процессом может только ведущий!", ephemeral=True)
        
        await inter.response.send_message(embed=get_embed_mafia(inter.guild_id, "Наступает ночь. Город засыпает. Просыпаются активные роли", server.leader, "Ночь"))

        server.last_inter = inter

        for player in server.players.values():
            if player.role == "Мирный житель":
                continue

            if player.is_redirect:
                player = Player(server.leader, server, player.role)
            
            embed = Embed(title="Выбор", color=Color.red())

            role = ""

            if player.role == "Шериф":
                embed.description = "Выберите игрока, роль которого вы хотели бы узнать"
                role = "sherif"
            elif player.role == "Мафия":
                embed.description = "Выберите игрока, которого хотите убить"
                edit_embed_voiting(server, embed)
                role = "mafia"
            elif player.role == "Доктор":
                embed.description = "Выберите игрока, которого хотите спасти"
                role = "doctor"

            message = await player.user.send(embed=embed, components=format_buttons_selected_ative_roles(role, server))
            if role == "mafia":
                server.mafia_interaction.messages_vote.append(message)

    @commands.slash_command(name="start-voting", description="Начать голосование", dm_permission=False)
    async def start_voting(self, inter: ApplicationCommandInteraction):
        server = allServers.get(inter.guild_id)
        if server == None or server.status == 0:
            return await inter.response.send_message("Игра не запущена")
        elif inter.author != server.leader:
            return await inter.response.send_message("Управлять игровым процессом может только ведущий!", ephemeral=True)
        
        embed = get_embed_voiting(server)

        return await inter.response.send_message(embed=embed, components=format_buttons_voiting(server))
    
    @commands.slash_command(name="stop-mafia", description="Закончить игру", dm_permission=False)
    async def stop_mafia(self, inter: ApplicationCommandInteraction):
        server = allServers.get(inter.guild_id)
        if server == None:
            return await inter.response.send_message("Игра не запущена")
        elif inter.author != server.leader:
            return await inter.response.send_message("Управлять игровым процессом может только ведущий!", ephemeral=True)
        
        clear_server_and_players(inter.guild_id)

        return await inter.response.send_message("Игра была предварительно законченна")


def setup(bot):
    bot.add_cog(Mafia(bot))
