import math

import discord
import discord.ui as dui
from discord.interactions import Interaction

from .voivo import Speaker, Style


def make_option(i: int, x: Speaker):
    description = "スタイル: "
    description += ", ".join([y["name"] for y in x["styles"]])
    return discord.SelectOption(
        label=x["name"], description=description, value=str(i % 25)
    )


class StyleSelect(dui.Select):
    def __init__(self, styles: list[Style], parent: "Board"):
        self.parent = parent
        self.old_selected = 0
        self.styles = styles
        options = [
            discord.SelectOption(label=x["name"], value=str(i))
            for i, x in enumerate(styles)
        ]
        options[0].default = True
        super().__init__(placeholder="Select a style", options=options, row=1)

    async def callback(self, interaction: Interaction):
        selected = int(self.values[0])
        self.options[self.old_selected].default = False
        option = self.options[selected]
        option.default = True
        self.parent.speaker_id = self.styles[selected]["id"]
        self.parent.update_buttons()
        await interaction.response.edit_message(view=self.parent)
        self.old_selected = selected


class SpeakerSelect(dui.Select):
    def __init__(self, speakers: list[Speaker], parent: "Board"):
        self.parent = parent
        # self.__old_selected: int | None = None
        self.old_selecteds: list[int | None] = [None] * math.ceil(len(speakers) / 25)
        self.speakers = speakers

        self.all_options = [make_option(i, x) for i, x, in enumerate(speakers)]
        self.page = 0
        # print(len(self.all_options))
        # print(self.all_options)
        # print(self.has_next())
        # print(self.has_prev())
        super().__init__(
            placeholder="Select a speaker", options=self.all_options[:25], row=0
        )

    async def callback(self, interaction: Interaction):
        # print(self.values)
        if self.old_selected is not None:
            self.options[self.old_selected].default = False

        selected = int(self.values[0])
        speaker = self.speakers[selected]
        option = self.options[selected]
        option.default = True
        item = discord.utils.find(
            lambda x: isinstance(x, StyleSelect), self.parent.children
        )
        if item is not None:
            self.parent.remove_item(item)

        self.parent.add_item(StyleSelect(speaker["styles"], self.parent))
        self.parent.speaker_id = speaker["styles"][0]["id"]
        self.parent.update_buttons()
        await interaction.response.edit_message(view=self.parent)
        self.old_selected = selected

    def update(self):
        start = self.page * 25
        end = start + 25
        self.options = self.all_options[start:end]
        self.old_selected = None

    def has_prev(self):
        return self.page > 0

    def has_next(self):
        return 25 * (self.page + 1) < len(self.all_options)

    def prev(self):
        if not self.has_prev():
            raise Exception("No previous page")
        self.page -= 1
        self.update()

    def next(self):
        if not self.has_next():
            raise Exception("No next page")
        self.page += 1
        self.update()

    @property
    def old_selected(self):
        return self.old_selecteds[self.page]

    @old_selected.setter
    def old_selected(self, value):
        self.old_selecteds[self.page] = value


class Board(dui.View):
    def __init__(self, speakers: list[Speaker], speaker_id: int):
        super().__init__()
        # self.speakers = speakers
        self.speaker_id: int | None = speaker_id
        self.canceled = True
        self.speaker_select = SpeakerSelect(speakers, self)
        self.add_item(self.speaker_select)
        self.update_buttons()

    @dui.button(label="cancel", style=discord.ButtonStyle.red, row=2)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # self.canceled = True
        self.stop()
        # await interaction.response.edit_message(view=self)
        await interaction.message.delete()  # type: ignore

    @dui.button(label="←", style=discord.ButtonStyle.green, row=2)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.speaker_select.has_prev():
            self.speaker_select.prev()
        self.update_buttons()
        await interaction.response.edit_message(view=self)

    @dui.button(label="→", style=discord.ButtonStyle.green, row=2)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.speaker_select.has_next():
            self.speaker_select.next()

        self.update_buttons()
        await interaction.response.edit_message(view=self)

    @dui.button(label="決定", style=discord.ButtonStyle.green, row=2, disabled=True)
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="変更しました", view=None)
        self.canceled = False
        self.stop()

    def update_buttons(self):
        if self.speaker_id is None:
            self.submit.disabled = True
        else:
            self.submit.disabled = False

        if self.speaker_select.has_next():
            self.next.disabled = False
        else:
            self.next.disabled = True

        if self.speaker_select.has_prev():
            self.prev.disabled = False
        else:
            self.prev.disabled = True
