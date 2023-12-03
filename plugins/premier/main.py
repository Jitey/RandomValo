import discord
from discord.ext import commands
from discord.ext import tasks

from pathlib import Path
import json
parent_folder = Path(__file__).resolve().parent

from dataclasses import dataclass
from datetime import time, datetime as dt
import pytz

from icecream import ic


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
        embed.set_footer(text="`.reload` en cas de problème")
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
    role_id = 1178001872901128232
    role = None
    team = [306081415643004928,
            265613905957486592,
            316927311238660097,
            457956796061974529,
            480147211062083584,
            385849697904099329
            ]
    
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
    
    
    @tasks.loop(time=[time(hour=timezone_to_utc(hour=17).time().hour)])
    async def check_in(self)->discord.Message:
        messages = self.load_json('message')
        channel_id = 691378116710498317
        channel = self.bot.get_channel(channel_id)

        if dt.now().weekday() in {3, 5,6}:
            embed=discord.Embed(
                title="Check-in match Premier",
                description="Qui sera là ce soir ?",
                color=0x7E6A4F
            )
            embed.set_footer(text="`.reload` en cas de problème")

            msg = await channel.send(f"{Premier.role.mention}", embed=embed, view=CheckInView())
            messages['last_message'] = msg.id
            self.write_json(messages,'message')
            await msg.add_reaction("🔄")
    
    
    @check_in.before_loop
    async def before_check_in(self)->None:
        for e in Premier.next_match.values():
                e.clear()
        await self.bot.wait_until_ready()
        serveur = self.bot.get_guild(691378116710498314)
        Premier.role = serveur.get_role(Premier.role_id)
        
    
    @commands.hybrid_command(name='reload')
    async def reload(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        finally:
            await self.reload_check_in(ctx.channel)
        
    
    @commands.Cog.listener(name='on_reaction_add')
    async def reload_reaction(self, reaction: discord.Reaction, user: discord.Member):
        if reaction.emoji == "🔄":
            await self.reload_check_in(reaction.message.channel)
        
    
    async def reload_check_in(self, channel: discord.TextChannel):
        if last_message_id := self.load_json('message')['last_message']:
            msg = await channel.fetch_message(last_message_id)
            await msg.edit(view=CheckInView())
    
    
    def load_json(self, file: str)->dict:
        with open(f"{parent_folder}/{file}.json", 'r') as f:
            return json.load(f)
    
    def write_json(self, data: dict, path: str)->None:
        with open(f"{parent_folder}/{path}.json", 'w') as f:
            json.dump(data, f, indent=2)
        
    
    
        



async def setup(bot: commands.Bot)->None:
    await bot.add_cog(PremierCog(bot))