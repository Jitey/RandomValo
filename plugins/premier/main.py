import discord
from discord.ext import commands
from discord.ext import tasks

from dataclasses import dataclass
from datetime import time, datetime as dt
import pytz


# |----------UI du check_in----------|
class CheckInView(discord.ui.View):
    def __init__(self):
        super().__init__()
    
    
    
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

    
    
    @discord.ui.button(label="Présent", style=discord.ButtonStyle.green)
    async def prensent(self, interaction: discord.Interaction, button: discord.Button)->None:
        user = interaction.user
        Premier.next_match['present'].append(interaction.user)
        if user in Premier.next_match['absent']:
            Premier.next_match['absent'].remove(user)
        await self.update_check_in(interaction)
    

    @discord.ui.button(label="Pas dispo", style=discord.ButtonStyle.red)
    async def non_prensent(self, interaction: discord.Interaction, button: discord.Button)->None:
        user = interaction.user
        Premier.next_match['absent'].append(interaction.user)
        if user in Premier.next_match['present']:
            Premier.next_match['present'].remove(user)
        await self.update_check_in(interaction)




@dataclass
class Premier:
    # team = [306081415643004928,
    #         265613905957486592,
    #         316927311238660097,
    #         457956796061974529,
    #         480147211062083584,
    #         385849697904099329
    #         ]
    team = [306081415643004928]
    
    next_match = {'present': [], 
                  'absent': []
                  }



class PremierCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_in.start()
        
    
    

    def timezone_to_utc(year: int=dt.now().year, month:int=1, day: int=1, hour: int=0, minute: int=0, second: int=0):
        hour_task_tz = dt(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        return hour_task_tz.astimezone(pytz.UTC)    
    
    
    @tasks.loop(time=[time(hour=timezone_to_utc(hour=16).time().hour)])
    async def check_in(self)->discord.Message:
        channel_id = 1146395373225648178
        channel = self.bot.get_channel(channel_id)

        if dt.now().weekday() in {3, 4, 5,6}:
            content = "".join(f"<@{user_id}>" for user_id in Premier.team)

            embed=discord.Embed(
                title="Check-in match Premier",
                description="Qui sera là ce soir ?",
                color=0x7E6A4F
            )

            await channel.send(content, embed=embed, view=CheckInView())
    
    
    @check_in.before_loop
    async def before_check_in(self)->None:
        for e in Premier.next_match.values():
                e.clear()
        await self.bot.wait_until_ready()
        
    
        
    
    
        



async def setup(bot: commands.Bot)->None:
    await bot.add_cog(PremierCog(bot))