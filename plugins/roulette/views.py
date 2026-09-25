import discord

from numpy import random as rd

from .models import Agent, Weapon, STARTERS
from .game import Game


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
                description = result,
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
        self.game = game
        self.liste_agents = liste_agents
        self.selected_agent = rerolled_agent
        
    
    async def reroll(self, user_id: int)->None:
        # Enlève l'agent refusé et ceux verrouillés pendant la soirée
        locked = self.game.locked.get(user_id, set())
        self.liste_agents = [agent for agent in self.liste_agents 
                             if agent != self.selected_agent 
                             and agent.nom not in locked]
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
        self.game.locked.get(user.id, set()).discard(self.selected_agent.nom)
        self.game.lineup[self.game.get_team(user)][user] = self.selected_agent
        await interaction.response.send_message(f"Ton nouvel agent est **{self.selected_agent.nom}**")
        await self.disable_all_buttons(interaction)

    
    
    @discord.ui.button(label="Non", emoji="👎", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button)->None:
        user = interaction.user
        try:
            if self.selected_agent.nom in STARTERS:
                self.game.lineup[self.game.get_team(user)][user] = self.selected_agent
                await interaction.response.send_message(content=f"Arrête de mentir sale mytho et prend {self.selected_agent.nom}")
                await self.disable_all_buttons(interaction)
            else:
                self.game.locked.setdefault(user.id, set()).add(self.selected_agent.nom)
                await self.reroll(user.id)
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
        self.shield = ['Aucun', 'Petit', 'Regen', 'Gros']
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
        self.shield = ['Aucun', 'Petit', 'Regen', 'Gros']
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
