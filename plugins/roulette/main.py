import discord
from discord.ext import commands

from dataclasses import dataclass
from sqlite3 import *
from pathlib import Path

from numpy import random as rd

parent_folder = Path(__file__).resolve().parent




#|-----------Dataclasses----------|
@dataclass
class Agent:
        nom: str
        role: str


@dataclass
class Weapon:
        nom: str
        type_arme: str



# |----------UI de la commande de start----------|
class StartView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        
    @discord.ui.button(label="Premade", emoji="👥")
    async def premade_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        Game.reset()
        await interaction.response.send_modal(PremadeModal())
    
    
    @discord.ui.button(label="Custom", emoji="⚔️")
    async def custom_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        Game.reset()
        await interaction.response.send_modal(CustomModal())
    


# |----------Mode premade----------|
class PremadeModal(discord.ui.Modal, title="Mode premade"):
    nombre = discord.ui.TextInput(
        label="max 5 joueurs",
        placeholder="Entrez le nombre de participants"
    )
    
    async def on_submit(self, interaction: discord.Interaction)->None:
        Game.nb_joueurs = int(self.nombre.value)
        return await interaction.response.send_message(f"Réagir pour participer ({Game.nb_joueurs} joueurs attendu)",view=PremadeView())
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return int(self.nombre.value) <= 5


class PremadeView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()

        
    @discord.ui.button(label="Participer", style=discord.ButtonStyle.green)
    async def premade_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user not in Game.participants[0]:
            Game.participants[0].append(interaction.user)
            await interaction.response.send_message("Tu as été ajouté à l'équipe", ephemeral=True)
        else:
            Game.participants[0].remove(interaction.user)
            await interaction.response.send_message("Tu as été retiré de l'équipe", ephemeral=True)
        
        if len(Game.participants[0]) == Game.nb_joueurs:
            button.disabled = True
            await interaction.message.edit(view=button.view)

            result = "".join(f"{participant.mention}\n" for participant in Game.participants[0])
            embed=discord.Embed(
                title = "Participants enregistrés",
                description = result ,
                color = 0xAE02A1
            )
            await interaction.channel.send(embed=embed)




# |----------Mode custom----------|
class CustomModal(discord.ui.Modal, title="Mode custom"):
    nombre = discord.ui.TextInput(
        label="entre 2 et 10",
        placeholder="Entrez le nombre de participants"
    )
    
    async def on_submit(self, interaction: discord.Interaction)->None:
        Game.nb_joueurs = int(self.nombre.value)
        return await interaction.response.send_message(f"Veuillez réagir pour participer ({Game.nb_joueurs} joueurs attendu)",view=CustomView())
        
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return 2 <= int(self.nombre.value) <= 10
    
        
class CustomView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        
        
    @discord.ui.button(label="Équipe 1", style=discord.ButtonStyle.green)
    async def first_team_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user not in Game.participants[0]:
            Game.participants[0].append(interaction.user)
            await interaction.response.send_message("Tu as été ajouté à l'équipe 1", ephemeral=True)
        else:
            Game.participants[0].remove(interaction.user)
            await interaction.response.send_message("Tu as été retiré de l'équipe 1", ephemeral=True)
        
        if len(Game.participants[0]) + len(Game.participants[1]) == Game.nb_joueurs:
            await self.disable_all_buttons(interaction)
            
            for k in range(len(Game.participants)):
                result = "".join(f"{participant.mention}\n" for participant in Game.participants[k])

                embed=discord.Embed(
                    title = "Participants enregistrés",
                    description = f"Equipe {k+1} :\n{result}" ,
                    color = Game.color[k] # Hex-coded color
                )
                await interaction.channel.send(embed=embed)
            
    
    
    @discord.ui.button(label="Équipe 2", style=discord.ButtonStyle.red)
    async def second_team_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user not in Game.participants[1]:
            Game.participants[1].append(interaction.user)
            await interaction.response.send_message("Tu as été ajouté à l'équipe 2", ephemeral=True)
        else:
            Game.participants[1].remove(interaction.user)
            await interaction.response.send_message("Tu as été retiré de l'équipe 2", ephemeral=True)
        
        if len(Game.participants[0]) + len(Game.participants[1]) == Game.nb_joueurs:
            await self.disable_all_buttons(interaction)
            
            for k in range(len(Game.participants)):
                result = "".join(f"{participant.mention}\n" for participant in Game.participants[k])

                embed=discord.Embed(
                    title = "Participants enregistrés",
                    description = f"Equipe {k+1} :\n{result}" ,
                    color = Game.color[k] # Hex-coded color
                )
                await interaction.channel.send(embed=embed)
                
                
        
    async def disable_all_buttons(self, interaction: discord.Interaction)->None:
        for child in self.children:
            if type(child) == discord.ui.Button:
                child.disabled = True
        
        await interaction.message.edit(view=self)





# |----------UI de la commande de reroll----------|
class RerollView(discord.ui.View):
    def __init__(self, liste_agents: list, res: Agent) -> None:
        super().__init__()
        self.agents_de_base = {'Brimstone','Phoenix','Jett','Sova','Sage'}
        self.liste_agents = liste_agents
        self.res = res
        
    
    async def reroll(self)->None:
        self.liste_agents.remove(self.res)
        if self.liste_agents:
            self.res = rd.choice(self.liste_agents)
        else:
            raise ValueError("Il n'y a plus assez d'agent")
        
    async def disable_all_buttons(self, interaction: discord.Interaction)->None:
        for child in self.children:
            if type(child) == discord.ui.Button:
                child.disabled = True
        
        await interaction.message.edit(view=self)
        
        
    @discord.ui.button(label="Oui", emoji="👍", style=discord.ButtonStyle.green)
    async def premade_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        user = interaction.user
        Game.lineup[Game.get_team(user)][user] = self.res
        await interaction.response.send_message(f"Ton nouvel agent est **{self.res.nom}**")
        await self.disable_all_buttons(interaction)

    
    
    @discord.ui.button(label="Non", emoji="👎", style=discord.ButtonStyle.red)
    async def custom_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        user = interaction.user
        try:
            if self.res.nom in self.agents_de_base:
                Game.lineup[Game.get_team(user)][user] = self.res
                await interaction.response.send_message(content=f"Arrête de mentir sale mytho et prend {self.res.nom}")
                await self.disable_all_buttons(interaction)
            else:
                await self.reroll()
                await interaction.response.edit_message(content=f"{user.mention} as-tu {self.res.nom} ? (O/n)")
        except ValueError as error:
            embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
            await interaction.response.send_message(embed=embed, ephemeral=True)



# |----------UI de la commande de weapon----------|
class WeaponView(discord.ui.View):
    def __init__(self, weapons: list[Weapon]) -> None:
        super().__init__(timeout=None)
        self.petite_arme = 0
        self.start = 0
        self.end = len(weapons)
        self.weapons = weapons
        self.shield = ['Aucun','Petit','Gros']
        self.shield_proba = [1/10,4.5/10,4.5/10]
        self.last_message = None

                
    async def roll_weapon(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        user = interaction.user
        if self.petite_arme==2:
            self.start = 5
        self.petite_arme = (self.petite_arme + 1)%3
        
        embed=discord.Embed(
        title = button.label,
        description = f"Arme : **{self.weapons[rd.randint(self.start,self.end)].nom}**\n\
                        Shield : **{rd.choice(self.shield)}**" ,
        color = 0xAE02A1
        )
        embed.set_author(name = user.display_name, icon_url = user.display_avatar)
        
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Normale", emoji="🪖")
    async def normale_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        self.start = 0
        self.end = len(self.weapons)
        self.shield = ['Aucun','Petit','Gros']
        self.shield_proba = [1/5,2/5,2/5]
        await self.roll_weapon(interaction, button)
    
    
    @discord.ui.button(label="Gun round", emoji="🔫")
    async def gun_round_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        self.start = 0
        self.end = 5
        self.petite_arme = 1
        self.shield = ['Aucun']
        self.shield_proba = [1]
        await self.roll_weapon(interaction, button)
    
    
    @discord.ui.button(label="Petit round", emoji="🐥")
    async def petit_round_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        self.start = 0
        self.end = 10
        self.shield = ['Aucun','Petit']
        self.shield_proba = [1/3,2/3]
        await self.roll_weapon(interaction, button)





# |-----------Contient les données du jeu----------|
class Game:     
    nb_joueurs = 0
    participants = [[] , []]
    lineup = [{} , {}]
    color = [0x9ACD32 , 0xFF0000]


    @classmethod
    def reset(cls):
        for e in cls.participants:
            e.clear()
        for e in cls.lineup:
            e.clear()
    
    @classmethod
    def get_team(cls, user: discord.Member)->int:
        for i in range(len(cls.participants)):
            if user in cls.participants[i]:
                return i
    
    @classmethod
    def user_in_team(cls, user_id, equipe: list=[], index: int=0)->tuple[bool, discord.Member]:
        if not equipe:
            equipe = cls.participants[index]
            
        for user in equipe:
            return user if user.id == user_id else None





class RouletteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.mode_aleatoire = ""
        self.agents = self.load_data('Agents')
        self.weapons = self.load_data('Weapons')
    
        
        
    # |---------Commandes---------|
    @commands.hybrid_command(name="start", description="Lance une nouvelle partie")
    async def select_start(self, ctx: commands.Context)->discord.Message:
        self.mode_aleatoire = ""
        embed=discord.Embed(
            title = "Choix du mode de jeu",
            color = 0xAE02A1
            )
        return await ctx.send(embed=embed, view=StartView())
        
    
    @commands.hybrid_command(name="agent", description="Attribut un agent aléatoirement à tout les joueurs")
    async def agent(self, ctx: commands.Context)->discord.Message:
        self.mode_aleatoire = 'Full random'

        N = [len(e) for e in Game.participants]
        vide = True
        try:
            for k in range(len(N)):
                if N[k]:
                    vide = False
                    result = ""
                    if N[k]==0:
                        raise ValueError("L'une des équipes est vide")

                    res = rd.choice(self.agents,size=N[k],replace=False)
                    for i in range(N[k]):
                        result += f"{Game.participants[k][i].mention}: {res[i].nom}\n"
                        Game.lineup[k][Game.participants[k][i]] = res[i]    

                    embed = discord.Embed(
                        title="Composition de l'équipes",
                        description=result,
                        color=Game.color[k],
                    )

                    author = ctx.message.author
                    embed.set_author(name = author.display_name, icon_url = author.display_avatar)
                    await ctx.reply(embed=embed, mention_author=False)
            if vide:
                raise ValueError("Aucune équipe enregistré. Utilisez  la commande `start`")
        except ValueError as error:
            embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
            await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(name="goodcomp", description="Comme `agent` mais utilise un agent de chaque rôle")
    async def goodcomp(self, ctx: commands.Context)->discord.Message:
        self.mode_aleatoire = 'Goodcomp'

        liste_role = ['duelist',
                        'controller',
                        'initiator',
                        'sentinel']

        rd.shuffle(liste_role)

        N = [len(e) for e in Game.participants]
        try:
            for k in range(len(N)):
                if N[k]:
                    agent_tampon = self.agents.copy()
                    full = N[k]==5
                    if full:
                        N[k] -= 1
                    if N[k]==0:
                        raise ValueError("L'une des équipes est vide. Commencez par faire `.start`")

                    result = ""
                    for i in range(N[k]):
                        res = self.pick_agent(liste_role[i])
                        agent_tampon.remove(res)   
                        result += f"{Game.participants[k][i].mention}: {res.nom}\n"
                        Game.lineup[k][Game.participants[k][i]] = res

                    if full:
                        res = rd.choice(agent_tampon)
                        result += f"{Game.participants[-1][i].mention}: {res.nom}\n"
                        Game.lineup[-1][Game.participants[-1][i]] = res

                    embed = discord.Embed(
                        title="Composition de l'équipe",
                        description=result,
                        color=Game.color[k],
                    )
                    author = ctx.message.author
                    embed.set_author(name = author.display_name, icon_url = author.display_avatar)

                    await ctx.reply(embed=embed, mention_author=False)
        except (ValueError, IndexError) as error:
            embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
            await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(name="reroll", description="Choisit un nouvel agent. À utiliser uniquement si l'agent choisit par .agent n'est pas possedé")
    async def reroll(self, ctx: commands.Context)->discord.Message:
        user = ctx.author
        try:
            if not Game.lineup[0]:
                raise ValueError("Il faut d'abord générer une compo avec les commandes `agent` ou `goodcomp`")
            
            team = Game.get_team(user)
            if team is not None:
                current_lineup = Game.lineup[team]
                if current_lineup[user].nom in {'Brimstone','Phoenix','Jett','Sova','Sage'}:
                    return await ctx.reply(f"Mon reuf t'es obligé d'avoir {current_lineup[user].nom}")
            else:
                raise PermissionError("Tu doit être dans une équipe pour faire cette commande. Tu peu le faire avec la fonction `start`")

            if self.mode_aleatoire == 'Full random':
                liste_agents = self.agents.copy()
            elif self.mode_aleatoire == 'Goodcomp':
                liste_agents = self.agents_by_role(current_lineup[user].role)
            
            current_agent = current_lineup[user]
            if current_agent in liste_agents:
                liste_agents.remove(current_agent)

            res = rd.choice(liste_agents)
            return await ctx.send(f"{user.mention} as-tu {res.nom} ? (O/n)", view=RerollView(liste_agents, res))

        except (ValueError, PermissionError) as error:
            await self.send_error(ctx, error)


    @commands.hybrid_command(name="weapon", description="Ouvre un menu pour choisir les armes aléatoirement")
    async def weapon(self, ctx: commands.Context)->discord.Message:
        embed=discord.Embed(
            title = "Choix du type de round",
            color = 0xAE02A1
            )
        return await ctx.send(embed=embed, view=WeaponView(self.weapons))


    @commands.hybrid_command(name='spike', description="Désigne le spike carier")
    async def spike(self, ctx: commands.Context)->discord.Message:
        return await ctx.reply(f"Spike carrier : {rd.choice(Game.participants[Game.get_team(ctx.author)]).mention}")
        # channel = self.bot.get_channel(691378116710498317)
        # return await channel.send("Il est au taquet le p'tit smokyz")




    # |------------Annexes------------|
    def load_data(self, object:str)->list[Agent|Weapon]:
        dict_classes_object = {
            'Agents': Agent,
            'Weapons': Weapon
            }

        with connect(f"{parent_folder}/valorant.sqlite") as connection:
            curseur = connection.cursor()
            
            curseur.execute(f"SELECT nom , classe FROM {object}")
            classe_object = dict_classes_object[object]
        return [classe_object(nom,classe) for nom, classe in curseur.fetchall()]

    async def send_error(self, ctx: commands.Context, error: Error)->discord.Message:
        embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
        return await ctx.reply(embed=embed, mention_author=False)

    def agents_by_role(self, role: str)->list[Agent]:
        return [agent for agent in self.agents if agent.role==role]

    def pick_agent(self, role: str)->Agent:
        return rd.choice(self.agents_by_role(role))




async def setup(bot: commands.Bot)->None:
    await bot.add_cog(RouletteCog(bot))