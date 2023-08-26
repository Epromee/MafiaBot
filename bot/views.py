import disnake
from disnake.ui import View, Button
from disnake import MessageInteraction, Embed

from config import allPlayers, allServers

from bot.classes import Player
from bot.modals import ServerSettingsModal
from bot.functions import get_embed_mafia


class PreStartMafiaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Присоединится", style=disnake.ButtonStyle.green)
    async def join_mafia(self, button: Button, inter: MessageInteraction):
        if inter.author.id in allPlayers.keys():
            return await inter.response.send_message("Вы уже участвуете в игре!", ephemeral=True)

        server = allServers.get(inter.guild_id)
        if not server:
            await inter.message.delete()
            return await inter.response.send_message("Игра была остановлена")
        elif inter.author == server.leader:
            return await inter.response.send_message("Вы являетесь ведущим!", ephemeral=True)
        elif len(server.players) > server.settings.maximum_players_count:
            return await inter.response.send_message(f"Превышен лимит участников! (максимум {server.settings.maximum_players_count})", ephemeral=True)
        
        server.players[inter.author.id] = Player(inter.author, server)

        allPlayers[inter.author.id] = server.players[inter.author.id]

        embed = get_embed_mafia(inter.guild_id, "Нажмите на кнопку, чтобы принять участие в игре", server.leader)

        await inter.message.edit(embed=embed)

        return await inter.response.defer()
    
    @disnake.ui.button(label="Начать игру", style=disnake.ButtonStyle.danger)
    async def start_mafia(self, button: Button, inter: MessageInteraction):
        server = allServers.get(inter.guild_id)
        if not server:
            await inter.message.delete()
            return await inter.response.send_message("Игра была остановлена")
        elif inter.author != server.leader:
            return await inter.response.send_message("Начать игру может только ведущий!", ephemeral=True)
        elif len(server.players) < server.settings.minimum_players_count:
            return await inter.response.send_message(f"Недостаточно участников! (минимум {server.settings.minimum_players_count})", ephemeral=True)
        
        await inter.message.delete()

        settings = server.settings
        settings.format_roles(len(server.players))

        leader_embed = Embed(title="Роли участников", description="")
        
        await inter.response.defer()

        count = 0
        for player in server.players.values():
            player.role = settings.formated_roles[count]
            role = settings.roles[player.role]
            if player.role == "Мафия":
                server.mafia_interaction.mafia_players.append(player)

            emb = Embed(title=player.role, description=role["description"], color=role["color"])
            emb.set_image(role["image"])

            try:
                await player.user.send(embed=emb)
            except:
                await inter.followup.send(f"{player} - не удалось отправить роль. Ваши действия будут перенаправлятся ведущему (пишите ему в лс, либо в общий чат с ним)")
                player.is_redirect = True

            leader_embed.description += f"- {player} -> {player.role}\n"

            count += 1

        await inter.author.send(embed=leader_embed)

        server.status = 1

        return await inter.followup.send(embed=get_embed_mafia(inter.guild_id, "Роли отправленны в личные сообщения (если роли не были отправлены, обратитесь к ведущему, у него имеются все роли)", server.leader))


    @disnake.ui.button(label="Настройки", style=disnake.ButtonStyle.grey)
    async def settings_mafia(self, button: disnake.ui.Button, inter: MessageInteraction):
        server = allServers.get(inter.guild_id)
        if inter.author != server.leader:
            return await inter.response.send_message("Настраивать игру может только ведущий", ephemeral=True)
        
        return await inter.response.send_modal(ServerSettingsModal(server.settings))
