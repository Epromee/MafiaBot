import disnake
from disnake.ui import Modal

from disnake import ModalInteraction


class ServerSettingsModal(Modal):
    def __init__(self, settings):
        self.settings = settings

        components = [
            disnake.ui.TextInput(
                label="Максимальное число игроков (границы 1-20)",
                custom_id="maximum_players_count",
                max_length=2,
                placeholder=str(self.settings.maximum_players_count)
            ),
            disnake.ui.TextInput(
                label="Минимальное число игроков (границы 1-20)",
                custom_id="minimum_players_count",
                max_length=2,
                placeholder=str(self.settings.minimum_players_count)
            )
        ]

        super().__init__(title="Настройки игры", components=components)

    async def callback(self, inter: ModalInteraction) -> None:
        is_succes, error_message = self.settings.update(**inter.text_values)

        if is_succes:
            return await inter.response.send_message(f"Настройки игры обновлены!", ephemeral=True)
        
        return await inter.response.send_message(f"{error_message} Настройки не были сохранены..", ephemeral=True)


