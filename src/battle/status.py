import random
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..models.pokemon import BattlePokemon


class StatusType(Enum):
    """Available status effects"""
    PARALYSIS = "paralysis"
    BURN = "burn" 
    POISON = "poison"
    FREEZE = "freeze"
    SLEEP = "sleep"


class StatusEffect(ABC):
    """Base class for status effects"""
    
    def __init__(self, name: str, duration: Optional[int] = None):
        self.name = name
        self.duration = duration  # None = permanent until cured
        self.turns_active = 0
    
    @abstractmethod
    def apply_start_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Apply effect at start of turn. Return message describing effect."""
        pass
    
    @abstractmethod
    def apply_end_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Apply effect at end of turn. Return message describing effect."""
        pass
    
    @abstractmethod
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """Check if status prevents Pokemon from acting this turn."""
        pass
    
    @abstractmethod
    def get_stat_modifier(self, stat_name: str) -> float:
        """Get stat modifier for this status effect (multiplier)."""
        pass
    
    def advance_turn(self) -> bool:
        """
        Advance turn counter. 
        Returns True if status should be removed (duration expired).
        """
        self.turns_active += 1
        if self.duration is not None:
            return self.turns_active >= self.duration
        return False
    
    def can_be_applied_with(self, other_status: 'StatusEffect') -> bool:
        """Check if this status can be applied alongside another status."""
        # Most major status effects are mutually exclusive
        major_statuses = {StatusType.PARALYSIS, StatusType.BURN, StatusType.POISON, 
                         StatusType.FREEZE, StatusType.SLEEP}
        
        if (self.name in [s.value for s in major_statuses] and 
            other_status.name in [s.value for s in major_statuses]):
            return False
        
        return True


class ParalysisEffect(StatusEffect):
    """Paralysis status effect"""
    
    def __init__(self):
        super().__init__(StatusType.PARALYSIS.value)
        self.skip_chance = 0.25  # 25% chance to skip turn
    
    def apply_start_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Check if paralysis prevents action"""
        if random.random() < self.skip_chance:
            return f"{pokemon.pokemon.name} is paralyzed and cannot move!"
        return ""
    
    def apply_end_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """No end-of-turn effect for paralysis"""
        return ""
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """25% chance to prevent action"""
        return random.random() < self.skip_chance
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Paralysis reduces Speed by 50%"""
        if stat_name == "speed":
            return 0.5
        return 1.0


class BurnEffect(StatusEffect):
    """Burn status effect"""
    
    def __init__(self):
        super().__init__(StatusType.BURN.value)
        self.damage_fraction = 1/16  # 1/16 max HP per turn
    
    def apply_start_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """No start-of-turn effect for burn"""
        return ""
    
    def apply_end_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Apply burn damage at end of turn"""
        damage = max(1, int(pokemon.max_hp * self.damage_fraction))
        pokemon.current_hp = max(0, pokemon.current_hp - damage)
        
        return f"{pokemon.pokemon.name} is hurt by its burn! Lost {damage} HP."
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """Burn doesn't prevent actions"""
        return False
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Burn reduces Attack by 50%"""
        if stat_name == "attack":
            return 0.5
        return 1.0


class PoisonEffect(StatusEffect):
    """Poison status effect"""
    
    def __init__(self):
        super().__init__(StatusType.POISON.value)
        self.damage_fraction = 1/8  # 1/8 max HP per turn
    
    def apply_start_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """No start-of-turn effect for poison"""
        return ""
    
    def apply_end_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Apply poison damage at end of turn"""
        damage = max(1, int(pokemon.max_hp * self.damage_fraction))
        pokemon.current_hp = max(0, pokemon.current_hp - damage)
        
        return f"{pokemon.pokemon.name} is hurt by poison! Lost {damage} HP."
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """Poison doesn't prevent actions"""
        return False
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Poison has no stat modifiers"""
        return 1.0


class FreezeEffect(StatusEffect):
    """Freeze status effect (bonus implementation)"""
    
    def __init__(self):
        super().__init__(StatusType.FREEZE.value)
        self.thaw_chance = 0.2  # 20% chance to thaw each turn
    
    def apply_start_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Check if Pokemon thaws out"""
        if random.random() < self.thaw_chance:
            return f"{pokemon.pokemon.name} thawed out!"
        return f"{pokemon.pokemon.name} is frozen solid!"
    
    def apply_end_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """No end-of-turn effect for freeze"""
        return ""
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """Check if still frozen"""
        if random.random() < self.thaw_chance:
            # Remove freeze status
            if StatusType.FREEZE.value in pokemon.status_effects:
                pokemon.status_effects.remove(StatusType.FREEZE.value)
            return False
        return True
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Freeze has no stat modifiers"""
        return 1.0


class SleepEffect(StatusEffect):
    """Sleep status effect (bonus implementation)"""
    
    def __init__(self, duration: Optional[int] = None):
        # Sleep typically lasts 1-3 turns
        if duration is None:
            duration = random.randint(1, 3)
        super().__init__(StatusType.SLEEP.value, duration)
    
    def apply_start_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Check if Pokemon is still asleep"""
        if self.turns_active >= self.duration:
            return f"{pokemon.pokemon.name} woke up!"
        return f"{pokemon.pokemon.name} is fast asleep..."
    
    def apply_end_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """No end-of-turn effect for sleep"""
        return ""
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """Sleep prevents action until duration expires"""
        return self.turns_active < self.duration
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Sleep has no stat modifiers"""
        return 1.0


class StatusManager:
    """Manages status effects for Pokemon in battle"""
    
    # Map status names to their effect classes
    STATUS_EFFECTS = {
        StatusType.PARALYSIS.value: ParalysisEffect,
        StatusType.BURN.value: BurnEffect,
        StatusType.POISON.value: PoisonEffect,
        StatusType.FREEZE.value: FreezeEffect,
        StatusType.SLEEP.value: SleepEffect,
    }
    
    def __init__(self):
        self.active_effects: Dict[str, StatusEffect] = {}
    
    def apply_status(self, pokemon: 'BattlePokemon', status_type: StatusType) -> str:
        """
        Apply a status effect to a Pokemon
        
        Args:
            pokemon: Pokemon to apply status to
            status_type: Type of status to apply
            
        Returns:
            Message describing the status application
        """
        status_name = status_type.value
        
        # Check if Pokemon already has this status
        if status_name in self.active_effects:
            return f"{pokemon.pokemon.name} is already {status_name}!"
        
        # Check if status can be applied (type immunities, etc.)
        if not self._can_apply_status(pokemon, status_type):
            return f"{pokemon.pokemon.name} cannot be {status_name}!"
        
        # Check conflicts with existing status effects
        for existing_status in self.active_effects.values():
            new_effect = self.STATUS_EFFECTS[status_name]()
            if not new_effect.can_be_applied_with(existing_status):
                return f"{pokemon.pokemon.name} is already affected by {existing_status.name}!"
        
        # Apply the status effect
        effect = self.STATUS_EFFECTS[status_name]()
        self.active_effects[status_name] = effect
        
        # Add to Pokemon's status list if not already there
        if status_name not in pokemon.status_effects:
            pokemon.status_effects.append(status_name)
        
        return f"{pokemon.pokemon.name} is now {status_name}!"
    
    def remove_status(self, pokemon: 'BattlePokemon', status_type: StatusType) -> str:
        """
        Remove a status effect from a Pokemon
        
        Args:
            pokemon: Pokemon to remove status from
            status_type: Type of status to remove
            
        Returns:
            Message describing the status removal
        """
        status_name = status_type.value
        
        if status_name not in self.active_effects:
            return f"{pokemon.pokemon.name} is not {status_name}!"
        
        # Remove from active effects
        del self.active_effects[status_name]
        
        # Remove from Pokemon's status list
        if status_name in pokemon.status_effects:
            pokemon.status_effects.remove(status_name)
        
        return f"{pokemon.pokemon.name} is no longer {status_name}!"
    
    def process_start_turn_effects(self, pokemon: 'BattlePokemon') -> List[str]:
        """
        Process all start-of-turn status effects
        
        Args:
            pokemon: Pokemon to process effects for
            
        Returns:
            List of messages describing effects
        """
        messages = []
        effects_to_remove = []
        
        for status_name, effect in self.active_effects.items():
            # Apply start-of-turn effect
            message = effect.apply_start_turn_effect(pokemon)
            if message:
                messages.append(message)
            
            # Check if effect should be removed
            if effect.advance_turn():
                effects_to_remove.append(status_name)
        
        # Remove expired effects
        for status_name in effects_to_remove:
            messages.append(self.remove_status(pokemon, StatusType(status_name)))
        
        return messages
    
    def process_end_turn_effects(self, pokemon: 'BattlePokemon') -> List[str]:
        """
        Process all end-of-turn status effects
        
        Args:
            pokemon: Pokemon to process effects for
            
        Returns:
            List of messages describing effects
        """
        messages = []
        
        for effect in self.active_effects.values():
            message = effect.apply_end_turn_effect(pokemon)
            if message:
                messages.append(message)
        
        return messages
    
    def can_act(self, pokemon: 'BattlePokemon') -> bool:
        """
        Check if Pokemon can act this turn (not prevented by status)
        
        Args:
            pokemon: Pokemon to check
            
        Returns:
            True if Pokemon can act
        """
        for effect in self.active_effects.values():
            if effect.prevents_action(pokemon):
                return False
        return True
    
    def get_stat_multiplier(self, stat_name: str) -> float:
        """
        Get combined stat multiplier from all status effects
        
        Args:
            stat_name: Name of the stat
            
        Returns:
            Combined multiplier for the stat
        """
        multiplier = 1.0
        
        for effect in self.active_effects.values():
            multiplier *= effect.get_stat_modifier(stat_name)
        
        return multiplier
    
    def has_status(self, status_type: StatusType) -> bool:
        """Check if a specific status is active"""
        return status_type.value in self.active_effects
    
    def get_active_statuses(self) -> List[str]:
        """Get list of all active status names"""
        return list(self.active_effects.keys())
    
    def clear_all_statuses(self, pokemon: 'BattlePokemon') -> List[str]:
        """Clear all status effects"""
        messages = []
        
        for status_name in list(self.active_effects.keys()):
            messages.append(self.remove_status(pokemon, StatusType(status_name)))
        
        return messages
    
    def _can_apply_status(self, pokemon: 'BattlePokemon', status_type: StatusType) -> bool:
        """
        Check if a status can be applied to a Pokemon
        Considers type immunities and other factors
        """
        # Electric types are immune to paralysis
        if (status_type == StatusType.PARALYSIS and 
            "electric" in pokemon.pokemon.types):
            return False
        
        # Fire types are immune to burn
        if (status_type == StatusType.BURN and 
            "fire" in pokemon.pokemon.types):
            return False
        
        # Poison types are immune to poison
        if (status_type == StatusType.POISON and 
            ("poison" in pokemon.pokemon.types or "steel" in pokemon.pokemon.types)):
            return False
        
        # Ice types are immune to freeze
        if (status_type == StatusType.FREEZE and 
            "ice" in pokemon.pokemon.types):
            return False
        
        return True


def create_status_manager() -> StatusManager:
    """Factory function to create a new StatusManager"""
    return StatusManager()


# Status effect probability constants
STATUS_CHANCES = {
    "thunder_wave": 1.0,     # 100% paralysis chance
    "will_o_wisp": 1.0,      # 100% burn chance  
    "toxic": 1.0,            # 100% poison chance
    "body_slam": 0.3,        # 30% paralysis chance
    "flamethrower": 0.1,     # 10% burn chance
    "poison_sting": 0.3,     # 30% poison chance
}