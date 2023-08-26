from disnake import Embed, Color, ButtonStyle
from disnake.ui import Button
from config import allPlayers, allServers


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
        players_str += "- " + player.user.mention + "\n"

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
                    info += f"- {author.user.mention}\n"

        embed.add_field(name=player.user.global_name if player.user.global_name else player.user.name, value=info)


def get_embed_voiting(server):
    embed = Embed(title="Голосование", description="Выберите игрока, которого считаете мафией")

    edit_embed_voiting(server, embed)
    
    return embed


async def voiting_proccess_get_result(server, embed):
    players_expeled = server.get_result_voting()
    print(players_expeled)
            
    if len(players_expeled) > 1:
        embed.add_field(name="Равные голоса", value=f"За {', '.join (player_expeled.__str__() for player_expeled in players_expeled)} проголосовало одинаковое количество человек. Объявляется переголосование! (Теперь голосовать можно только за них)")
                
        edit_embed_voiting(server, embed, players_expeled)

        server.clear_cache_day()

        return players_expeled, embed

    return players_expeled[0], embed