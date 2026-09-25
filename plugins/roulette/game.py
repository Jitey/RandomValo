import discord
from dataclasses import dataclass, field

from .models import Agent


# |-----------Contient les données du jeu----------|
@dataclass
class Game:
    nb_joueurs: int = 0
    participants: list[list[discord.Member]] = field(default_factory=lambda: [[], []])
    lineup: list[dict[discord.Member, Agent]] = field(default_factory=lambda: [{}, {}])
    color: list[int] = field(default_factory=lambda: [0x9ACD32, 0xFF0000])
    author: discord.User | None = None
    mode_aleatoire: str = ""
    locked: dict[int, set[str]] = field(default_factory=dict)


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
    
    def ready(self):
        return len(self.participants[0]) + len(self.participants[1]) == self.nb_joueurs

    def __str__(self):
        return f"Game(nb_joueurs={self.nb_joueurs}, participants={self.participants}, lineup={self.lineup})"


    def __repr__(self):
        return f"Game(nb_joueurs={self.nb_joueurs}, participants={self.participants}, lineup={self.lineup})"
