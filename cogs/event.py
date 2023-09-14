from disnake.ext import commands
from disnake import MessageInteraction, Embed, Message, ChannelType

from config import allPlayers
from random import choice
from bot.functions import *


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


def check_dotctor(server_inter, server, embed, target):
    if "Доткор" in server.settings.formated_roles:
        cured_player = server_inter.players_role["Доктор"].get_selected_target()
        if cured_player == target:
            embed.add_field(name="Доктор", value=f"Доктор смог спасти нашего бедалагу, поэтому {cured_player} остается живым!")
        else:
            embed.add_field(name="Доктор", value=f"Доктор не успел приехать на помощь {target}")
            if target.role not in ["Мирный житель", "Бессмертный"]:
                if target.role in ['Мафия', "Крестный отец"]:
                    server.mafia_interaction.kick_mafia_player(target)
                else:
                    server.dead_active_roles.add(target.role)
                                

def remove_player_after_active_roles(server, player):
    if not player:
        return 
    
    if player.role not in ["Мирный житель", "Бессмертный"]:
        if player.role in ['Мафия', "Крестный отец"] or check_werewolf(server, player):
            server.mafia_interaction.kick_mafia_player(player)
        else:
            server.dead_active_roles.add(player.role)
    
    remove_player_for_memory(server, player.user.id)


async def make_end_after_night(inter: MessageInteraction, server):
    server_inter = server.server_interaction
    embed = Embed(title="Наступает день", description="Активные роли сделали свой выбор")

    killed_players = []
    killers = []

    if check_role_in_formated_roles(server, "Мафия"):    
        if server.mafia_killed_player.role == "Бессмертный":
            embed.add_field(name="Мафия", value=f"Этой ночью, мафия не смогла никого убить")
            killed_players.append(server.mafia_killed_player)
            killers.append(choice(server.mafia_interaction.mafia_players))
        else:
            value_kill = f"Этой ночью, мафия захотела избавиться от {server.mafia_killed_player}."

            embed.add_field(name="Мафия", value=value_kill)

    maniac_killed_player = None
    if check_role_in_formated_roles(server, "Маньяк"):
        maniac = server_inter.players_role["Маньяк"]
        maniac_killed_player = maniac.get_selected_target()
        if maniac_killed_player == "" or maniac_killed_player.role == "Бессмертный":
            embed.add_field(name="Маньяк", value=f"Этой ночью, маньяк никого не убил")
        else:
            embed.add_field(name="Маньяк", value=f"Этой ночью, маньяк распотрошил {maniac_killed_player}")
            killed_players.append(maniac_killed_player)
            killers.append(maniac.player)

    kamikaze_killed_player = None
    if check_role_in_formated_roles(server, "Камикадзе"):
        kamkiaze = server_inter.players_role["Камикадзе"]
        kamikaze_killed_player = kamkiaze.get_selected_target()
        if kamikaze_killed_player:
            embed.add_field(name="Камикадзе", value=f"{kamkiaze.player} смог обнаружить Комиссара ({kamikaze_killed_player}), и ценой своей жизнью, уничтожил его")
            killed_players.append(kamikaze_killed_player)
            killers.append(kamkiaze.player)

            remove_player_for_memory(server, kamkiaze.player.user.id)

    if check_role_in_formated_roles(server, "Свидетель"):
        witness = server.server_interaction.players_role["Свидетель"]
        witness_seleted_player = witness.get_selected_target()
        if witness_seleted_player in killed_players:
            await witness.player.user.send(f"{killers[killed_players.index(witness_seleted_player)]} убил игрока {witness_seleted_player}")

    if check_role_in_formated_roles(server, "Телохранитель"):
        bodyguard = server_inter.players_role["Телохранитель"]
        protected_player = bodyguard.get_selected_target()
        if protected_player in killed_players: 
            field_value = f"Телохранитель, ценой своей жизнью, спас {protected_player}"

            killed_players.append(bodyguard.player)

            embed.add_field(name="Телохранитель", value=field_value)
        else:
           remove_player_after_active_roles(server, maniac_killed_player)
           remove_player_after_active_roles(server, kamikaze_killed_player)
           killed_players.remove(maniac_killed_player)
           killed_players.remove(kamikaze_killed_player)

    if check_role_in_formated_roles(server, "Доктор"):
        cured_player = server_inter.players_role["Доктор"].get_selected_target()
        if cured_player in killed_players:
            embed.add_field(name="Доктор", value=f"Доктор успел приехать на помощь {cured_player}")
            killed_players.remove(cured_player)
        else:
            embed.add_field(name="Доктор", value=f"Доктор не успел приехать на помощь игрокам")

    for player in killed_players:
        remove_player_after_active_roles(server, player)
            
    await check_win_and_make_after_win(embed, server, server.last_inter)

    server.clear_cache_night()


async def make_action_active_roles(inter, server, role, target, author):
    if role not in ["komisar", "mafia", "godfather"]:
        if target == "skip":
            role.active_role.change_select("")
            await server.leader.send(f"{role}: пропустил ход")
            return await inter.followup.send("Вы пропустили ход")
        
        role.active_role.change_select(target)
        await server.leader.send(role.active_role.messages[0].format(target))
        await inter.followup.send(role.active_role.messages[1].format(target))
    else:
        match role:
            case "komisar":
                await server.leader.send(f"Комиссар проверил {target}")

                if server.check_player_role(target):
                    await inter.followup.send(f"{target} является мафией!!")
                else:
                    await inter.followup.send(f"{target} не является мафией")
            case "mafia":
                await server.mafia_interaction.send_voting(inter, target)
            case "godfather":
                server.mafia_kill_player(target)
                await server.leader.send(f"Мафия убила {target}")
                await server.mafia_interaction.send_mafia_players(f"По итогу обсуждения, был убит {target}")
        


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
        author = allPlayers.get(inter.author.id)    

        if not author:
            return await inter.response.send_message("Вы не являетесь участником игры!!!!!", ephemeral=True)
        
        if component_ids[2] == "skip":
            target = "skip"
        else:
            target = allPlayers.get(int(component_ids[2]))
            server = target.server

        if "mafia" != component_ids[1]:
            await inter.message.delete()

        await inter.response.defer()

        await make_action_active_roles(inter, server, component_ids[1], target, author)

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
        
        rapist = server.server_interaction.players_role["Насильник"]
        if rapist and rapist.selected_target == author:
            return await inter.response.send_message("Вы не можете голосовать этим днем.", ephemeral=True)
        
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
            embed.add_field(name="Итог", value=f"По итогам голосовани, в тюрьму был посажен {players_expeled}")

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
        
        server = player.server
        rapist = server.server_interaction.players_role["Насильник"]
        if rapist and rapist.selected_target == player:
            return await message.channel.send("Этой ночью вы не сможете участвовать в обсуждении")

        author = message.author
        
        embed = Embed(description=message.content)
        embed.set_author(name=author.global_name if author.global_name else author.name, icon_url=author.avatar.url)

        for mafia in server.mafia_interaction.mafia_players:
            if mafia.user != author:
                if mafia.is_redirect:
                    await server.leader.send(embed=embed)
                else:
                    await mafia.user.send(embed=embed)


def setup(bot):
    bot.add_cog(Events(bot))