from disnake.ext import commands, tasks
from disnake import ApplicationCommandInteraction, Embed, Color

from bot.classes import Server, Player

from config import allServers
from bot.functions import *
from bot.views import PreStartMafiaView


class Mafia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(seconds=2)
    async def first_active_roles_thinking(self, role, server):
        print(role)
        if server.server_interaction.players_role[role].selected_player != "":
            self.first_active_roles_thinking.stop()

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
        
        await inter.response.send_message(embed=get_embed_mafia(inter.guild_id, "Наступает ночь. Город засыпает. Просыпаются активные роли (Если в игре есть такие роли, как Любовница и Насильник, то сначал выбирают они, а уже потом будет выбор за другими ролями)", server.leader, "Ночь"))

        server.last_inter = inter
        
        mistress_selected_player = None
        if check_role_in_formated_roles(server, "Любовница"):
            embed = Embed(title="Выбор", color=Color.red())
            embed.description = "Выберите игрока, которого хотите лешить хода ночью"
            mistress = server.server_interaction.players_role["Любовница"]
            await mistress.player.user.send(
                embed=embed, 
                components=format_buttons_selected_ative_roles("mistress", server)
                )
            await self.first_active_roles_thinking.start("Любовница", server)
            mistress_selected_player = mistress.selected_player
        
        rapist = server.server_interaction.players_role["Насильник"]
        rapist_selected_player = None
        if rapist != mistress_selected_player:
            if check_role_in_formated_roles(server, "Насильник"):
                embed = Embed(title="Выбор", color=Color.red())
                embed.description = "Выберите игрока, которого хотите изнасиловать"
                await rapist.player.user.send(
                    embed=embed, 
                    components=format_buttons_selected_ative_roles("rapist", server)
                    )
                await self.first_active_roles_thinking.start("Насильник", server)
                rapist_selected_player = rapist.selected_player

        for player in server.players.values():
            result_werewolf = check_werewolf(server, player)

            if player.role in ["Мирный житель", "Бессмертный"] or (player in [mistress_selected_player, rapist_selected_player]) or not result_werewolf:
                continue

            if player.is_redirect:
                player = Player(server.leader, server, player.role)

            embed = Embed(title="Выбор", color=Color.red())

            role = ""
            if result_werewolf:
                embed.description = "Выберите игрока, которого хотите убить"
                edit_embed_voiting(server, embed)
                role = "mafia"
            else:
                match player.role:
                    case "Комиссар":
                        embed.description = "Выберите игрока, роль которого вы хотели бы узнать"
                        role = "komisar"
                    case "Мафия":
                        embed.description = "Выберите игрока, которого хотите убить"
                        edit_embed_voiting(server, embed)
                        role = "mafia"
                    case "Крестный отец":
                        embed.description = "Выберите игрока, которого хотите убить"
                        edit_embed_voiting(server, embed)
                        role = "mafia"
                    case "Доктор":
                        embed.description = "Выберите игрока, которого хотите спасти"
                        role = "doctor"
                    case "Телохранитель":
                        embed.description = "Выберите игрока, за которого, в случае нападения, вы отдадите свою жизнь"
                        role = "bodyguard"
                    case "Маньяк":
                        embed.description = "Выберите игрока, которого хотите распотрошить"
                        role = "maniac"
                    case "Свидетель":
                        embed.description = "Выберите игрока, убийцу которого, в случае его смерти, вы хотите узнать"
                        role = "witness"
                    case "Камикадзе":
                        embed.description = "Выбирете игрока, которого считаете комиссаром"
                        role = "kamikaze"

            if role in ["maniac", "bodyguard"]:
                btns = format_buttons_selected_ative_roles(role, server)
                btns.append(get_button_skip(role))
                return await player.user.send(embed=embed, components=btns)
            
            message = await player.user.send(
                embed=embed, 
                components=format_buttons_selected_ative_roles(role, server)
                )
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
