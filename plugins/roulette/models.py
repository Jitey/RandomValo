from dataclasses import dataclass


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


STARTERS = frozenset({'Brimstone', 'Phoenix', 'Jett', 'Sova', 'Sage'})
