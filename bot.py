# Daki paid ID 557

# |----------Module d'environnement-----------|
from os import getenv, sep
from os.path import join
from dotenv import load_dotenv
from pathlib import Path
import glob
# |----------Module du projet-----------|
import discord
from discord.ext import commands

import logging



class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[92m",  # Vert
        "INFO": "\033[94m",   # Bleu
        "WARNING": "\033[93m",  # Jaune
        "ERROR": "\033[91m",  # Rouge
        "CRITICAL": "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

# Appliquez le gestionnaire personnalisé
formatter = ColoredFormatter(
    fmt='\033[90m\033[1m%(asctime)s\033[0m %(levelname)s   %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)





PARENT_FOLDER = Path(__file__).resolve().parent
load_dotenv(dotenv_path=f"{PARENT_FOLDER}/.env")

PREFIX = ','
IGNORED_EXTENSIONS = []



        

class RandomValo(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
        self.IGNORED_EXTENSIONS = IGNORED_EXTENSIONS
        self.ROOT = PARENT_FOLDER
    
    
    async def setup_hook(self) -> None:
        await self.load_all_extensions()
        synced = await self.tree.sync()
        print(f"{len(synced)} commandes synchroisées")

    
    async def on_ready(self) -> None:
        activity = discord.Game(name="VALORANT")
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        print(f'Connecté en tant que {self.user.name}')


    async def load_all_extensions(self) -> None:
        for plugin in glob.glob(join(PARENT_FOLDER, "plugins", "**")):
            extention = plugin.split(sep)[-1]
            if extention not in self.IGNORED_EXTENSIONS:
                try:
                    await bot.load_extension(f"plugins.{extention}.main")
                    logging.info(f"Extension {extention} chargée")
                except Exception as error:
                    logging.error(f"Un problème est survenu lors du chargement de l'extension {extention}\n{error}")


if __name__=='__main__':
    bot = RandomValo()
    bot.run(getenv("BOT_TOKEN"))