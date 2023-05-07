import logging
import os

import discord
from dotenv import load_dotenv

from iot_bot import IotBot

load_dotenv()
intents = discord.Intents.all()
intents.typing = False
bot = IotBot(command_prefix="!", intents=intents)
bot.run(os.environ["TOKEN"], log_level=logging.INFO, root_logger=True)
