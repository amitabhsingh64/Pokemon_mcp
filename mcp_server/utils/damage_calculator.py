"""Advanced Pokemon damage calculation engine."""

import random
import math
from typing import Dict, Optional, TYPE_CHECKING

from .type_chart import get_dual_type_effectiveness, calculate_stab_multiplier
from .moves_database import Move, MoveCategory

if TYPE_CHECKING:
    from ..battle import BattlePokemon


class DamageCalculator:
    """Advanced damage calculator using official Pokemon formula."""
    
    @staticmethod
    def calculate_damage(
        attacker: 'BattlePokemon',
        defender: 'BattlePokemon',
        move: Move,
        weather: str = "normal",
        terrain: str = "normal",
        is_critical: Optional[bool] = None
    ) -> Dict:
        """
        Calculate damage using the official Pokemon damage formula:
        Damage = (((2×Level÷5+2)×Power×A÷D)÷50+2) × Modifiers
        
        Returns dict with damage amount and calculation details.
        """
        if move.power <= 0 or move.category == MoveCategory.STATUS:
            return {
                "damage": 0,
                "is_critical": False,
                "effectiveness": 1.0,
                "stab": 1.0,
                "details": f"{move.name} is a status move - no damage dealt"
            }
        
        # Step 1: Base damage calculation
        level = attacker.level
        power = move.power
        
        # Get attack/defense stats based on move category
        if move.category == MoveCategory.PHYSICAL:
            attack_stat = attacker.get_effective_stat("attack")
            defense_stat = defender.get_effective_stat("defense")
        else:  # SPECIAL
            attack_stat = attacker.get_effective_stat("special_attack")
            defense_stat = defender.get_effective_stat("special_defense")
        
        # Base damage formula: ((2×Level÷5+2)×Power×A÷D)÷50+2)
        base_damage = ((2 * level / 5 + 2) * power * attack_stat / defense_stat) / 50 + 2
        
        # Step 2: Apply modifiers
        modifiers = []
        total_modifier = 1.0
        
        # Critical hit (determined or calculated)
        if is_critical is None:
            is_critical = DamageCalculator._calculate_critical_hit(attacker, move)
        
        if is_critical:
            critical_modifier = 1.5
            total_modifier *= critical_modifier
            modifiers.append(f"Critical hit! (×{critical_modifier})")
        
        # Type effectiveness
        effectiveness = get_dual_type_effectiveness(move.type, defender.types)
        total_modifier *= effectiveness
        
        effectiveness_text = DamageCalculator._get_effectiveness_text(effectiveness)
        if effectiveness_text:
            modifiers.append(effectiveness_text)
        
        # STAB (Same Type Attack Bonus)
        stab_modifier = calculate_stab_multiplier(move.type, attacker.types)
        if stab_modifier > 1.0:
            total_modifier *= stab_modifier
            modifiers.append(f"STAB (×{stab_modifier})")
        
        # Weather modifiers
        weather_modifier = DamageCalculator._get_weather_modifier(move.type, weather)
        if weather_modifier != 1.0:
            total_modifier *= weather_modifier
            modifiers.append(f"Weather (×{weather_modifier})")
        
        # Random factor (85-100%)
        random_factor = random.randint(85, 100) / 100
        total_modifier *= random_factor
        
        # Final damage calculation
        final_damage = int(base_damage * total_modifier)
        final_damage = max(1, final_damage)  # Minimum 1 damage
        
        return {
            "damage": final_damage,
            "is_critical": is_critical,
            "effectiveness": effectiveness,
            "stab": stab_modifier,
            "base_damage": int(base_damage),
            "total_modifier": total_modifier,
            "modifiers": modifiers,
            "details": f"{move.name} deals {final_damage} damage" + (f" ({', '.join(modifiers)})" if modifiers else "")
        }
    
    @staticmethod
    def _calculate_critical_hit(attacker: 'BattlePokemon', move: Move) -> bool:
        """Calculate if move results in critical hit."""
        # Base critical hit rate is 1/24 (approximately 4.17%)
        critical_rate = 1/24
        
        # Some moves have higher critical hit ratios
        high_crit_moves = ["karate-chop", "razor-leaf", "slash", "crabhammer"]
        if move.name.lower() in high_crit_moves:
            critical_rate = 1/8  # 12.5%
        
        return random.random() < critical_rate
    
    @staticmethod
    def _get_effectiveness_text(effectiveness: float) -> str:
        """Get descriptive text for type effectiveness."""
        if effectiveness == 0.0:
            return "It has no effect!"
        elif effectiveness < 0.5:
            return "It's barely effective..."
        elif effectiveness == 0.5:
            return "It's not very effective..."
        elif effectiveness == 2.0:
            return "It's super effective!"
        elif effectiveness > 2.0:
            return "It's extremely effective!"
        return ""
    
    @staticmethod
    def _get_weather_modifier(move_type: str, weather: str) -> float:
        """Get weather modifier for move damage."""
        weather = weather.lower()
        move_type = move_type.lower()
        
        # Weather effects
        weather_modifiers = {
            "sun": {"fire": 1.5, "water": 0.5},
            "rain": {"water": 1.5, "fire": 0.5},
            "sandstorm": {"rock": 1.5, "ground": 1.5, "steel": 1.5},
            "hail": {"ice": 1.5}
        }
        
        return weather_modifiers.get(weather, {}).get(move_type, 1.0)
    
    @staticmethod
    def calculate_status_damage(pokemon: 'BattlePokemon', status_type: str) -> int:
        """Calculate damage from status effects."""
        max_hp = pokemon.max_hp
        
        if status_type == "burn":
            return max(1, int(max_hp / 16))  # 1/16 max HP
        elif status_type == "poison":
            return max(1, int(max_hp / 8))   # 1/8 max HP
        elif status_type == "badly_poison":
            # Badly poisoned damage increases each turn
            turns_poisoned = getattr(pokemon.status_manager, 'poison_turns', 1)
            return max(1, int(max_hp * turns_poisoned / 16))
        
        return 0
    
    @staticmethod
    def calculate_recoil_damage(attacker: 'BattlePokemon', damage_dealt: int, move: Move) -> int:
        """Calculate recoil damage for moves like Double-Edge."""
        recoil_moves = {
            "double-edge": 0.33,    # 1/3 of damage dealt
            "take-down": 0.25,      # 1/4 of damage dealt
            "submission": 0.25,     # 1/4 of damage dealt
            "jump-kick": 0.50,      # 1/2 if miss
            "hi-jump-kick": 0.50,   # 1/2 if miss
        }
        
        recoil_ratio = recoil_moves.get(move.name.lower(), 0)
        if recoil_ratio > 0:
            return max(1, int(damage_dealt * recoil_ratio))
        
        return 0
    
    @staticmethod
    def calculate_healing(pokemon: 'BattlePokemon', move: Move) -> int:
        """Calculate healing from recovery moves."""
        healing_moves = {
            "recover": 0.5,         # 50% max HP
            "soft-boiled": 0.5,     # 50% max HP
            "rest": 1.0,            # 100% max HP
            "roost": 0.5,           # 50% max HP
            "synthesis": 0.5,       # 50% max HP (weather dependent)
            "moonlight": 0.5,       # 50% max HP (weather dependent)
            "morning-sun": 0.5,     # 50% max HP (weather dependent)
        }
        
        heal_ratio = healing_moves.get(move.name.lower(), 0)
        if heal_ratio > 0:
            max_healing = int(pokemon.max_hp * heal_ratio)
            actual_healing = min(max_healing, pokemon.max_hp - pokemon.current_hp)
            return actual_healing
        
        return 0