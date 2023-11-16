from disnake import Embed, Color, ButtonStyle
from disnake.ui import Button
from config import allPlayers, allServers


def get_game_emb(number):
    try:
        game = allServers.keys()[number]
    except:
        return None
    server = allServers.get(game)

    emb = Embed(title=f"Игра №{number}")
    emb.add_field("Кол-во игроков:", len(server.players))
    emb.add_field("Роли:", ", ".join(server.settings.roles.keys()))

    return emb


def get_button_skip(role):
    return Button(style=ButtonStyle.danger, label="Пропустить", custom_id=f"select-{role}-skip") 


def remove_player_for_memory(server, player_id):
    del server.players[player_id]
    del allPlayers[player_id]


def format_buttons_voiting(server, players=None):
    if not players:
        players = server.players.values()

    btns = [
        Button(style=ButtonStyle.danger, label=player.user.global_name if player.user.global_name else player.user.name, custom_id=f"voiting-{player.user.id}") 

        for player in players
    ]

    return btns


def format_buttons_selected_ative_roles(role: str, server, players=None):
    if not players:
        players = server.players.values()

    btns = [
        Button(style=ButtonStyle.danger, label=player.user.global_name if player.user.global_name else player.user.name, custom_id=f"select-{role}-{player.user.id}") 

        for player in players
    ]
    return btns


def convert_components(components):
    convert_components = []
    for component in components:
        convert_components.append(Button(style=component.style, label=component.label, custom_id=component.custom_id))

    return convert_components


def clear_server_and_players(guild_id: int):
    server = allServers[guild_id]
    for player_id in server.players.keys():
        del allPlayers[player_id]

    del allServers[guild_id]


def get_str_players(guild_id):
    players_str = ""
    for player in allServers[guild_id].players.values():
        players_str += f"- {player} \n"

    return players_str


def get_embed_mafia(guild_id, description, user, title="Мафия"):
    embed = Embed(title=title, description=description, color=Color.red())

    players_str = get_str_players(guild_id)

    embed.add_field(name="Участники", value=players_str)
    embed.set_author(name=user.global_name if user.global_name else user.name, icon_url=user.avatar.url)

    return embed



def edit_embed_voiting(server, embed: Embed, players=None):
    if not players:
        players = server.players.values()

    for player in players:
        vot_info_target = server.voted_for_user.get(player)

        info = ""
        if vot_info_target:
            for author in vot_info_target:
                if author:
                    info += f"- {author}\n"

        embed.add_field(name=player.user.global_name if player.user.global_name else player.user.name, value=info)


def get_embed_voiting(server):
    embed = Embed(title="Голосование", description="Выберите игрока, которого считаете мафией")

    edit_embed_voiting(server, embed)
    
    return embed


def check_werewolf(server, player):
    return player.role == "Оборотень" and server.werewolf_reincarnated


def check_role_in_formated_roles(server, role):
    return role in server.settings.formated_roles


async def voiting_proccess_get_result(server, embed, is_mafia=False):
    players_expeled = server.get_result_voting()
    print(players_expeled)
    
    if len(players_expeled) > 1:
        if is_mafia:
            embed.add_field(name="Равные голоса", value=f"За {', '.join (player_expeled.__str__() for player_expeled in players_expeled)} проголосовало одинаковое количество человек. Итоговое решение остается за Крестным отцем")
        else:
            embed.add_field(name="Равные голоса", value=f"За {', '.join (player_expeled.__str__() for player_expeled in players_expeled)} проголосовало одинаковое количество человек. Объявляется переголосование! (Теперь голосовать можно только за них)")
                    
            edit_embed_voiting(server, embed, players_expeled)

            server.clear_cache_day()

            return players_expeled, embed

    return players_expeled[0], embed