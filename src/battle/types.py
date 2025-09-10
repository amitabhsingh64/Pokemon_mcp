from typing import Dict, List, Tuple
from enum import Enum


class TypeEffectiveness(Enum):
    """Type effectiveness multipliers"""
    NO_EFFECT = 0.0
    NOT_VERY_EFFECTIVE = 0.5
    NORMAL = 1.0
    SUPER_EFFECTIVE = 2.0


class PokemonTypes:
    """Complete Pokémon type effectiveness chart"""
    
    # All 18 Pokémon types
    TYPES = [
        "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
        "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", 
        "dark", "steel", "fairy"
    ]
    
    # Type effectiveness chart: attacking_type -> {defending_type: multiplier}
    # Based on Generation 6+ (includes Fairy type)
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
    
    @classmethod
    def get_effectiveness(cls, attacking_type: str, defending_type: str) -> float:
        """
        Get type effectiveness multiplier for attacking type vs defending type
        
        Args:
            attacking_type: The type of the attacking move
            defending_type: The type of the defending Pokémon
            
        Returns:
            Effectiveness multiplier (0.0, 0.5, 1.0, or 2.0)
        """
        attacking_type = attacking_type.lower()
        defending_type = defending_type.lower()
        
        if attacking_type not in cls.TYPES or defending_type not in cls.TYPES:
            return 1.0  # Default to normal effectiveness for unknown types
        
        # Get effectiveness from chart, default to 1.0 (normal effectiveness)
        return cls.TYPE_CHART.get(attacking_type, {}).get(defending_type, 1.0)
    
    @classmethod
    def get_dual_type_effectiveness(
        cls, 
        attacking_type: str, 
        defending_types: List[str]
    ) -> float:
        """
        Get effectiveness against a dual-type Pokémon
        Multiplies effectiveness against both types
        
        Args:
            attacking_type: The type of the attacking move
            defending_types: List of defending Pokémon's types (1 or 2)
            
        Returns:
            Combined effectiveness multiplier (0.0, 0.25, 0.5, 1.0, 2.0, or 4.0)
        """
        if not defending_types:
            return 1.0
        
        total_effectiveness = 1.0
        for defending_type in defending_types:
            effectiveness = cls.get_effectiveness(attacking_type, defending_type)
            total_effectiveness *= effectiveness
        
        return total_effectiveness
    
    @classmethod
    def get_effectiveness_description(cls, multiplier: float) -> str:
        """
        Get human-readable description of effectiveness
        
        Args:
            multiplier: Effectiveness multiplier
            
        Returns:
            String description of effectiveness
        """
        if multiplier == 0.0:
            return "has no effect"
        elif multiplier < 0.5:
            return "is barely effective"
        elif multiplier == 0.5:
            return "is not very effective"
        elif multiplier == 1.0:
            return "is normally effective"
        elif multiplier == 2.0:
            return "is super effective"
        elif multiplier > 2.0:
            return "is extremely effective"
        else:
            return "is effective"
    
    @classmethod
    def get_type_weaknesses(cls, pokemon_types: List[str]) -> Dict[str, float]:
        """
        Get all type weaknesses for a Pokémon
        
        Args:
            pokemon_types: List of the Pokémon's types
            
        Returns:
            Dict mapping attacking types to effectiveness multipliers > 1.0
        """
        weaknesses = {}
        
        for attacking_type in cls.TYPES:
            effectiveness = cls.get_dual_type_effectiveness(attacking_type, pokemon_types)
            if effectiveness > 1.0:
                weaknesses[attacking_type] = effectiveness
        
        return weaknesses
    
    @classmethod
    def get_type_resistances(cls, pokemon_types: List[str]) -> Dict[str, float]:
        """
        Get all type resistances for a Pokémon
        
        Args:
            pokemon_types: List of the Pokémon's types
            
        Returns:
            Dict mapping attacking types to effectiveness multipliers < 1.0
        """
        resistances = {}
        
        for attacking_type in cls.TYPES:
            effectiveness = cls.get_dual_type_effectiveness(attacking_type, pokemon_types)
            if effectiveness < 1.0:
                resistances[attacking_type] = effectiveness
        
        return resistances
    
    @classmethod
    def get_type_immunities(cls, pokemon_types: List[str]) -> List[str]:
        """
        Get all type immunities for a Pokémon
        
        Args:
            pokemon_types: List of the Pokémon's types
            
        Returns:
            List of types that have no effect (0.0x)
        """
        immunities = []
        
        for attacking_type in cls.TYPES:
            effectiveness = cls.get_dual_type_effectiveness(attacking_type, pokemon_types)
            if effectiveness == 0.0:
                immunities.append(attacking_type)
        
        return immunities
    
    @classmethod
    def is_same_type_attack_bonus(cls, move_type: str, pokemon_types: List[str]) -> bool:
        """
        Check if move gets Same Type Attack Bonus (STAB)
        
        Args:
            move_type: Type of the move being used
            pokemon_types: List of the Pokémon's types
            
        Returns:
            True if move type matches any of the Pokémon's types
        """
        move_type = move_type.lower()
        return move_type in [ptype.lower() for ptype in pokemon_types]
    
    @classmethod
    def get_stab_multiplier(cls, move_type: str, pokemon_types: List[str]) -> float:
        """
        Get STAB multiplier (1.5x if same type, 1.0x otherwise)
        
        Args:
            move_type: Type of the move being used
            pokemon_types: List of the Pokémon's types
            
        Returns:
            STAB multiplier (1.5 or 1.0)
        """
        return 1.5 if cls.is_same_type_attack_bonus(move_type, pokemon_types) else 1.0
    
    @classmethod
    def analyze_matchup(cls, attacker_types: List[str], defender_types: List[str]) -> Dict[str, float]:
        """
        Analyze type matchup between two Pokémon
        
        Args:
            attacker_types: Attacking Pokémon's types
            defender_types: Defending Pokémon's types
            
        Returns:
            Dict with effectiveness of each attacker type vs defender
        """
        matchup = {}
        
        for attacking_type in attacker_types:
            effectiveness = cls.get_dual_type_effectiveness(attacking_type, defender_types)
            matchup[attacking_type] = effectiveness
        
        return matchup
    
    @classmethod
    def get_best_attacking_type(cls, attacker_types: List[str], defender_types: List[str]) -> Tuple[str, float]:
        """
        Get the best attacking type for the matchup
        
        Args:
            attacker_types: Attacking Pokémon's types
            defender_types: Defending Pokémon's types
            
        Returns:
            Tuple of (best_type, effectiveness)
        """
        best_type = attacker_types[0] if attacker_types else "normal"
        best_effectiveness = 0.0
        
        for attacking_type in attacker_types:
            effectiveness = cls.get_dual_type_effectiveness(attacking_type, defender_types)
            if effectiveness > best_effectiveness:
                best_effectiveness = effectiveness
                best_type = attacking_type
        
        return best_type, best_effectiveness
    
    @classmethod
    def validate_type(cls, type_name: str) -> bool:
        """
        Validate if a type name is valid
        
        Args:
            type_name: Type name to validate
            
        Returns:
            True if valid type
        """
        return type_name.lower() in cls.TYPES
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get list of all valid Pokémon types"""
        return cls.TYPES.copy()
    
    @classmethod
    def get_type_chart_summary(cls) -> Dict[str, Dict[str, List[str]]]:
        """
        Get a summary of the type chart organized by effectiveness
        
        Returns:
            Dict with types organized by their offensive effectiveness
        """
        summary = {}
        
        for attacking_type in cls.TYPES:
            summary[attacking_type] = {
                "super_effective": [],
                "not_very_effective": [],
                "no_effect": []
            }
            
            type_data = cls.TYPE_CHART.get(attacking_type, {})
            
            for defending_type, effectiveness in type_data.items():
                if effectiveness == 2.0:
                    summary[attacking_type]["super_effective"].append(defending_type)
                elif effectiveness == 0.5:
                    summary[attacking_type]["not_very_effective"].append(defending_type)
                elif effectiveness == 0.0:
                    summary[attacking_type]["no_effect"].append(defending_type)
        
        return summary