import discord
from discord.ext import commands

from dataclasses import dataclass
from sqlite3 import *
from pathlib import Path
from os.path import join, sep

from numpy import random as rd, ndarray
from icecream import ic

import json


PARENT_FOLDER = Path(__file__).resolve().parent




#|-----------Dataclasses----------|
@dataclass
class Agent:
        nom: str
        role: str


@dataclass
class Weapon:
        nom: str
        type_arme: str
        
        
dict_classes_object = {
            'Agents': Agent,
            'Weapons': Weapon
            }



# |-----------Contient les données du jeu----------|
class Game:
    nb_joueurs = 0
    participants: list[list[discord.Member]] = [[] , []]
    lineup: list[dict[discord.Member, Agent]] = [{} , {}]
    color = [0x9ACD32 , 0xFF0000]
    author: discord.User = None


    def reset(self):
        """Réinitialise les données de la partie
        """
        for e in self.participants:
            e.clear()
        for e in self.lineup:
            e.clear()
    
    def get_team(self, user: discord.Member)->int|None:
        """Renvoie le numéro de l'équipe du joueur

        Args:
            user (discord.Member): Joueur

        Returns:
            int: Numéro de l'équipe
        """
        for i in range(len(self.participants)):
            if user in self.participants[i]:
                return i
    
    def user_in_team(self, user_id, equipe: list=[], index: int=0)->bool:
        """Renvoie si le joueur est dans l'équipe

        Args:
            user_id (_type_): _id du joueur
            equipe (list, optional): Equipe. Defaults to [].
            index (int, optional): Numéro de l'équipe. Defaults to 0.

        Returns:
            tuple[bool, discord.Member]: True si le joueur est dans l'équipe
        """
        if not equipe:
            equipe = self.participants[index]
            
        for user in equipe:
            if user.id == user_id:
                return True
            
        return False

    def ready(self):
        return len(self.participants[0]) + len(self.participants[1]) == self.nb_joueurs

    def __str__(self):
        return f"Game(nb_joueurs={self.nb_joueurs}, participants={self.participants}, lineup={self.lineup})"


    def __repr__(self):
        return f"Game(nb_joueurs={self.nb_joueurs}, participants={self.participants}, lineup={self.lineup})"





# |----------UI de la commande de start----------|
class StartView(discord.ui.View):
    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game
        
    @discord.ui.button(label="Premade", emoji="👥")
    async def premade_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(PremadeModal(self.game))
    
    @discord.ui.button(label="Custom", emoji="⚔️")
    async def custom_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CustomModal(self.game))
    


# |----------Mode premade----------|
class PremadeModal(discord.ui.Modal, title="Mode premade"):
    def __init__(self, game: Game, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game
        self.add_item(discord.ui.TextInput(
            label="max 5 joueurs",
            placeholder="Entrez le nombre de participants"
        ))
    
    async def on_submit(self, interaction: discord.Interaction)->None:
        self.game.nb_joueurs = int(self.nombre.value)
        self.game.reset()
        return await interaction.response.send_message(f"Réagir pour participer ({self.nombre.value} joueurs attendu)",view=PremadeView(self.game))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.nombre = self.children[0]
        return int(self.nombre.value) <= 5


class PremadeView(discord.ui.View):
    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game

        
    @discord.ui.button(label="Participer", style=discord.ButtonStyle.green)
    async def premade_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user not in self.game.participants[0]:
            self.game.participants[0].append(interaction.user)
            await interaction.response.send_message("Tu as été ajouté à l'équipe", ephemeral=True)
        else:
            self.game.participants[0].remove(interaction.user)
            await interaction.response.send_message("Tu as été retiré de l'équipe", ephemeral=True)
        
        if self.game.ready():
            button.disabled = True
            await interaction.message.edit(view=button.view)

            result = "".join(f"{participant.mention}\n" for participant in self.game.participants[0])
            embed=discord.Embed(
                title = "Participants enregistrés",
                description = result ,
                color = 0xAE02A1
            )
            await interaction.channel.send(embed=embed)




# |----------Mode custom----------|
class CustomModal(discord.ui.Modal, title="Mode custom"):
    def __init__(self, game: Game, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game
        self.add_item(discord.ui.TextInput(
            label="entre 2 et 10",
            placeholder="Entrez le nombre de participants"
        ))

    
    async def on_submit(self, interaction: discord.Interaction)->None:
        self.game.nb_joueurs = int(self.nombre.value)
        return await interaction.response.send_message(f"Veuillez réagir pour participer ({self.nombre.value} joueurs attendu)",view=CustomView(self.game))
        
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.nombre = self.children[0]
        return 2 <= int(self.nombre.value) <= 10
    
        
class CustomView(discord.ui.View):
    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game
        
        
    @discord.ui.button(label="Équipe 1", style=discord.ButtonStyle.green)
    async def first_team_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user not in self.game.participants[0]:
            self.game.participants[0].append(interaction.user)
            await interaction.response.send_message("Tu as été ajouté à l'équipe 1", ephemeral=True)
        else:
            self.game.participants[0].remove(interaction.user)
            await interaction.response.send_message("Tu as été retiré de l'équipe 1", ephemeral=True)
        
        if self.game.ready():
            await self.disable_all_buttons(interaction)
            
            for k in range(len(self.game.participants)):
                result = "".join(f"{participant.mention}\n" for participant in self.game.participants[k])

                embed=discord.Embed(
                    title = "Participants enregistrés",
                    description = f"Equipe {k+1} :\n{result}" ,
                    color = self.game.color[k] # Hex-coded color
                )
                await interaction.channel.send(embed=embed)
            
    
    
    @discord.ui.button(label="Équipe 2", style=discord.ButtonStyle.red)
    async def second_team_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user not in self.game.participants[1]:
            self.game.participants[1].append(interaction.user)
            await interaction.response.send_message("Tu as été ajouté à l'équipe 2", ephemeral=True)
        else:
            self.game.participants[1].remove(interaction.user)
            await interaction.response.send_message("Tu as été retiré de l'équipe 2", ephemeral=True)
        
        if self.game.ready():
            await self.disable_all_buttons(interaction)
            
            for k in range(len(self.game.participants)):
                result = "".join(f"{participant.mention}\n" for participant in self.game.participants[k])

                embed=discord.Embed(
                    title = "Participants enregistrés",
                    description = f"Equipe {k+1} :\n{result}" ,
                    color = self.game.color[k] # Hex-coded color
                )
                await interaction.channel.send(embed=embed)
                
                
        
    async def disable_all_buttons(self, interaction: discord.Interaction)->None:
        for child in self.children:
            if type(child) == discord.ui.Button:
                child.disabled = True
        
        await interaction.message.edit(view=self)





# |----------UI de la commande de reroll----------|
class RerollView(discord.ui.View):
    def __init__(self, game: Game,liste_agents: list[Agent], rerolled_agent: Agent) -> None:
        super().__init__()
        self.agents_de_base = {'Brimstone','Phoenix','Jett','Sova','Sage'}
        self.game = game
        self.liste_agents = liste_agents
        self.selected_agent = rerolled_agent
        
    
    async def reroll(self)->None:
        # Enlève l'agent de la liste des agent restant
        self.liste_agents.remove(self.selected_agent)
        # Si il reste des agents libre dans la liste
        if self.liste_agents:
            self.selected_agent = rd.choice(self.liste_agents)
        else:
            raise ValueError("Il n'y a plus assez d'agent")
        
    async def disable_all_buttons(self, interaction: discord.Interaction)->None:
        for child in self.children:
            if type(child) == discord.ui.Button:
                child.disabled = True
        
        return await interaction.message.edit(view=self)
        
        
    @discord.ui.button(label="Oui", emoji="👍", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        user = interaction.user
        self.game.lineup[self.game.get_team(user)][user] = self.selected_agent
        await interaction.response.send_message(f"Ton nouvel agent est **{self.selected_agent.nom}**")
        await self.disable_all_buttons(interaction)

    
    
    @discord.ui.button(label="Non", emoji="👎", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        user = interaction.user
        try:
            if self.selected_agent.nom in self.agents_de_base:
                self.game.lineup[self.game.get_team(user)][user] = self.selected_agent
                await interaction.response.send_message(content=f"Arrête de mentir sale mytho et prend {self.selected_agent.nom}")
                await self.disable_all_buttons(interaction)
            else:
                await self.reroll()
                await interaction.response.edit_message(content=f"{user.mention} as-tu {self.selected_agent.nom} ? (O/n)")
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
        self.petite_arme: int = 0
        self.start: int = 0
        self.end = len(weapons)
        self.weapons = weapons
        self.shield = ['Aucun', 'Petit', 'Rege', 'Gros']
        self.shield_proba = [1/10, 3/10, 3/10, 3/10]
        self.last_message = None

                
    async def roll_weapon(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        user = interaction.user
        if self.petite_arme==2:
            self.start = 5
        
        # Incrémentation de la variable petite_arme jusqu'à 2
        self.petite_arme = (self.petite_arme + 1) % 3
        rand_idx = rd.randint(self.start, self.end)
        
        embed=discord.Embed(
        title = button.label,
        description = f"Arme : **{self.weapons[rand_idx].nom}**\n\
                        Shield : **{rd.choice(self.shield, p=self.shield_proba)}**" ,
        color = 0xAE02A1
        )
        embed.set_author(name = user.display_name, icon_url = user.display_avatar)
        
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Normale", emoji="🪖")
    async def normale_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        self.start = 0
        self.end = len(self.weapons)
        self.shield = ['Aucun', 'Petit', 'Rege', 'Gros']
        self.shield_proba = [1/6, 1/6, 2/6, 2/6]
        
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







class RouletteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.mode_aleatoire = ""
        self.agents: list[Agent] = self.load_data_from_json('Agents')
        self.weapons: list[Weapon] = self.load_data_from_json('Weapons')
        self.games: dict[any, Game] = {}
    
        
        
    # |---------Commandes---------|
    @commands.hybrid_command(name="start", description="Lance une nouvelle partie")
    async def select_start(self, ctx: commands.Context)->discord.Message:
        """Lance une nouvelle partie

        Args:
            ctx (commands.Context): Contexte de la commande

        Returns:
            discord.Message: Choix du mode de jeu
        """
        game = self.games[ctx.guild.id] = Game()

        self.mode_aleatoire = ""
        embed=discord.Embed(
            title = "Choix du mode de jeu",
            color = 0xAE02A1
            )
        return await ctx.send(embed=embed, view=StartView(game))
        
    
    @commands.hybrid_command(name="agent", description="Attribut un agent aléatoirement à tout les joueurs")
    async def agent(self, ctx: commands.Context)->discord.Message:
        author = ctx.author
        try:
            game = self.games[ctx.guild.id]
        except KeyError as error:
            return await ctx.reply(f"Tu dois d'abord faire `/start` pour créer une partie", mention_author=False)

        self.mode_aleatoire = 'Full random'
        # N contient une liste des longueurs des équipes
        N = [len(team) for team in game.participants]
        vide = True
        try:
            # Répète autant de fois qu'il y a d'équipes
            for k in range(len(N)):
                # Si l'équipe n'est pas vide
                if N[k]:
                    vide = False
                    if N[k]==0:
                        raise ValueError("L'une des équipes est vide")

                    # Créer une liste de même longueur que l'équipe avec les agents
                    res: ndarray[Agent] = rd.choice(self.agents,size=N[k],replace=False)
                    result_msg = ""
                    # Créer un message avec la composition de l'équipe et ajoute les agents à la liste des agents de l'équipe
                    for i in range(N[k]):
                        result_msg += f"{game.participants[k][i].mention}: {res[i].nom}\n"
                        # Associe l'agent au joueur dans l'équipe
                        game.lineup[k][game.participants[k][i]] = res[i]    

                    embed = discord.Embed(
                        title="Composition de l'équipes",
                        description=result_msg,
                        color=game.color[k],
                    )

                    embed.set_author(name = author.display_name, icon_url = author.display_avatar)
                    await ctx.reply(embed=embed, mention_author=False)
            if vide:
                raise ValueError("Aucune équipe enregistré. Utilisez  la commande `start`")
        except ValueError as error:
            embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
            return await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(name="goodcomp", description="Comme `agent` mais utilise un agent de chaque rôle")
    async def goodcomp(self, ctx: commands.Context)->discord.Message:
        author = ctx.author
        try:
            game = self.games[ctx.guild.id]
        except KeyError as error:
            return await ctx.reply(f"Tu dois d'abord faire `/start` pour créer une partie", mention_author=False)


        self.mode_aleatoire = 'Goodcomp'
        # N contient une liste des longueurs des équipes
        N = [len(team) for team in game.participants]
        try:
            # Répète autant de fois qu'il y a d'équipes
            for k in range(len(N)):
                # Si l'équipe n'est pas vide
                if N[k]:
                    liste_role = [
                        'duelist',
                        'controller',
                        'initiator',
                        'sentinel'
                    ]

                    # Mélange l'ordre des rôles pour qu'ils soient attribué aléatoirement
                    rd.shuffle(liste_role)
                    # Copie la liste des agents pour ne pas modifier l'original
                    agents_tampon = self.agents.copy()
                
                    # Une équipe est complète si elle contient 5 joueurs
                    full = (N[k] == 5)
                    if full:
                        # On s'occupe des 4 premiers joueurs pour avoir un joueur par rôle
                        N[k] -= 1

                    if N[k]==0:
                        raise ValueError("L'une des équipes est vide. Commencez par faire `.start`")

                    result = ""
                    # Créer un message avec la composition de l'équipe et ajoute les agents à la liste des agents de l'équipe
                    for i in range(N[k]):
                        agent = self.pick_agent(liste_role[i])
                        # Enlève l'agent de la liste tampon
                        agents_tampon.remove(agent)   
                        result += f"{game.participants[k][i].mention}: {agent.nom}\n"
                        # Associe l'agent au joueur dans l'équipe
                        game.lineup[k][game.participants[k][i]] = agent

                    if full:
                        # Selection de l'agent du dernier joueur parmis ceux restant, il peut avoir n'importe quel rôle
                        res = rd.choice(agents_tampon)
                        result += f"{game.participants[k][-1].mention}: {res.nom}\n"
                        game.lineup[-1][game.participants[k][-1]] = res

                    embed = discord.Embed(
                        title="Composition de l'équipe",
                        description=result,
                        color=game.color[k],
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
        game = self.games[ctx.guild.id]
        
        try:
            if not game.lineup[0] and not game.lineup[1]:
                raise ValueError("Il faut d'abord générer une compo avec les commandes `agent` ou `goodcomp`")
            
            team = game.get_team(user)
            if team is not None:
                current_lineup = game.lineup[team]
                if current_lineup[user].nom in {'Brimstone','Phoenix','Jett','Sova','Sage'}:
                    return await ctx.reply(f"Mon reuf t'es obligé d'avoir {current_lineup[user].nom}")
            else:
                raise PermissionError("Tu doit être dans une équipe pour faire cette commande. Commence par en créer une avec la fonction `start`")

            match self.mode_aleatoire:
                case 'Full random':
                    # Copie la liste des agents
                    liste_agents = self.agents.copy()
                case 'Goodcomp':
                    # Copie la liste des agents ayant le même rôle
                    liste_agents = self.agents_by_role(current_lineup[user].role)
            
            for agent in current_lineup.values():
                if agent in liste_agents:
                    liste_agents.remove(agent)

            rerolled_agent: Agent = rd.choice(liste_agents)
            return await ctx.send(f"{user.mention} as-tu {rerolled_agent.nom} ? (O/n)", view=RerollView(game, liste_agents, rerolled_agent))

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
        """Choisit aléatoirement le spike carrier

        Args:
            ctx (commands.Context): Context

        Returns:
            discord.Message: Message
        """
        try:
            game = self.games[ctx.guild.id]
            team = game.get_team(ctx.author)
            return await ctx.reply(f"Spike carrier : {rd.choice(game.participants[team]).mention}")
        
        except KeyError as error:
            embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description="Tu dois d'abord créer l'équipe avec la commande `start`",
                    )
            return await ctx.reply(embed=embed, mention_author=False)




    # |------------Annexes------------|
    def agents_by_role(self, role: str)->list[Agent]:
        """Retourne la liste des agents ayant le rôle donné

        Args:
            role (str): Rôle de l'agent

        Returns:
            list[Agent]: Liste des agents ayant le rôle donné
        """
        return [agent for agent in self.agents if agent.role==role]

    def pick_agent(self, role: str)->Agent:
        """Choisit un agent aléatoirement parmis les agents ayant ce rôle

        Args:
            role (str): Rôle de l'agent

        Returns:
            Agent: Agent choisi aléatoirement
        """
        return rd.choice(self.agents_by_role(role))

    def load_data_from_sql(self, object:str)->list[Agent|Weapon]:
        with connect(f"{PARENT_FOLDER}/valorant.sqlite") as connection:
            curseur = connection.cursor()
            
            curseur.execute(f"SELECT nom , classe FROM {object}")
            classe_object = dict_classes_object[object]
            
        return [classe_object(*args) for args in curseur.fetchall()]

    def load_data_from_json(self, object: str)->list[Agent|Weapon]:
        with open(join(PARENT_FOLDER, "valorant.json")) as file:
            json_data = json.load(file)[object]
            
            classe_object = dict_classes_object[object]
            
        return [classe_object(*args) for args in json_data]

    async def send_error(self, ctx: commands.Context, error: Error)->discord.Message:
        embed = discord.Embed(
                        title=f"{type(error).__name__}",
                        description=error,
                    )
        return await ctx.reply(embed=embed, mention_author=False)

   


async def setup(bot: commands.Bot)->None:
    await bot.add_cog(RouletteCog(bot))