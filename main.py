# |----------Module d'environnement-----------|
from os import getenv
from dotenv import load_dotenv
from pathlib import Path
import glob
# |----------Module du projet-----------|
import discord
from discord.ext import commands


parent_folder = Path(__file__).resolve().parent
load_dotenv(dotenv_path=f"{parent_folder}/.env")

PREFIX = '.'
IGNORE_EXTENSIONS = ['premier']


async def load_all_extensions(bot: commands.Bot):
    for plugin in glob.glob(f"{parent_folder}/plugins/**"):
        extention = plugin.split('/')[-1]
        if extention not in IGNORE_EXTENSIONS:
            await bot.load_extension(f"plugins.{extention}.main")
        


class RandomValo(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
    
    
    async def setup_hook(self) -> None:
        await load_all_extensions(self)
        synced = await self.tree.sync()
        print(f"{len(synced)} commandes synchroisées")

    
    async def on_ready(self) -> None:
        activity = discord.Game(name="VALORANT")
        await self.change_presence(status=discord.Status.offline, activity=activity)
        
        print(f'Connecté en tant que {self.user.name}')




if __name__=='__main__':
    bot = RandomValo()
    bot.run(getenv("BOT_TOKEN"))