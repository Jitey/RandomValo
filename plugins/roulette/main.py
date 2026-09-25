import discord
from discord.ext import commands

from sqlite3 import *
from pathlib import Path
from typing import Callable

from numpy import random as rd

import json
import urllib.request

from .models import Agent, Weapon, dict_classes_object, STARTERS
from .game import Game
from .views import StartView, RerollView, WeaponView


PARENT_FOLDER = Path(__file__).resolve().parent


class RouletteCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
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

        game.mode_aleatoire = ""
        embed=discord.Embed(
            title = "Choix du mode de jeu",
            color = 0xAE02A1
            )
        return await ctx.send(embed=embed, view=StartView(game))
        
    
    @commands.hybrid_command(name="agent", description="Attribut un agent aléatoirement à tout les joueurs")
    async def agent(self, ctx: commands.Context)->discord.Message:
        return await self._run_compo(ctx, self._pick_full_random, 'Full random')


    @commands.hybrid_command(name="goodcomp", description="Comme `agent` mais utilise un agent de chaque rôle")
    async def goodcomp(self, ctx: commands.Context)->discord.Message:
        return await self._run_compo(ctx, self._pick_goodcomp, 'Goodcomp')

    async def _run_compo(self, ctx: commands.Context, pick: Callable, mode: str)->discord.Message:
        """Fonction commune pour initialiser la composition des équipes

        Args:
            ctx (commands.Context): Contexte de la commande
            pick (Callable): Fonction de pick d'agent

        Returns:
            discord.Message: Message avec la composition des équipes
        """
        game = await self._get_game(ctx)
        if game is None:
            return
        N = [len(team) for team in game.participants]
        try:
            self._validate_teams(N)
            game.mode_aleatoire = mode
            for k, n in enumerate(N):
                picks = pick(n)
                self._assign_team(game, k, picks)
                await self._reply_team(ctx, game, k, [f"{p.mention}: {a.nom}" for p, a in zip(game.participants[k], picks)])
        except (ValueError, IndexError) as error:
            return await self.send_error(ctx, error)


    @commands.hybrid_command(name="reroll", description="Choisit un nouvel agent. À utiliser uniquement si l'agent choisit par .agent n'est pas possedé")
    async def reroll(self, ctx: commands.Context)->discord.Message:
        user = ctx.author
        game = await self._get_game(ctx)
        if game is None:
            return
        try:
            if not game.lineup[0] and not game.lineup[1]:
                raise ValueError("Il faut d'abord générer une compo avec les commandes `agent` ou `goodcomp`")
            
            team = game.get_team(user)
            if team is None:
                raise PermissionError("Tu doit être dans une équipe pour faire cette commande. Commence par en créer une avec la fonction `start`")
            
            current_lineup = game.lineup[team]
            if current_lineup[user].nom in STARTERS:
                return await ctx.reply(f"Mon reuf t'es obligé d'avoir {current_lineup[user].nom}")
            
            liste_agents = self._pool_reroll(game, current_lineup, user)
            rerolled_agent: Agent = rd.choice(liste_agents)
            return await ctx.send(f"{user.mention} as-tu {rerolled_agent.nom} ? (O/n)", view=RerollView(game, liste_agents, rerolled_agent))
        
        except (ValueError, PermissionError, KeyError) as error:
            return await self.send_error(ctx, error)


    @commands.hybrid_command(name="weapon", description="Ouvre un menu pour choisir les armes aléatoirement")
    async def weapon(self, ctx: commands.Context)->discord.Message:
        embed=discord.Embed(
            title = "Choix du type de round",
            color = 0xAE02A1
            )
        return await ctx.send(embed=embed, view=WeaponView(self.weapons))


    @commands.hybrid_command(name="refresh", description="Recharge les agents et armes depuis valorant-api")
    async def refresh(self, ctx: commands.Context)->discord.Message:
        try:
            n_agents, n_weapons = self._refresh_data()
            return await ctx.reply(f"Données à jour : {n_agents} agents, {n_weapons} armes", mention_author=False)
        except Exception as error:
            return await self.send_error(ctx, error)


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
    async def _get_game(self, ctx: commands.Context):
        """Récupère les données de la partie

        Args:
            ctx (commands.Context): Contexte de la commande

        Returns:
            _type_: Donnée de la partie
        """
        try:
            return self.games[ctx.guild.id]
        except KeyError:
            await ctx.reply("Tu dois d'abord faire `/start` pour créer une partie", mention_author=False)
            return None

    def _validate_teams(self, N: list[int]) -> None:
        """Vérifie que la dimention des équipes est conforme

        Args:
            N (list[int]): Liste des nombre de joueurs par équipe (N[0]: nombre de joueur de la première équipe)

        Raises:
            ValueError: Les équipes sont vide
            ValueError: Une des équipe est vide
        """
        if not any(N):
            raise ValueError("Aucune équipe enregistré. Utilisez la commande `start`")
        for k, n in enumerate(N):
            if not n:
                raise ValueError(f"L'équipe {k} est vide")

    async def _reply_team(self, ctx: commands.Context, game: Game, k: int, lines: list[str]) -> None:
        """Envoie un message embed discord avec la composition d'équipe

        Args:
            ctx (commands.Context): Contexte de la commande
            game (Game): Donnée de la partie
            k (int): indexe de l'équipe
            lines (list[str]): Lignes du message
        """
        embed = discord.Embed(title="Composition de l'équipe", description="\n".join(lines), color=game.color[k])
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
        await ctx.reply(embed=embed, mention_author=False)

    def _pick_full_random(self, n: int) -> list[Agent]:
        """Créer la composition d'équipe 100% aléatoirement

        Args:
            n (int): Nombre de joueur dans l'équipe

        Returns:
            list[Agent]: lineup de la compo
        """
        return list(rd.choice(self.agents, size=n, replace=False))

    def _pick_goodcomp(self, n: int) -> list[Agent]:
        """Créer la composition d'équipe avec au moins 1 agent par rôle

        Args:
            n (int): Nombre de joueur dans l'équipe

        Returns:
            list[Agent]: lineup de la compo
        """
        liste_role = ['duelist', 'controller', 'initiator', 'sentinel']
        rd.shuffle(liste_role)
        agents_tampon = self.agents.copy()
        
        count = n - 1 if n == 5 else n
        picks = [self.pick_agent(liste_role[i]) for i in range(count)]
        for agent in picks:
            agents_tampon.remove(agent)
        if n == 5:
            picks.append(rd.choice(agents_tampon))
        return picks

    def _assign_team(self, game: Game, k: int, picks: list[Agent]) -> None:
        players = game.participants[k]
        for i, player in enumerate(players):
            if picks[i].nom in game.locked.get(player.id, ()):
                for j in range(len(picks)):
                    if (picks[j].nom not in game.locked.get(player.id, ())
                            and picks[i].nom not in game.locked.get(players[j].id, ())):
                        picks[i], picks[j] = picks[j], picks[i]
                        break
        for player, agent in zip(players, picks):
            game.lineup[k][player] = agent

    def _pool_reroll(self, game: Game, current_lineup: dict, user: discord.Member) -> list[Agent]:
        match game.mode_aleatoire:
            case 'Full random':
                pool = self.agents.copy()
            case 'Goodcomp':
                pool = self.agents_by_role(current_lineup[user].role)
            case _:
                raise ValueError("Génère d'abord une compo avec `agent` ou `goodcomp`")
            
        locked = game.locked.get(user.id, set())
        pool = [agent for agent in pool if agent not in current_lineup.values() and agent.nom not in locked]
        if not pool:
            raise ValueError("Aucun agent disponible pour le reroll")
        
        return pool

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

    VALO_API = "https://valorant-api.com/v1"
    WEAPON_ORDER = {"melee": 0, "sidearm": 1, "smg": 2, "shotgun": 3, "rifle": 4, "sniper": 5, "heavy": 6}

    def _fetch_json(self, path: str) -> dict:
        """Récupère des données sur l'API Riot

        Args:
            path (str): Path API des données

        Returns:
            dict: Données récupérées
        """
        req = urllib.request.Request(f"{self.VALO_API}{path}", headers={"User-Agent": "RandomValo-bot"})
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.load(res)

    def _fetch_agents(self) -> list[Agent]:
        """Fetch la liste des agents sur le jeu

        Returns:
            list[Agent]: Liste des agents
        """
        data = self._fetch_json("/agents?language=en-US&isPlayableCharacter=true")["data"]
        return [Agent(agent["displayName"], agent["role"]["displayName"].lower()) 
                for agent in data if agent.get("role")]

    def _fetch_weapons(self) -> list[Weapon]:
        """Fetch la liste des armes syr le jeu

        Returns:
            list[Weapon]: Liste des armes
        """
        data = self._fetch_json("/weapons?language=en-US")["data"]
        items = [(weapon["displayName"], weapon["category"].split("::")[-1].lower()) for weapon in data]
        items.sort(key=lambda t: self.WEAPON_ORDER[t[1]])
        return [Weapon(nom, "cut" if cat == "melee" else cat) for nom, cat in items]

    def _save_snapshot(self) -> None:
        """Sauvegarde localement les listes d'agents et armes
        """
        payload = {"Agents": [[a.nom, a.role] for a in self.agents],
                   "Weapons": [[w.nom, w.type_arme] for w in self.weapons]}
        with open(PARENT_FOLDER / "valorant.json", "w") as file:
            json.dump(payload, file, indent=2)

    def _refresh_data(self) -> tuple[int, int]:
        """Fetch toute les données d'agents et armes

        Returns:
            tuple[int, int]: Nombre d'agents et armes
        """
        agents = self._fetch_agents()
        weapons = self._fetch_weapons()
        self.agents, self.weapons = agents, weapons
        self._save_snapshot()
        
        return len(agents), len(weapons)

    def load_data_from_sql(self, object:str)->list[Agent|Weapon]:
        with connect(f"{PARENT_FOLDER}/valorant.sqlite") as connection:
            curseur = connection.cursor()
            
            curseur.execute(f"SELECT nom , classe FROM {object}")
            classe_object = dict_classes_object[object]
            
        return [classe_object(*args) for args in curseur.fetchall()]

    def load_data_from_json(self, object: str)->list[Agent|Weapon]:
        with open(PARENT_FOLDER / "valorant.json") as file:
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
