"""Pokemon type effectiveness calculations."""

from typing import Dict, List, Tuple
from enum import Enum

class TypeEffectiveness(Enum):
    """Type effectiveness multipliers."""
    NO_EFFECT = 0.0
    NOT_VERY_EFFECTIVE = 0.5
    NORMAL = 1.0
    SUPER_EFFECTIVE = 2.0

# Complete Pokemon type effectiveness chart
TYPE_CHART = {
    "normal": {
        "rock": 0.5, "ghost": 0.0, "steel": 0.5
    },
    "fire": {
        "fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0,
        "rock": 0.5, "dragon": 0.5, "steel": 2.0
    },
    "water": {
        "fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0,
        "rock": 2.0, "dragon": 0.5
    },
    "electric": {
        "water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0,
        "flying": 2.0, "dragon": 0.5
    },
    "grass": {
        "fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5,
        "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0,
        "dragon": 0.5, "steel": 0.5
    },
    "ice": {
        "fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5,
        "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5
    },
    "fighting": {
        "normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5,
        "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0,
        "dark": 2.0, "steel": 2.0, "fairy": 0.5
    },
    "poison": {
        "grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5,
        "ghost": 0.5, "steel": 0.0, "fairy": 2.0
    },
    "ground": {
        "fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0,
        "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0
    },
    "flying": {
        "electric": 0.5, "grass": 2.0, "ice": 0.5, "fighting": 2.0,
        "bug": 2.0, "rock": 0.5, "steel": 0.5
    },
    "psychic": {
        "fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0,
        "steel": 0.5
    },
    "bug": {
        "fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5,
        "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0,
        "steel": 0.5, "fairy": 0.5
    },
    "rock": {
        "fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5,
        "flying": 2.0, "bug": 2.0, "steel": 0.5
    },
    "ghost": {
        "normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5
    },
    "dragon": {
        "dragon": 2.0, "steel": 0.5, "fairy": 0.0
    },
    "dark": {
        "fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5,
        "fairy": 0.5
    },
    "steel": {
        "fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0,
        "rock": 2.0, "steel": 0.5, "fairy": 2.0
    },
    "fairy": {
        "fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0,
        "dark": 2.0, "steel": 0.5
    }
}

POKEMON_TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice", "fighting",
    "poison", "ground", "flying", "psychic", "bug", "rock", "ghost",
    "dragon", "dark", "steel", "fairy"
]


def get_type_effectiveness(attacking_type: str, defending_type: str) -> float:
    """Get effectiveness multiplier for attacking type vs defending type."""
    attacking_type = attacking_type.lower()
    defending_type = defending_type.lower()
    
    if attacking_type not in POKEMON_TYPES or defending_type not in POKEMON_TYPES:
        return 1.0
    
    return TYPE_CHART.get(attacking_type, {}).get(defending_type, 1.0)


def get_dual_type_effectiveness(attacking_type: str, defending_types: List[str]) -> float:
    """Get effectiveness against dual-type Pokemon."""
    if not defending_types:
        return 1.0
    
    total_effectiveness = 1.0
    for defending_type in defending_types:
        effectiveness = get_type_effectiveness(attacking_type, defending_type)
        total_effectiveness *= effectiveness
    
    return total_effectiveness


def get_effectiveness_description(multiplier: float) -> str:
    """Get human-readable description of effectiveness."""
    if multiplier == 0.0:
        return "has no effect"
    elif multiplier < 0.5:
        return "is barely effective"
    elif multiplier == 0.5:
        return "is not very effective"
    elif multiplier == 1.0:
        return ""
    elif multiplier == 2.0:
        return "is super effective"
    elif multiplier > 2.0:
        return "is extremely effective"
    else:
        return "is effective"


def calculate_stab_multiplier(move_type: str, pokemon_types: List[str]) -> float:
    """Calculate Same Type Attack Bonus multiplier."""
    move_type = move_type.lower()
    pokemon_types = [t.lower() for t in pokemon_types]
    
    return 1.5 if move_type in pokemon_types else 1.0


def get_type_weaknesses(pokemon_types: List[str]) -> Dict[str, float]:
    """Get all type weaknesses for a Pokemon."""
    weaknesses = {}
    
    for attacking_type in POKEMON_TYPES:
        effectiveness = get_dual_type_effectiveness(attacking_type, pokemon_types)
        if effectiveness > 1.0:
            weaknesses[attacking_type] = effectiveness
    
    return weaknesses


def get_type_resistances(pokemon_types: List[str]) -> Dict[str, float]:
    """Get all type resistances for a Pokemon."""
    resistances = {}
    
    for attacking_type in POKEMON_TYPES:
        effectiveness = get_dual_type_effectiveness(attacking_type, pokemon_types)
        if effectiveness < 1.0:
            resistances[attacking_type] = effectiveness
    
    return resistances


def analyze_matchup(attacker_types: List[str], defender_types: List[str]) -> Dict[str, float]:
    """Analyze type matchup between two Pokemon."""
    matchup = {}
    
    for attacking_type in attacker_types:
        effectiveness = get_dual_type_effectiveness(attacking_type, defender_types)
        matchup[attacking_type] = effectiveness
    
    return matchup