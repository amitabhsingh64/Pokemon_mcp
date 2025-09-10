"""Pokemon status effects implementation."""

import random
from abc import ABC, abstractmethod
from typing import Dict, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..battle import BattlePokemon


class StatusType(Enum):
    """Available status effects."""
    PARALYSIS = "paralysis"
    BURN = "burn"
    POISON = "poison"
    FREEZE = "freeze"
    SLEEP = "sleep"


class StatusEffect(ABC):
    """Base class for status effects."""
    
    def __init__(self, name: str, duration: Optional[int] = None):
        self.name = name
        self.duration = duration  # None = permanent until cured
        self.turns_active = 0
    
    @abstractmethod
    def apply_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Apply effect during turn. Return message describing effect."""
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
        """Advance turn counter. Returns True if status should be removed."""
        self.turns_active += 1
        if self.duration is not None:
            return self.turns_active >= self.duration
        return False


class ParalysisEffect(StatusEffect):
    """Paralysis status effect."""
    
    def __init__(self):
        super().__init__(StatusType.PARALYSIS.value)
        self.skip_chance = 0.25  # 25% chance to skip turn
    
    def apply_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """No turn damage for paralysis."""
        return ""
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """25% chance to prevent action."""
        if random.random() < self.skip_chance:
            return True
        return False
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Paralysis reduces Speed by 50%."""
        if stat_name == "speed":
            return 0.5
        return 1.0


class BurnEffect(StatusEffect):
    """Burn status effect."""
    
    def __init__(self):
        super().__init__(StatusType.BURN.value)
        self.damage_fraction = 1/16  # 1/16 max HP per turn
    
    def apply_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Apply burn damage."""
        damage = max(1, int(pokemon.max_hp * self.damage_fraction))
        pokemon.current_hp = max(0, pokemon.current_hp - damage)
        return f"{pokemon.name} is hurt by its burn! Lost {damage} HP."
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """Burn doesn't prevent actions."""
        return False
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Burn reduces Attack by 50%."""
        if stat_name == "attack":
            return 0.5
        return 1.0


class PoisonEffect(StatusEffect):
    """Poison status effect."""
    
    def __init__(self):
        super().__init__(StatusType.POISON.value)
        self.damage_fraction = 1/8  # 1/8 max HP per turn
    
    def apply_turn_effect(self, pokemon: 'BattlePokemon') -> str:
        """Apply poison damage."""
        damage = max(1, int(pokemon.max_hp * self.damage_fraction))
        pokemon.current_hp = max(0, pokemon.current_hp - damage)
        return f"{pokemon.name} is hurt by poison! Lost {damage} HP."
    
    def prevents_action(self, pokemon: 'BattlePokemon') -> bool:
        """Poison doesn't prevent actions."""
        return False
    
    def get_stat_modifier(self, stat_name: str) -> float:
        """Poison has no stat modifiers."""
        return 1.0


class StatusManager:
    """Manages status effects for Pokemon."""
    
    STATUS_EFFECTS = {
        StatusType.PARALYSIS.value: ParalysisEffect,
        StatusType.BURN.value: BurnEffect,
        StatusType.POISON.value: PoisonEffect,
    }
    
    def __init__(self):
        self.active_effects: Dict[str, StatusEffect] = {}
    
    def apply_status(self, pokemon: 'BattlePokemon', status_type: StatusType) -> str:
        """Apply a status effect to a Pokemon."""
        status_name = status_type.value
        
        # Check if Pokemon already has this status
        if status_name in self.active_effects:
            return f"{pokemon.name} is already {status_name}!"
        
        # Check type immunities
        if not self._can_apply_status(pokemon, status_type):
            return f"{pokemon.name} cannot be {status_name}!"
        
        # Apply the status effect
        effect = self.STATUS_EFFECTS[status_name]()
        self.active_effects[status_name] = effect
        
        return f"{pokemon.name} is now {status_name}!"
    
    def remove_status(self, pokemon: 'BattlePokemon', status_type: StatusType) -> str:
        """Remove a status effect from a Pokemon."""
        status_name = status_type.value
        
        if status_name not in self.active_effects:
            return f"{pokemon.name} is not {status_name}!"
        
        del self.active_effects[status_name]
        return f"{pokemon.name} is no longer {status_name}!"
    
    def process_turn_effects(self, pokemon: 'BattlePokemon') -> str:
        """Process all status effects for the turn."""
        messages = []
        effects_to_remove = []
        
        for status_name, effect in self.active_effects.items():
            # Apply turn effect
            message = effect.apply_turn_effect(pokemon)
            if message:
                messages.append(message)
            
            # Check if effect should be removed
            if effect.advance_turn():
                effects_to_remove.append(status_name)
        
        # Remove expired effects
        for status_name in effects_to_remove:
            del self.active_effects[status_name]
            messages.append(f"{pokemon.name} recovered from {status_name}!")
        
        return " ".join(messages)
    
    def can_act(self, pokemon: 'BattlePokemon') -> bool:
        """Check if Pokemon can act this turn."""
        for effect in self.active_effects.values():
            if effect.prevents_action(pokemon):
                return False
        return True
    
    def get_stat_multiplier(self, stat_name: str) -> float:
        """Get combined stat multiplier from all status effects."""
        multiplier = 1.0
        
        for effect in self.active_effects.values():
            multiplier *= effect.get_stat_modifier(stat_name)
        
        return multiplier
    
    def has_status(self, status_type: StatusType) -> bool:
        """Check if a specific status is active."""
        return status_type.value in self.active_effects
    
    def get_active_statuses(self) -> list:
        """Get list of all active status names."""
        return list(self.active_effects.keys())
    
    def _can_apply_status(self, pokemon: 'BattlePokemon', status_type: StatusType) -> bool:
        """Check if a status can be applied to a Pokemon."""
        # Electric types are immune to paralysis
        if (status_type == StatusType.PARALYSIS and 
            "electric" in pokemon.types):
            return False
        
        # Fire types are immune to burn
        if (status_type == StatusType.BURN and 
            "fire" in pokemon.types):
            return False
        
        # Poison and Steel types are immune to poison
        if (status_type == StatusType.POISON and 
            ("poison" in pokemon.types or "steel" in pokemon.types)):
            return False
        
        return True