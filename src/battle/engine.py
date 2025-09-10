import random
import asyncio
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from enum import Enum

from ..models.pokemon import BattlePokemon, BattleLog, BattleResult, MoveDetails
from .calculator import DamageCalculator, DamageResult
from .status import StatusManager, StatusType
from .types import PokemonTypes

if TYPE_CHECKING:
    from ..services.pokeapi import PokeAPIClient


class BattleState(Enum):
    """Battle state enumeration"""
    SETUP = "setup"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class BattleEngine:
    """Core battle simulation engine"""
    
    def __init__(self):
        self.damage_calculator = DamageCalculator()
        self.type_system = PokemonTypes()
        self.state = BattleState.SETUP
        self.turn_counter = 0
        self.battle_log: List[BattleLog] = []
        self.max_turns = 100  # Prevent infinite battles
        
        # Battle participants
        self.pokemon1: Optional[BattlePokemon] = None
        self.pokemon2: Optional[BattlePokemon] = None
        
        # Status managers for each Pokemon
        self.status_manager1 = StatusManager()
        self.status_manager2 = StatusManager()
        
        # Battle conditions
        self.weather: Optional[str] = None
        self.terrain: Optional[str] = None
    
    def setup_battle(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> None:
        """
        Set up the battle with two Pokemon
        
        Args:
            pokemon1: First Pokemon
            pokemon2: Second Pokemon
        """
        self.pokemon1 = pokemon1
        self.pokemon2 = pokemon2
        self.state = BattleState.SETUP
        self.turn_counter = 0
        self.battle_log.clear()
        
        # Log battle start
        self._log_action(
            action="battle_start",
            attacker=pokemon1.pokemon.name,
            defender=pokemon2.pokemon.name,
            message=f"Battle begins! {pokemon1.pokemon.name} vs {pokemon2.pokemon.name}!"
        )
    
    async def simulate_battle(
        self,
        pokemon1: BattlePokemon,
        pokemon2: BattlePokemon,
        ai_strategy: str = "random"
    ) -> BattleResult:
        """
        Simulate a complete battle between two Pokemon
        
        Args:
            pokemon1: First Pokemon
            pokemon2: Second Pokemon  
            ai_strategy: AI strategy for move selection
            
        Returns:
            Complete battle result
        """
        self.setup_battle(pokemon1, pokemon2)
        self.state = BattleState.IN_PROGRESS
        
        while (self.state == BattleState.IN_PROGRESS and 
               self.turn_counter < self.max_turns and
               not pokemon1.is_fainted and 
               not pokemon2.is_fainted):
            
            await self._execute_turn(ai_strategy)
        
        # Determine winner
        winner, loser = self._determine_winner()
        self.state = BattleState.FINISHED
        
        return BattleResult(
            winner=winner.pokemon.name,
            loser=loser.pokemon.name,
            total_turns=self.turn_counter,
            battle_log=self.battle_log.copy(),
            final_stats={
                pokemon1.pokemon.name: {
                    "hp": pokemon1.current_hp,
                    "max_hp": pokemon1.max_hp,
                    "status_effects": pokemon1.status_effects.copy(),
                    "fainted": pokemon1.is_fainted
                },
                pokemon2.pokemon.name: {
                    "hp": pokemon2.current_hp,
                    "max_hp": pokemon2.max_hp,
                    "status_effects": pokemon2.status_effects.copy(),
                    "fainted": pokemon2.is_fainted
                }
            }
        )
    
    async def _execute_turn(self, ai_strategy: str = "random") -> None:
        """Execute a single battle turn"""
        self.turn_counter += 1
        
        # Process start-of-turn status effects
        await self._process_start_of_turn_effects()
        
        # Determine turn order
        first_pokemon, second_pokemon = self.damage_calculator.get_turn_order(
            self.pokemon1, self.pokemon2
        )
        
        # Execute actions in order
        if not first_pokemon.is_fainted and not second_pokemon.is_fainted:
            await self._execute_pokemon_action(first_pokemon, second_pokemon, ai_strategy)
        
        if not first_pokemon.is_fainted and not second_pokemon.is_fainted:
            await self._execute_pokemon_action(second_pokemon, first_pokemon, ai_strategy)
        
        # Process end-of-turn status effects
        await self._process_end_of_turn_effects()
        
        # Check for battle end
        if self.pokemon1.is_fainted or self.pokemon2.is_fainted:
            self.state = BattleState.FINISHED
    
    async def _execute_pokemon_action(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        ai_strategy: str
    ) -> None:
        """Execute a Pokemon's action for the turn"""
        # Check if Pokemon can act (not prevented by status)
        status_manager = self._get_status_manager(attacker)
        
        if not status_manager.can_act(attacker):
            self._log_action(
                action="skip_turn",
                attacker=attacker.pokemon.name,
                defender=defender.pokemon.name,
                message=f"{attacker.pokemon.name} cannot move this turn!"
            )
            return
        
        # Select move
        move = await self._select_move(attacker, ai_strategy)
        
        if not move:
            self._log_action(
                action="no_move",
                attacker=attacker.pokemon.name,
                defender=defender.pokemon.name,
                message=f"{attacker.pokemon.name} has no available moves!"
            )
            return
        
        # Use move
        await self._use_move(attacker, defender, move)
    
    async def _select_move(self, pokemon: BattlePokemon, strategy: str = "random") -> Optional[MoveDetails]:
        """
        Select a move for the Pokemon to use
        
        Args:
            pokemon: Pokemon selecting move
            strategy: Selection strategy
            
        Returns:
            Selected move or None if no moves available
        """
        # Get available moves (level-up moves only for simplicity)
        available_moves = [
            move for move in pokemon.pokemon.moves 
            if move.level_learned <= pokemon.level
        ]
        
        if not available_moves:
            return None
        
        if strategy == "random":
            selected_move_info = random.choice(available_moves)
        else:
            # Default to first available move
            selected_move_info = available_moves[0]
        
        # Create a basic move details object
        # In a full implementation, this would fetch from PokeAPI
        return self._create_basic_move_details(selected_move_info.name)
    
    def _create_basic_move_details(self, move_name: str) -> MoveDetails:
        """
        Create basic move details for common moves
        This is a simplified version - in production, would fetch from PokeAPI
        """
        # Basic move database for common moves
        move_data = {
            "tackle": {"power": 40, "accuracy": 100, "type": "normal", "damage_class": "physical"},
            "scratch": {"power": 40, "accuracy": 100, "type": "normal", "damage_class": "physical"},
            "ember": {"power": 40, "accuracy": 100, "type": "fire", "damage_class": "special"},
            "water-gun": {"power": 40, "accuracy": 100, "type": "water", "damage_class": "special"},
            "vine-whip": {"power": 45, "accuracy": 100, "type": "grass", "damage_class": "physical"},
            "thundershock": {"power": 40, "accuracy": 100, "type": "electric", "damage_class": "special"},
            "flamethrower": {"power": 90, "accuracy": 100, "type": "fire", "damage_class": "special"},
            "surf": {"power": 90, "accuracy": 100, "type": "water", "damage_class": "special"},
            "earthquake": {"power": 100, "accuracy": 100, "type": "ground", "damage_class": "physical"},
            "thunderbolt": {"power": 90, "accuracy": 100, "type": "electric", "damage_class": "special"},
            "ice-beam": {"power": 90, "accuracy": 100, "type": "ice", "damage_class": "special"},
            "psychic": {"power": 90, "accuracy": 100, "type": "psychic", "damage_class": "special"},
            "shadow-ball": {"power": 80, "accuracy": 100, "type": "ghost", "damage_class": "special"},
            "hyper-beam": {"power": 150, "accuracy": 90, "type": "normal", "damage_class": "special"},
        }
        
        # Default move if not in database
        default_data = {"power": 50, "accuracy": 100, "type": "normal", "damage_class": "physical"}
        data = move_data.get(move_name, default_data)
        
        return MoveDetails(
            name=move_name,
            power=data["power"],
            accuracy=data["accuracy"],
            pp=10,  # Default PP
            priority=0,
            damage_class=data["damage_class"],
            type=data["type"],
            target="normal",
            effect_chance=None,
            effect_entries=[]
        )
    
    async def _use_move(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move: MoveDetails
    ) -> None:
        """Execute a move"""
        # Check move accuracy
        if not self._check_move_accuracy(move):
            self._log_action(
                action="miss",
                attacker=attacker.pokemon.name,
                defender=defender.pokemon.name,
                move_used=move.name,
                message=f"{attacker.pokemon.name} used {move.name}, but it missed!"
            )
            return
        
        # Calculate damage
        damage_result = self.damage_calculator.calculate_damage(
            attacker, defender, move, self.weather, self.terrain
        )
        
        # Apply damage
        if damage_result.damage > 0:
            defender.current_hp = max(0, defender.current_hp - damage_result.damage)
        
        # Create log entry
        effectiveness_msg = damage_result.effectiveness_message
        critical_msg = damage_result.critical_message
        
        message_parts = [f"{attacker.pokemon.name} used {move.name}!"]
        
        if damage_result.damage > 0:
            message_parts.append(f"It dealt {damage_result.damage} damage.")
        
        if critical_msg:
            message_parts.append(critical_msg)
        
        if effectiveness_msg:
            message_parts.append(effectiveness_msg)
        
        if defender.is_fainted:
            message_parts.append(f"{defender.pokemon.name} fainted!")
        
        self._log_action(
            action="attack",
            attacker=attacker.pokemon.name,
            defender=defender.pokemon.name,
            move_used=move.name,
            damage=damage_result.damage,
            effectiveness=self.type_system.get_effectiveness_description(damage_result.type_effectiveness),
            critical_hit=damage_result.is_critical,
            message=" ".join(message_parts)
        )
        
        # Apply status effects (simplified)
        await self._apply_move_status_effects(attacker, defender, move)
    
    def _check_move_accuracy(self, move: MoveDetails) -> bool:
        """Check if move hits based on accuracy"""
        if move.accuracy is None:
            return True  # Moves like Swift always hit
        
        return random.randint(1, 100) <= move.accuracy
    
    async def _apply_move_status_effects(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move: MoveDetails
    ) -> None:
        """Apply status effects from moves (simplified implementation)"""
        # Basic status effect chances for some moves
        status_moves = {
            "thundershock": (StatusType.PARALYSIS, 0.1),
            "thunderbolt": (StatusType.PARALYSIS, 0.1),
            "flamethrower": (StatusType.BURN, 0.1),
            "ember": (StatusType.BURN, 0.1),
            "poison-sting": (StatusType.POISON, 0.3),
        }
        
        if move.name in status_moves:
            status_type, chance = status_moves[move.name]
            if random.random() < chance:
                status_manager = self._get_status_manager(defender)
                message = status_manager.apply_status(defender, status_type)
                if "now" in message:  # Status was successfully applied
                    self._log_action(
                        action="status_applied",
                        attacker=attacker.pokemon.name,
                        defender=defender.pokemon.name,
                        status_applied=status_type.value,
                        message=message
                    )
    
    async def _process_start_of_turn_effects(self) -> None:
        """Process status effects at start of turn"""
        for pokemon, status_manager in [(self.pokemon1, self.status_manager1), 
                                       (self.pokemon2, self.status_manager2)]:
            messages = status_manager.process_start_turn_effects(pokemon)
            for message in messages:
                self._log_action(
                    action="status_effect",
                    attacker=pokemon.pokemon.name,
                    defender="",
                    message=message
                )
    
    async def _process_end_of_turn_effects(self) -> None:
        """Process status effects at end of turn"""
        for pokemon, status_manager in [(self.pokemon1, self.status_manager1),
                                       (self.pokemon2, self.status_manager2)]:
            messages = status_manager.process_end_turn_effects(pokemon)
            for message in messages:
                self._log_action(
                    action="status_damage",
                    attacker=pokemon.pokemon.name,
                    defender="",
                    message=message
                )
                
                if pokemon.is_fainted:
                    self._log_action(
                        action="faint",
                        attacker=pokemon.pokemon.name,
                        defender="",
                        message=f"{pokemon.pokemon.name} fainted from status effects!"
                    )
    
    def _get_status_manager(self, pokemon: BattlePokemon) -> StatusManager:
        """Get the status manager for a specific Pokemon"""
        if pokemon == self.pokemon1:
            return self.status_manager1
        else:
            return self.status_manager2
    
    def _determine_winner(self) -> Tuple[BattlePokemon, BattlePokemon]:
        """Determine battle winner and loser"""
        if self.pokemon1.is_fainted and self.pokemon2.is_fainted:
            # Both fainted - winner is whoever has more HP percentage
            hp_pct1 = self.pokemon1.hp_percentage
            hp_pct2 = self.pokemon2.hp_percentage
            if hp_pct1 >= hp_pct2:
                return self.pokemon1, self.pokemon2
            else:
                return self.pokemon2, self.pokemon1
        elif self.pokemon1.is_fainted:
            return self.pokemon2, self.pokemon1
        elif self.pokemon2.is_fainted:
            return self.pokemon1, self.pokemon2
        else:
            # Battle ended due to turn limit - winner has higher HP percentage
            hp_pct1 = self.pokemon1.hp_percentage
            hp_pct2 = self.pokemon2.hp_percentage
            if hp_pct1 >= hp_pct2:
                return self.pokemon1, self.pokemon2
            else:
                return self.pokemon2, self.pokemon1
    
    def _log_action(
        self,
        action: str,
        attacker: str,
        defender: str,
        move_used: Optional[str] = None,
        damage: Optional[int] = None,
        effectiveness: Optional[str] = None,
        critical_hit: bool = False,
        status_applied: Optional[str] = None,
        message: str = ""
    ) -> None:
        """Add entry to battle log"""
        log_entry = BattleLog(
            turn=self.turn_counter,
            action=action,
            attacker=attacker,
            defender=defender,
            move_used=move_used,
            damage=damage,
            effectiveness=effectiveness,
            critical_hit=critical_hit,
            status_applied=status_applied,
            message=message
        )
        
        self.battle_log.append(log_entry)
    
    def get_battle_state(self) -> Dict:
        """Get current battle state"""
        return {
            "state": self.state.value,
            "turn": self.turn_counter,
            "pokemon1": {
                "name": self.pokemon1.pokemon.name if self.pokemon1 else None,
                "hp": self.pokemon1.current_hp if self.pokemon1 else 0,
                "max_hp": self.pokemon1.max_hp if self.pokemon1 else 0,
                "status": self.pokemon1.status_effects if self.pokemon1 else [],
                "fainted": self.pokemon1.is_fainted if self.pokemon1 else False
            },
            "pokemon2": {
                "name": self.pokemon2.pokemon.name if self.pokemon2 else None,
                "hp": self.pokemon2.current_hp if self.pokemon2 else 0,
                "max_hp": self.pokemon2.max_hp if self.pokemon2 else 0,
                "status": self.pokemon2.status_effects if self.pokemon2 else [],
                "fainted": self.pokemon2.is_fainted if self.pokemon2 else False
            },
            "weather": self.weather,
            "terrain": self.terrain
        }
    
    def reset_battle(self) -> None:
        """Reset battle state for new battle"""
        self.state = BattleState.SETUP
        self.turn_counter = 0
        self.battle_log.clear()
        self.pokemon1 = None
        self.pokemon2 = None
        self.status_manager1 = StatusManager()
        self.status_manager2 = StatusManager()
        self.weather = None
        self.terrain = None