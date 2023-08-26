from disnake.ext import commands
from disnake import MessageInteraction, Embed, Message, ChannelType, Color

from config import allPlayers
from bot.functions import clear_server_and_players, get_embed_voiting, format_buttons_voiting, voiting_proccess_get_result, convert_components


async def check_win_and_make_after_win(embed: Embed, server, inter):
    is_win_mafia = server.check_mafia_win()
    is_mir_win = server.check_mir_win()
    if is_win_mafia or is_mir_win:
        if is_win_mafia:
            embed.add_field(name="Конец. Победа мафии...", value="Игроков с картой мафии осталось столько же, сколько и игроков с другими картами.")
        elif is_mir_win:
            embed.add_field(name="Конец. Победа мирных жителей!", value="Игроков с картой мафии не осталось!")
                
        survivors = ""
        for player in server.players.values():
            survivors += f"- {player} -> {player.role}\n"

        embed.add_field(name="Выжившие", value=survivors)
        clear_server_and_players(inter.guild_id)
    else:
        embed.add_field(name="Утро", value="Игра продолжается! Начинается общее обсуждение")

    await inter.followup.send(embed=embed)


async def make_end_after_night(inter: MessageInteraction, server):
    embed = Embed(title="Наступает день", description="Активные роли сделали свой выбор")

    embed.add_field(name="Мафия", value=f"Этой ночью, мафия захотела избавиться от {server.mafia_killed_player}")
    if server.cured_player == server.mafia_killed_player:
        embed.add_field(name="Доктор", value=f"Доктор смог спасти нашего бедалагу, поэтому {server.cured_player} остается живым!")
    else:
        embed.add_field(name="Доктор", value=f"Доктор не успел приехать на помощь {server.mafia_killed_player}")
        print(server.mafia_killed_player)
        if server.mafia_killed_player.role != "Мирный житель":
            if server.mafia_killed_player.role == 'Мафия':
                server.mafia_interaction.kick_mafia_player(server.mafia_killed_player)
            else:
                server.dead_active_roles.add(server.mafia_killed_player.role)
                
        del server.players[server.mafia_killed_player.user.id]
        del allPlayers[server.mafia_killed_player.user.id]
            
    await check_win_and_make_after_win(embed, server, server.last_inter)

    server.clear_cache_night()


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(self.bot.user.name)

    @commands.Cog.listener("on_button_click")
    async def active_role_select_user(self, inter: MessageInteraction):
        component_ids = inter.component.custom_id.split("-")
        if component_ids[0] != "select":
            return
        
        print(component_ids)
        if not allPlayers.get(inter.author.id):
            return

        target = allPlayers.get(int(component_ids[2]))
        print(target.user.name)
        try:
            server = target.server
        except:
            print(target, allPlayers)
            exit(400)

        if "mafia" != component_ids[1]:
            await inter.message.delete()

        await inter.response.defer()

        if "sherif" == component_ids[1]:
            await server.leader.send(f"Шериф проверил {target.user.mention}")

            if server.check_player_role(target):
                await inter.followup.send(f"{target.user.mention} является мафией!!")
            else:
                await inter.followup.send(f"{target.user.mention} не является мафией")
        elif "mafia" == component_ids[1]:
            await server.mafia_interaction.send_voting(inter, target)
        elif "doctor" == component_ids[1]:
            server.treat_player(target)
            await server.leader.send(f"Доктор вылечил {target.user.mention}")
            await inter.followup.send(f"Вы вылечили {target.user.mention}")

        if server.check_roles_is_selected():
            await make_end_after_night(inter, server)
        

    @commands.Cog.listener("on_button_click")
    async def voiting_target_select(self, inter: MessageInteraction):
        component_ids = inter.component.custom_id.split("-")
        if component_ids[0] != "voiting":
            return
        
        author = allPlayers.get(inter.author.id)    

        if not author:
            return await inter.response.send_message("Вы не являетесь участником игры!!!!!", ephemeral=True)
        
        target = allPlayers.get(int(component_ids[1]))
        
        await inter.response.defer()

        server = target.server
        server.vote(author, target)
        embed = get_embed_voiting(server)

        if server.is_all_voted_users():
            await inter.message.delete()

            players_expeled, embed = await voiting_proccess_get_result(server, embed)
            if type(players_expeled) == list:
                return await inter.followup.send(embed=embed, components=format_buttons_voiting(server, players_expeled))
            
            server.expel_target(players_expeled)
            embed.add_field(name="Итог", value=f"По итогам голосовани, в тюрьму был посажен {players_expeled.user.mention}")

            await check_win_and_make_after_win(embed, server, inter)

            return server.clear_cache_day()

        return await inter.message.edit(embed=embed, components=convert_components(inter.message.components[0].children))

    @commands.Cog.listener("on_message")
    async def mafia_chat(self, message: Message):
        if message.channel.type != ChannelType.private:
            return
        
        player = allPlayers.get(message.author.id)
        if not player or player.role != "Мафия":
            return
        
        author = message.author
        
        embed = Embed(description=message.content)
        embed.set_author(name=author.global_name if author.global_name else author.name, icon_url=author.avatar.url)
        server = player.server
        for mafia in server.mafia_interaction.mafia_players:
            if mafia.user != author:
                await mafia.user.send(embed=embed)


def setup(bot):
    bot.add_cog(Events(bot))