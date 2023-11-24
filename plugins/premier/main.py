import discord
from discord.ext import commands
from discord.ext import tasks
from datetime import time, datetime as dt
import pytz



class Premier(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_in.start()
        self.team = [306081415643004928,
                     265613905957486592,
                     316927311238660097,
                     457956796061974529,
                     480147211062083584,
                     385849697904099329]
    
    

    def timezone_to_utc(year: int=dt.now().year, month:int=1, day: int=1, hour: int=0, minute: int=0, second: int=0):
        hour_task_tz = dt(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        return hour_task_tz.astimezone(pytz.UTC)    
    
    
    @tasks.loop(time=[time(hour=timezone_to_utc(hour=16).time().hour)])
    async def check_in(self)->discord.Message:
        channel_id = 1146395373225648178
        channel = self.bot.get_channel(channel_id)

        if dt.now().weekday() in {5,6}:
            
            content = "".join(f"<@{user_id}>" for user_id in self.team)

            embed=discord.Embed(
                title="Check-in match Premier",
                description="Qui sera là ce soir ?",
                color=0x7E6A4F
            )

            check_in_msg = await channel.send(content, embed=embed)

            for emoji in ["✅","❌"]:
                await check_in_msg.add_reaction(emoji)
    
    
    @check_in.before_loop
    async def before_check_in(self)->None:
        await self.bot.wait_until_ready()
        
    
        
    
    
        



async def setup(bot: commands.Bot)->None:
    await bot.add_cog(Premier(bot))