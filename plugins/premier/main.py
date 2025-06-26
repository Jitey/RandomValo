import discord
from discord.ext import commands
from discord.ext import tasks

import json
from os.path import join
from pathlib import Path

from dataclasses import dataclass
from datetime import time, datetime as dt
import pytz
from zoneinfo import ZoneInfo

from icecream import ic


# |----------UI du check_in----------|
class CheckInView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    
    
    async def update_check_in(self, interaction: discord.Interaction)->None:
        joueurs_presents = "".join(f"{joueur.mention}\n" for joueur in Premier.next_match['present'])
        joueurs_absents = "".join(f"{joueur.mention}\n" for joueur in Premier.next_match['absent'])

        embed=discord.Embed(
            title="Check-in match Premier",
            description="Qui sera là ce soir ?",
            color=0x7E6A4F
        )
        
        embed.add_field(name='Présents', value=joueurs_presents, inline=True)
        embed.add_field(name='Absents', value=joueurs_absents, inline=True)
        await interaction.response.edit_message(embed=embed)

    
    
    @discord.ui.button(label="Présent", style=discord.ButtonStyle.green, custom_id='present_button')
    async def prensent(self, interaction: discord.Interaction, button: discord.Button)->None:
        user = interaction.user
        if user in Premier.next_match['absent']:
            Premier.next_match['absent'].remove(user)
        
        if user in Premier.next_match['present']:
            Premier.next_match['present'].remove(user)
        else:
            Premier.next_match['present'].append(interaction.user)
        
        await self.update_check_in(interaction)
    

    @discord.ui.button(label="Pas dispo", style=discord.ButtonStyle.red, custom_id='absent_button')
    async def non_prensent(self, interaction: discord.Interaction, button: discord.Button)->None:
        user = interaction.user
        if user in Premier.next_match['present']:
            Premier.next_match['present'].remove(user)
        
        if user in Premier.next_match['absent']:
            Premier.next_match['absent'].remove(user)
        else:
            Premier.next_match['absent'].append(interaction.user)

        await self.update_check_in(interaction)




@dataclass
class Premier:
    role_id = 1368596485771497543
    role = None
    team = [306081415643004928,
            265613905957486592,
            316927311238660097,
            457956796061974529,
            480147211062083584,
            532943399678902282
            ]
    
    next_match = {'present': [], 
                  'absent': []
                  }
    
    @classmethod
    def reset(clc)->None:
        clc.next_match['present'].clear()
        clc.next_match['absent'].clear()






ROOT = Path(__file__).resolve().parent


class PremierCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.data = self.load_json("data_premier")
        self.check_in.start()
    

    
    @tasks.loop(time=time(hour=17, tzinfo=ZoneInfo("Europe/Paris")))
    async def check_in(self)->discord.Message:
        channel_id = 691378116710498317
        channel = self.bot.get_channel(channel_id)

        for server in self.data:
            if not self.data[server]['check_in']:
                return
            
            if dt.now().weekday() in {3,5,6}:
                Premier.reset()
                embed=discord.Embed(
                    title="Check-in match Premier",
                    description="Qui sera là ce soir ?",
                    color=0x7E6A4F
                )

                await channel.send(f"{Premier.role.mention}", embed=embed, view=CheckInView())
    
    
    @check_in.before_loop
    async def before_check_in(self)->None:
        for e in Premier.next_match.values():
                e.clear()
        await self.bot.wait_until_ready()
        serveur = self.bot.get_guild(691378116710498314)
        Premier.role = serveur.get_role(Premier.role_id)
        
    
    @commands.hybrid_command(name="switch", description="Activate or deactivate the check-in for the Premier matches.")
    async def switch_check_in(self, ctx: commands.Context) -> None:
        """Switch the check-in on or off."""
        self.data[ctx.guild.name]['check_in'] ^= True
        self.update_logs(self.data, "data_premier")
    
    
    def load_json(self, file: str)->dict:
        """"Récupère les données du fichier json

        Args:
            file (str): Nom du fichier

        Returns:
            dict: Données enregistrées
        """
        with open(join(ROOT,f"{file}.json"), 'r') as f:
            return json.load(f)

    def update_logs(self, data: dict, file: str)->None:
        """Enregistre le fichier logs

        Args:
            data (dict): Données à enregistrer
            path (str): Chemin du fichier à enregistrer
        """
        with open(join(ROOT,f"{file}.json"), 'w') as f:
            json.dump(data,f,indent=2) 
        



async def setup(bot: commands.Bot)->None:
    await bot.add_cog(PremierCog(bot))
    bot.add_view(CheckInView())