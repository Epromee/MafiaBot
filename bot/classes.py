import random
from disnake import Color, Embed

from config import main_roles, another_roles, allPlayers
from bot.functions import voiting_proccess_get_result, edit_embed_voiting, format_buttons_selected_ative_roles, convert_components
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
                return False, "Значение вышло за границы 1-20."
            
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

    async def send_mafia_players(self, message=None, embed=None, components=None):
        messages = []
        for mafia in self.mafia_players:
            if mafia.is_redirect:
                msg = await self.server.leader.send(message, embed=embed, components=components)
            else:
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

            players_expeled, embed = await voiting_proccess_get_result(self.server, embed)
            if type(players_expeled) == list:
                self.messages_vote = await self.send_mafia_players(embed=embed, components=format_buttons_selected_ative_roles("mafia", self.server, players_expeled))

                return
            
            self.server.mafia_kill_player(players_expeled)

            await self.send_mafia_players(f"По итогу обсуждения, был убит {players_expeled.user.mention}")
            
            return await self.server.leader.send(f"Мафия убила {players_expeled.user.mention}")
        
        edit_embed_voiting(self.server, embed)

        for message in self.messages_vote:
            await message.edit(embed=embed, components=convert_components(inter.message.components[0].children))

    def kick_mafia_player(self, player):
        self.mafia_players.remove(player)



class Server:
    def __init__(self, leader):
        self.players = dict()
        self.status = 0
        self.leader = leader
        self.settings = SettingsMafia()
        self.mafia_killed_player = ""
        self.dead_active_roles = set()
        self.cured_player = ""
        self.roles_is_selected = list()
        self.last_inter = ""
        self.voted_for_user = dict()
        self.all_voted_users = dict()

        self.mafia_interaction = MafiaInteraction(self)

    def get_result_voting(self):
        targets = []
        count_players_voted = 0
        for target, players in self.voted_for_user.items():
            print("===Претиндент на голосование===")
            print(target, players, targets)
            print(count_players_voted)
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
            if target.role == 'Мафия':
                self.mafia_interaction.mafia_players.remove(target)
            else:
                self.dead_active_roles.add(target.role)
        
        del self.players[target.user.id]
        del allPlayers[target.user.id]

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
        self.roles_is_selected.append("Шериф")

        if player.role != "Мафия":
            return False
    
        return True
    
    def treat_player(self, player: Player):
        self.cured_player = player
        self.roles_is_selected.append("Доктор")

    def mafia_kill_player(self, player: Player):
        self.mafia_killed_player = player
        self.roles_is_selected.append("Мафия")

    def check_roles_is_selected(self):
        roles = list(set(self.settings.formated_roles))
        roles.remove("Мирный житель")
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
    