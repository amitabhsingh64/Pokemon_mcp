"""Pokemon moves database with comprehensive move data."""

from typing import Dict, List, Optional
from enum import Enum
import random

from .status_effects import StatusType


class MoveCategory(Enum):
    """Move categories."""
    PHYSICAL = "physical"
    SPECIAL = "special"
    STATUS = "status"


class Move:
    """Pokemon move data."""
    
    def __init__(
        self, 
        name: str,
        type: str,
        category: MoveCategory,
        power: int = 0,
        accuracy: int = 100,
        pp: int = 10,
        priority: int = 0,
        status_effect: Optional[StatusType] = None,
        status_chance: float = 0.0,
        description: str = ""
    ):
        self.name = name
        self.type = type
        self.category = category
        self.power = power
        self.accuracy = accuracy
        self.pp = pp
        self.priority = priority
        self.status_effect = status_effect
        self.status_chance = status_chance
        self.description = description


# Comprehensive moves database
MOVES_DATABASE = {
    # Normal-type moves
    "tackle": Move("Tackle", "normal", MoveCategory.PHYSICAL, 40, 100, 35, 0, None, 0.0, "A physical attack in which the user charges and slams into the target with its whole body."),
    "scratch": Move("Scratch", "normal", MoveCategory.PHYSICAL, 40, 100, 35, 0, None, 0.0, "Hard, pointed, sharp claws rake the target to inflict damage."),
    "quick-attack": Move("Quick Attack", "normal", MoveCategory.PHYSICAL, 40, 100, 30, 1, None, 0.0, "The user lunges at the target at a speed that makes it almost invisible. This move always goes first."),
    "body-slam": Move("Body Slam", "normal", MoveCategory.PHYSICAL, 85, 100, 15, 0, StatusType.PARALYSIS, 0.3, "The user drops onto the target with its full body weight. This may also leave the target with paralysis."),
    "hyper-beam": Move("Hyper Beam", "normal", MoveCategory.SPECIAL, 150, 90, 5, 0, None, 0.0, "The target is attacked with a powerful beam. The user can't move on the next turn."),
    
    # Fire-type moves
    "ember": Move("Ember", "fire", MoveCategory.SPECIAL, 40, 100, 25, 0, StatusType.BURN, 0.1, "The target is attacked with small flames. This may also leave the target with a burn."),
    "flamethrower": Move("Flamethrower", "fire", MoveCategory.SPECIAL, 90, 100, 15, 0, StatusType.BURN, 0.1, "The target is scorched with an intense blast of fire. This may also leave the target with a burn."),
    "fire-blast": Move("Fire Blast", "fire", MoveCategory.SPECIAL, 110, 85, 5, 0, StatusType.BURN, 0.1, "The target is attacked with an intense blast of all-consuming fire. This may also leave the target with a burn."),
    "fire-punch": Move("Fire Punch", "fire", MoveCategory.PHYSICAL, 75, 100, 15, 0, StatusType.BURN, 0.1, "The target is punched with a fiery fist. This may also leave the target with a burn."),
    
    # Water-type moves
    "water-gun": Move("Water Gun", "water", MoveCategory.SPECIAL, 40, 100, 25, 0, None, 0.0, "The target is blasted with a forceful shot of water."),
    "bubble-beam": Move("Bubble Beam", "water", MoveCategory.SPECIAL, 65, 100, 20, 0, None, 0.0, "A spray of countless bubbles is jetted at the opposing Pokémon."),
    "surf": Move("Surf", "water", MoveCategory.SPECIAL, 90, 100, 15, 0, None, 0.0, "The user attacks everything around it by swamping its surroundings with a giant wave."),
    "hydro-pump": Move("Hydro Pump", "water", MoveCategory.SPECIAL, 110, 80, 5, 0, None, 0.0, "The target is blasted by a huge volume of water launched under great pressure."),
    
    # Electric-type moves
    "thunder-shock": Move("Thunder Shock", "electric", MoveCategory.SPECIAL, 40, 100, 30, 0, StatusType.PARALYSIS, 0.1, "A jolt of electricity crashes down on the target to inflict damage. This may also leave the target with paralysis."),
    "thunderbolt": Move("Thunderbolt", "electric", MoveCategory.SPECIAL, 90, 100, 15, 0, StatusType.PARALYSIS, 0.1, "A strong electric blast crashes down on the target. This may also leave the target with paralysis."),
    "thunder": Move("Thunder", "electric", MoveCategory.SPECIAL, 110, 70, 10, 0, StatusType.PARALYSIS, 0.3, "A wicked thunderbolt is dropped on the target to inflict damage. This may also leave the target with paralysis."),
    "thunder-punch": Move("Thunder Punch", "electric", MoveCategory.PHYSICAL, 75, 100, 15, 0, StatusType.PARALYSIS, 0.1, "The target is punched with an electrified fist. This may also leave the target with paralysis."),
    
    # Grass-type moves
    "vine-whip": Move("Vine Whip", "grass", MoveCategory.PHYSICAL, 45, 100, 25, 0, None, 0.0, "The target is struck with slender whiplike vines to inflict damage."),
    "razor-leaf": Move("Razor Leaf", "grass", MoveCategory.PHYSICAL, 55, 95, 25, 0, None, 0.0, "Sharp-edged leaves are launched to slash at the opposing Pokémon."),
    "solar-beam": Move("Solar Beam", "grass", MoveCategory.SPECIAL, 120, 100, 10, 0, None, 0.0, "A two-turn attack. The user gathers light, then blasts a bundled beam on the next turn."),
    
    # Ice-type moves
    "ice-beam": Move("Ice Beam", "ice", MoveCategory.SPECIAL, 90, 100, 10, 0, StatusType.FREEZE, 0.1, "The target is struck with an icy-cold beam of energy. This may also leave the target frozen."),
    "blizzard": Move("Blizzard", "ice", MoveCategory.SPECIAL, 110, 70, 5, 0, StatusType.FREEZE, 0.1, "A howling blizzard is summoned to strike opposing Pokémon. This may also leave the target frozen."),
    
    # Psychic-type moves
    "psychic": Move("Psychic", "psychic", MoveCategory.SPECIAL, 90, 100, 10, 0, None, 0.0, "The target is hit by a strong telekinetic force. This may also lower the target's Sp. Def stat."),
    "psybeam": Move("Psybeam", "psychic", MoveCategory.SPECIAL, 65, 100, 20, 0, None, 0.0, "The target is attacked with a peculiar ray."),
    "confusion": Move("Confusion", "psychic", MoveCategory.SPECIAL, 50, 100, 25, 0, None, 0.0, "The target is hit by a weak telekinetic force."),
    
    # Poison-type moves
    "poison-sting": Move("Poison Sting", "poison", MoveCategory.PHYSICAL, 15, 100, 35, 0, StatusType.POISON, 0.3, "The user stabs the target with a poisonous stinger. This may also poison the target."),
    "sludge-bomb": Move("Sludge Bomb", "poison", MoveCategory.SPECIAL, 90, 100, 10, 0, StatusType.POISON, 0.3, "Unsanitary sludge is hurled at the target. This may also poison the target."),
    
    # Fighting-type moves
    "karate-chop": Move("Karate Chop", "fighting", MoveCategory.PHYSICAL, 50, 100, 25, 0, None, 0.0, "The target is attacked with a sharp chop. Critical hits land more easily."),
    "seismic-toss": Move("Seismic Toss", "fighting", MoveCategory.PHYSICAL, 1, 100, 20, 0, None, 0.0, "The target is thrown using the power of gravity. It inflicts damage equal to the user's level."),
    
    # Ground-type moves
    "earthquake": Move("Earthquake", "ground", MoveCategory.PHYSICAL, 100, 100, 10, 0, None, 0.0, "The user sets off an earthquake that strikes every Pokémon around it."),
    
    # Flying-type moves
    "wing-attack": Move("Wing Attack", "flying", MoveCategory.PHYSICAL, 60, 100, 35, 0, None, 0.0, "The target is struck with large, imposing wings spread wide to inflict damage."),
    "fly": Move("Fly", "flying", MoveCategory.PHYSICAL, 90, 95, 15, 0, None, 0.0, "The user soars and then strikes its target on the next turn."),
    
    # Rock-type moves
    "rock-throw": Move("Rock Throw", "rock", MoveCategory.PHYSICAL, 50, 90, 15, 0, None, 0.0, "The user picks up and throws a small rock at the target to attack."),
    "rock-slide": Move("Rock Slide", "rock", MoveCategory.PHYSICAL, 75, 90, 10, 0, None, 0.0, "Large boulders are hurled at the opposing Pokémon to inflict damage."),
}


# Pokemon-specific movesets (Level-up moves only for simplicity)
POKEMON_MOVESETS = {
    "charizard": ["scratch", "ember", "flamethrower", "fire-blast", "wing-attack", "fly", "solar-beam", "earthquake"],
    "blastoise": ["tackle", "water-gun", "bubble-beam", "surf", "hydro-pump", "ice-beam", "earthquake", "body-slam"],
    "venusaur": ["tackle", "vine-whip", "razor-leaf", "solar-beam", "sludge-bomb", "earthquake", "body-slam", "poison-sting"],
    "pikachu": ["tackle", "thunder-shock", "thunderbolt", "thunder", "quick-attack", "body-slam", "seismic-toss", "thunder-punch"],
    "raichu": ["tackle", "thunder-shock", "thunderbolt", "thunder", "quick-attack", "body-slam", "seismic-toss", "thunder-punch"],
    "mewtwo": ["psychic", "psybeam", "confusion", "hyper-beam", "thunder-punch", "fire-punch", "ice-beam", "earthquake"],
    "mew": ["psychic", "psybeam", "confusion", "thunderbolt", "flamethrower", "ice-beam", "earthquake", "body-slam"],
    "zapdos": ["thunder-shock", "thunderbolt", "thunder", "wing-attack", "fly", "hyper-beam", "body-slam", "quick-attack"],
    "articuno": ["wing-attack", "fly", "ice-beam", "blizzard", "hyper-beam", "body-slam", "quick-attack", "psychic"],
    "moltres": ["wing-attack", "fly", "ember", "flamethrower", "fire-blast", "hyper-beam", "body-slam", "solar-beam"],
    "alakazam": ["psychic", "psybeam", "confusion", "thunder-punch", "fire-punch", "ice-beam", "hyper-beam", "seismic-toss"],
    "machamp": ["karate-chop", "seismic-toss", "earthquake", "fire-punch", "thunder-punch", "ice-beam", "rock-slide", "body-slam"],
    "gengar": ["confusion", "psychic", "thunder-punch", "fire-punch", "ice-beam", "sludge-bomb", "hypnosis", "body-slam"],
    "gyarados": ["tackle", "water-gun", "surf", "hydro-pump", "ice-beam", "thunderbolt", "earthquake", "hyper-beam"],
    "dragonite": ["wing-attack", "fly", "hyper-beam", "thunderbolt", "ice-beam", "flamethrower", "earthquake", "body-slam"],
    "snorlax": ["tackle", "body-slam", "hyper-beam", "earthquake", "surf", "thunderbolt", "ice-beam", "fire-punch"],
    
    # Add more Pokemon as needed - for demo, using basic movesets for others
    "default": ["tackle", "scratch", "quick-attack", "body-slam"]
}


def get_pokemon_moves(pokemon_name: str, level: int = 50, count: int = 4) -> List[Move]:
    """Get random moves for a Pokemon based on its moveset."""
    pokemon_name = pokemon_name.lower()
    
    # Get moveset for this Pokemon
    moveset = POKEMON_MOVESETS.get(pokemon_name, POKEMON_MOVESETS["default"])
    
    # For level-based restrictions, we could filter moves here
    # For now, just return random selection from available moves
    available_moves = [MOVES_DATABASE[move_name] for move_name in moveset if move_name in MOVES_DATABASE]
    
    # Return random selection of moves (typically 4 moves in Pokemon)
    selected_count = min(count, len(available_moves))
    return random.sample(available_moves, selected_count) if available_moves else []


def get_move_by_name(move_name: str) -> Optional[Move]:
    """Get move data by name."""
    return MOVES_DATABASE.get(move_name.lower())


def get_all_moves() -> List[Move]:
    """Get all available moves."""
    return list(MOVES_DATABASE.values())


def get_moves_by_type(move_type: str) -> List[Move]:
    """Get all moves of a specific type."""
    return [move for move in MOVES_DATABASE.values() if move.type.lower() == move_type.lower()]