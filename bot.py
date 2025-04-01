# Daki paid ID 557

# |----------Module d'environnement-----------|
from os import getenv
from os.path import join
from dotenv import load_dotenv
from pathlib import Path
import glob
# |----------Module du projet-----------|
import discord
from discord.ext import commands

import logging

logging.basicConfig(
    level=logging.INFO,  # Niveau de logging
    format='\033[1m%(asctime)s\033[0m  [\033[1m%(levelname)s\033[0m]  %(message)s',  # Format du message
    datefmt='%Y-%m-%d %H:%M:%S'  # Format de la date et heure
)

parent_folder = Path(__file__).resolve().parent
load_dotenv(dotenv_path=f"{parent_folder}/.env")

PREFIX = ','
IGNORE_EXTENSIONS = ['premier']


async def load_all_extensions(bot: commands.Bot):
    for plugin in glob.glob(join(parent_folder, "plugins", "**")):
        extention = plugin.split('/')[-1]
        if extention not in IGNORE_EXTENSIONS:
            try:
                await bot.load_extension(f"plugins.{extention}.main")
                logging.info(f"Extension {extention} chargée")
            except Exception as error:
                logging.error(f"Un problème est survenu lors du chargement de l'extension {extention}\n{error}")
        


class RandomValo(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
    
    
    async def setup_hook(self) -> None:
        await load_all_extensions(self)
        synced = await self.tree.sync()
        print(f"{len(synced)} commandes synchroisées")

    
    async def on_ready(self) -> None:
        activity = discord.Game(name="VALORANT")
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        print(f'Connecté en tant que {self.user.name}')




if __name__=='__main__':
    bot = RandomValo()
    bot.run(getenv("BOT_TOKEN"))