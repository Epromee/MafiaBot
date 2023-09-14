import random
from disnake import Color, Embed

from config import main_roles, another_roles, allPlayers
from bot.functions import *
from pprint import pprint


class SettingsMafia:
    def __init__(self):
        self.roles = {}

        self.maximum_players_count = 15
        self.minimum_players_count = 4

        self.roles.update(main_roles)
        self.roles.update(another_roles)

        self.formated_roles = []

    def format_roles(self, count):
        mafia = count // 3
        count -= mafia

        for i in range(mafia):
            self.formated_roles.append("Мафия")

        if mafia > 1:
            self.formated_roles.remove("Мафия")
            self.formated_roles.append("Крестный отец")

        for i in range(count):
            self.formated_roles.append("Мирный житель")

        for k in another_roles.keys():
            if count < 2:
                break

            self.formated_roles.remove("Мирный житель")
            self.formated_roles.append(k)

            count -= 1

        random.shuffle(self.formated_roles)
        pprint(self.formated_roles)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            try:
                value = int(v)
            except:
                return False, "Неправильный формат данных!"
            
            if value > 20 or value < 1:
                return False, "Значение вышло за границы 3-20."
            
            if k == "maximum_players_count":
                self.maximum_players_count = value
            elif k == "minimum_players_count":
                
                self.minimum_players_count = value

        return True, None




class Player:
    def __init__(self, user, server, role=None):
        self.user = user
        self.server = server
        self.role = role
        self.is_redirect = False

    def __str__(self):
        return self.user.mention




class MafiaInteraction:
    def __init__(self, server):
        self.server = server
        self.mafia_players = []
        self.messages_vote = []

    async def send_roles(self):
        roles = ""
        for player in self.mafia_players:
            roles += f"- {player} -> {player.role}\n"

        if check_role_in_formated_roles(self.server, "Камикадзе"):
            roles += f"- {self.server.server_interaction.players_role['Камикадзе'].player} -> Камикадзе"
        if check_role_in_formated_roles(self.server, "Насильник"):
            roles += f"- {self.server.server_interaction.players_role['Насильник'].player} -> Насильник"

        await self.send_mafia_players(embed=Embed(title="Мафия", description=roles))

    async def send_mafia_players(self, message=None, embed=None, components=None):
        messages = []
        for mafia in self.mafia_players:
            if mafia.is_redirect:
                msg = await self.server.leader.send(message, embed=embed, components=components)
            else:
                rapist = self.server.server_interaction.players_role["Насильник"]
                if rapist and rapist.selected_target == mafia:
                    continue
                
                msg = await mafia.user.send(message, embed=embed, components=components)

            messages.append(msg)

        return messages

    async def send_voting(self, inter, target):
        embed = Embed(title="Выбор", description="Выберите игрока, которого хотите убить", color=Color.red())

        author = allPlayers.get(inter.author.id)

        self.server.vote(author, target)

        if self.server.is_all_voted_mafia_users():
            for message in self.messages_vote:
                await message.delete()

            self.messages_vote.clear()

            players_expeled, embed = await voiting_proccess_get_result(self.server, embed, True)
            if type(players_expeled) == list:
                if self.server.server_interaction.players_role["Крестный отец"]:
                    await self.send_mafia_players(embed=embed)

                    godfather_embed = Embed(title="Выбор", description="Выберите игрока, который по итогу будет убит", color=Color.red())

                    await self.server.server_interaction.players_role["Крестный отец"].player.user.send(embed=godfather_embed, components=format_buttons_selected_ative_roles("godfather", self.server))
                else:
                    self.messages_vote = await self.send_mafia_players(embed=embed, components=format_buttons_selected_ative_roles("mafia", self.server, players_expeled))

                return

            self.server.mafia_kill_player(players_expeled)

            await self.send_mafia_players(f"По итогу обсуждения, был убит {players_expeled}")
            
            return await self.server.leader.send(f"Мафия убила {players_expeled}")
        
        edit_embed_voiting(self.server, embed)

        for message in self.messages_vote:
            await message.edit(embed=embed, components=convert_components(inter.message.components[0].children))

    def kick_mafia_player(self, player):
        self.mafia_players.remove(player)
        if check_role_in_formated_roles(self.server, "Оборотень"):
            if not self.server.werewolf_reincarnated:
                self.server.werewolf_reincarnate()


class ActiveRole:
    def __init__(self, server, player, messages):
        self.messages = messages
        self.player = player
        self.selected_target = ""
        self.server = server

    def get_selected_target(self):
        target = self.selected_target
        self.selected_target = ""
        return target

    def change_select(self, target):
        self.server.roles_is_selected.append(self.player.role)
        self.selected_target = target


class ServerInteraction:
    def __init__(self):
        self.players_role = {
            "Оборотень": "",
            "Камикадзе": "",
            "Крестный отец": "",
            "Телохранитель": "",
            "Доктор": "",
            "Маньяк": "",
            "Свидетель": "",
            "Любовница": "",
            "Насильник": "",
        }

        self.messages_optional_roles = []

    def add_optional_message(self, message):
        self.messages_optional_roles.append(message)

    async def remove_all_optional_messages(self):
        for message in self.messages_optional_roles:
            await message.delete()



class Server:
    def __init__(self, leader):
        self.players = dict()
        self.dead_active_roles = set()
        self.roles_is_selected = list()
        self.voted_for_user = dict()
        self.all_voted_users = dict()

        self.status = 0
        self.last_inter = ""
        self.leader = leader

        self.mafia_killed_player = ""
        self.werewolf_reincarnated = False

        self.settings = SettingsMafia()
        self.mafia_interaction = MafiaInteraction(self)
        self.server_interaction = ServerInteraction()

    def werewolf_reincarnate(self):
        self.werewolf_reincarnated = True

    def get_result_voting(self):
        targets = []
        count_players_voted = 0
        for target, players in self.voted_for_user.items():
            if len(players) > count_players_voted:
                count_players_voted = len(players)
                if len(targets) > 1:
                    targets.clear()
                    targets.append(target)
                elif len(targets) == 1:
                    targets[0] = target
                else:
                    targets.append(target)

            elif len(players) == count_players_voted:
                targets.append(target)

        return targets

    def expel_target(self, target):        
        if target.role != "Мирный житель":
            if target.role in ['Мафия', "Крестный отец"]:
                self.mafia_interaction.mafia_players.remove(target)
            else:
                self.dead_active_roles.add(target.role)
        
        remove_player_for_memory(self, target.user.id)

    def vote(self, author, target):
        _target = self.all_voted_users.get(author)
        if _target:
            self.voted_for_user[_target].remove(author)

        vot_info_target = self.voted_for_user.get(target)
        if vot_info_target:
            self.voted_for_user[target].add(author)
        else:
            self.voted_for_user[target] = {author}

        self.all_voted_users[author] = target

    def is_all_voted_mafia_users(self):
        if len(self.mafia_interaction.mafia_players) == len(self.all_voted_users):
            return True
        
        return False

    def is_all_voted_users(self):
        if len(self.players) == len(self.all_voted_users):
            return True
        
        return False

    def check_player_role(self, player: Player):
        self.roles_is_selected.append("Комиссар")

        if player.role not in ["Мафия", "Крестный отец"] or (player.role == "Оборотень" and not self.werewolf_reincarnated):
            return False
    
        return True

    def mafia_kill_player(self, player: Player):
        self.mafia_killed_player = player
        self.roles_is_selected.append("Мафия")

    def remove_extra_role(self, roles: list, role: str):
        if role in self.settings.formated_roles:
            if self.server_interaction.players_role[role].selected_target:
                roles.remove(role)

    def check_roles_is_selected(self):
        roles = list(set(self.settings.formated_roles))
        roles.remove("Мирный житель")
        self.remove_extra_role(roles, "Бессмертный")
        self.remove_extra_role(roles, "Оборотень")
        self.remove_extra_role(roles, "Крестный отец")

        for dead_role in self.dead_active_roles:
            roles.remove(dead_role)

        self.roles_is_selected.sort()
        roles.sort()

        if self.roles_is_selected == roles:
            return True
        
        return False
    
    def clear_cache_day(self):
        self.voted_for_user = {}
        self.all_voted_users = {}

    def clear_cache_night(self):
        self.cured_player = ""
        self.roles_is_selected = []
        self.mafia_killed_player = ""
        self.clear_cache_day()

    def check_mafia_win(self):
        if len(self.mafia_interaction.mafia_players) == len(self.players) - len(self.mafia_interaction.mafia_players) or len(self.players) - len(self.mafia_interaction.mafia_players) == 0:
            return True
        
        return False
    
    def check_mir_win(self):
        if len(self.mafia_interaction.mafia_players) == 0:
            return True
        
        return False
    