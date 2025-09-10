import random
from typing import Dict, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

from .types import PokemonTypes
from .status import StatusManager

if TYPE_CHECKING:
    from ..models.pokemon import BattlePokemon, MoveDetails


@dataclass
class DamageResult:
    """Result of a damage calculation"""
    damage: int
    is_critical: bool
    type_effectiveness: float
    stab_applied: bool
    effectiveness_message: str
    critical_message: str
    total_modifier: float


class DamageCalculator:
    """Handles all damage calculations for Pokemon battles"""
    
    def __init__(self):
        self.type_system = PokemonTypes()
    
    def calculate_damage(
        self,
        attacker: 'BattlePokemon',
        defender: 'BattlePokemon',
        move: 'MoveDetails',
        weather: Optional[str] = None,
        terrain: Optional[str] = None,
        critical_override: Optional[bool] = None
    ) -> DamageResult:
        """
        Calculate damage using the Pokemon damage formula
        
        Formula: Damage = (((2 × Level ÷ 5 + 2) × Power × A ÷ D) ÷ 50 + 2) × Modifiers
        
        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            move: Move being used
            weather: Current weather condition
            terrain: Current terrain
            critical_override: Force critical hit (for testing)
            
        Returns:
            DamageResult with all calculation details
        """
        # Status moves deal no damage
        if move.damage_class == "status" or move.power is None or move.power <= 0:
            return DamageResult(
                damage=0,
                is_critical=False,
                type_effectiveness=1.0,
                stab_applied=False,
                effectiveness_message="",
                critical_message="",
                total_modifier=0.0
            )
        
        # Determine if move is physical or special
        is_physical = move.damage_class == "physical"
        
        # Get attack and defense stats
        attack_stat = self._get_effective_attack_stat(attacker, is_physical)
        defense_stat = self._get_effective_defense_stat(defender, is_physical)
        
        # Base damage calculation
        level = attacker.level
        power = move.power
        
        # Core formula: (((2 × Level ÷ 5 + 2) × Power × A ÷ D) ÷ 50 + 2)
        base_damage = (((2 * level / 5 + 2) * power * attack_stat / defense_stat) / 50 + 2)
        
        # Calculate modifiers
        modifiers = self._calculate_modifiers(attacker, defender, move, weather, terrain)
        
        # Apply critical hit
        is_critical = critical_override if critical_override is not None else self._check_critical_hit(attacker, move)
        if is_critical:
            modifiers['critical'] = 1.5
        
        # Calculate final damage
        total_modifier = 1.0
        for modifier in modifiers.values():
            total_modifier *= modifier
        
        final_damage = int(base_damage * total_modifier)
        
        # Apply random factor (85-100%)
        random_factor = random.randint(85, 100) / 100
        final_damage = max(1, int(final_damage * random_factor))
        
        # Generate result messages
        effectiveness_message = self._get_effectiveness_message(modifiers['type'])
        critical_message = "A critical hit!" if is_critical else ""
        
        return DamageResult(
            damage=final_damage,
            is_critical=is_critical,
            type_effectiveness=modifiers['type'],
            stab_applied=modifiers['stab'] > 1.0,
            effectiveness_message=effectiveness_message,
            critical_message=critical_message,
            total_modifier=total_modifier
        )
    
    def _get_effective_attack_stat(self, pokemon: 'BattlePokemon', is_physical: bool) -> int:
        """Get effective attack stat considering status effects and stat modifiers"""
        if is_physical:
            base_stat = pokemon.get_effective_stat("attack")
            # Apply burn effect if present
            if "burn" in pokemon.status_effects:
                base_stat = int(base_stat * 0.5)
        else:
            base_stat = pokemon.get_effective_stat("special_attack")
        
        return max(1, base_stat)  # Minimum stat value of 1
    
    def _get_effective_defense_stat(self, pokemon: 'BattlePokemon', is_physical: bool) -> int:
        """Get effective defense stat considering stat modifiers"""
        if is_physical:
            base_stat = pokemon.get_effective_stat("defense")
        else:
            base_stat = pokemon.get_effective_stat("special_defense")
        
        return max(1, base_stat)  # Minimum stat value of 1
    
    def _calculate_modifiers(
        self,
        attacker: 'BattlePokemon',
        defender: 'BattlePokemon',
        move: 'MoveDetails',
        weather: Optional[str] = None,
        terrain: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate all damage modifiers"""
        modifiers = {}
        
        # STAB (Same Type Attack Bonus)
        modifiers['stab'] = self._calculate_stab(attacker, move)
        
        # Type effectiveness
        modifiers['type'] = self._calculate_type_effectiveness(defender, move)
        
        # Weather effects
        modifiers['weather'] = self._calculate_weather_modifier(move, weather)
        
        # Terrain effects (placeholder for future implementation)
        modifiers['terrain'] = 1.0
        
        # Ability modifiers (placeholder for future implementation)
        modifiers['ability'] = 1.0
        
        # Item modifiers (placeholder for future implementation)
        modifiers['item'] = 1.0
        
        # Other modifiers (placeholder)
        modifiers['other'] = 1.0
        
        return modifiers
    
    def _calculate_stab(self, attacker: 'BattlePokemon', move: 'MoveDetails') -> float:
        """Calculate Same Type Attack Bonus"""
        if self.type_system.is_same_type_attack_bonus(move.type, attacker.pokemon.types):
            return 1.5
        return 1.0
    
    def _calculate_type_effectiveness(self, defender: 'BattlePokemon', move: 'MoveDetails') -> float:
        """Calculate type effectiveness multiplier"""
        return self.type_system.get_dual_type_effectiveness(move.type, defender.pokemon.types)
    
    def _calculate_weather_modifier(self, move: 'MoveDetails', weather: Optional[str]) -> float:
        """Calculate weather-based damage modifier"""
        if not weather:
            return 1.0
        
        # Rain boosts Water moves, weakens Fire moves
        if weather == "rain":
            if move.type == "water":
                return 1.5
            elif move.type == "fire":
                return 0.5
        
        # Sun boosts Fire moves, weakens Water moves
        elif weather == "sun":
            if move.type == "fire":
                return 1.5
            elif move.type == "water":
                return 0.5
        
        # Sandstorm boosts Rock moves (in some generations)
        elif weather == "sandstorm":
            if move.type == "rock":
                return 1.3
        
        return 1.0
    
    def _check_critical_hit(self, attacker: 'BattlePokemon', move: 'MoveDetails') -> bool:
        """Determine if move scores a critical hit"""
        # Base critical hit ratio is 1/24 (approximately 4.17%)
        critical_ratio = 24
        
        # Some moves have higher critical hit ratios
        high_crit_moves = ["razor-leaf", "slash", "crabhammer", "karate-chop"]
        if move.name in high_crit_moves:
            critical_ratio = 8  # 1/8 chance (12.5%)
        
        # Some abilities and items can affect critical hit ratio
        # (placeholder for future implementation)
        
        return random.randint(1, critical_ratio) == 1
    
    def _get_effectiveness_message(self, effectiveness: float) -> str:
        """Get message describing type effectiveness"""
        if effectiveness == 0.0:
            return "It had no effect..."
        elif effectiveness < 0.5:
            return "It's barely effective..."
        elif effectiveness == 0.5:
            return "It's not very effective..."
        elif effectiveness == 1.0:
            return ""  # No message for normal effectiveness
        elif effectiveness == 2.0:
            return "It's super effective!"
        elif effectiveness > 2.0:
            return "It's extremely effective!"
        else:
            return ""
    
    def calculate_stat_at_level(
        self,
        base_stat: int,
        level: int,
        iv: int = 31,
        ev: int = 0,
        nature_modifier: float = 1.0,
        is_hp: bool = False
    ) -> int:
        """
        Calculate a Pokemon's stat at a given level
        
        Args:
            base_stat: Base stat value
            level: Pokemon level
            iv: Individual Value (0-31)
            ev: Effort Value (0-255, max 510 total)
            nature_modifier: Nature modifier (0.9, 1.0, or 1.1)
            is_hp: Whether this is HP stat (uses different formula)
            
        Returns:
            Calculated stat value
        """
        if is_hp:
            # HP formula: ((2 * Base + IV + EV/4) * Level / 100) + Level + 10
            hp = int(((2 * base_stat + iv + ev // 4) * level / 100) + level + 10)
            return max(1, hp)
        else:
            # Other stats: (((2 * Base + IV + EV/4) * Level / 100) + 5) * Nature
            stat = int((((2 * base_stat + iv + ev // 4) * level / 100) + 5) * nature_modifier)
            return max(1, stat)
    
    def calculate_speed_tie(self, pokemon1: 'BattlePokemon', pokemon2: 'BattlePokemon') -> 'BattlePokemon':
        """
        Determine turn order when Pokemon have same speed
        
        Args:
            pokemon1: First Pokemon
            pokemon2: Second Pokemon
            
        Returns:
            Pokemon that goes first
        """
        # In case of speed tie, randomly choose who goes first
        return random.choice([pokemon1, pokemon2])
    
    def get_turn_order(self, pokemon1: 'BattlePokemon', pokemon2: 'BattlePokemon') -> Tuple['BattlePokemon', 'BattlePokemon']:
        """
        Determine turn order based on speed stats
        
        Args:
            pokemon1: First Pokemon
            pokemon2: Second Pokemon
            
        Returns:
            Tuple of (first_to_act, second_to_act)
        """
        speed1 = pokemon1.get_effective_stat("speed")
        speed2 = pokemon2.get_effective_stat("speed")
        
        # Apply paralysis speed reduction
        if "paralysis" in pokemon1.status_effects:
            speed1 = int(speed1 * 0.5)
        if "paralysis" in pokemon2.status_effects:
            speed2 = int(speed2 * 0.5)
        
        if speed1 > speed2:
            return pokemon1, pokemon2
        elif speed2 > speed1:
            return pokemon2, pokemon1
        else:
            # Speed tie
            first = self.calculate_speed_tie(pokemon1, pokemon2)
            second = pokemon2 if first == pokemon1 else pokemon1
            return first, second
    
    def calculate_healing(self, pokemon: 'BattlePokemon', heal_amount: int, is_percentage: bool = False) -> int:
        """
        Calculate healing amount
        
        Args:
            pokemon: Pokemon being healed
            heal_amount: Amount to heal (HP or percentage)
            is_percentage: Whether heal_amount is a percentage
            
        Returns:
            Actual HP healed
        """
        if is_percentage:
            max_heal = int(pokemon.max_hp * (heal_amount / 100))
        else:
            max_heal = heal_amount
        
        # Don't heal above max HP
        actual_heal = min(max_heal, pokemon.max_hp - pokemon.current_hp)
        return max(0, actual_heal)
    
    def apply_recoil_damage(self, pokemon: 'BattlePokemon', damage_dealt: int, recoil_percentage: float = 0.25) -> int:
        """
        Calculate and apply recoil damage
        
        Args:
            pokemon: Pokemon taking recoil
            damage_dealt: Damage dealt by the move
            recoil_percentage: Percentage of damage as recoil
            
        Returns:
            Actual recoil damage taken
        """
        recoil_damage = max(1, int(damage_dealt * recoil_percentage))
        pokemon.current_hp = max(0, pokemon.current_hp - recoil_damage)
        return recoil_damage
    
    def calculate_priority(self, move: 'MoveDetails') -> int:
        """
        Get move priority for turn order calculation
        
        Args:
            move: Move details
            
        Returns:
            Priority value (higher = goes first)
        """
        # Most moves have priority 0
        # Quick Attack, Extreme Speed etc. have positive priority
        # Some moves like Counter have negative priority
        return move.priority
    
    def is_move_effective(self, defender: 'BattlePokemon', move: 'MoveDetails') -> bool:
        """
        Check if a move can affect the target
        
        Args:
            defender: Defending Pokemon
            move: Move being used
            
        Returns:
            True if move can hit target
        """
        effectiveness = self._calculate_type_effectiveness(defender, move)
        return effectiveness > 0.0