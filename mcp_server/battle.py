"""Enhanced Pokemon battle system with comprehensive mechanics."""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

from .utils.pokeapi_client import PokemonData
from .utils.status_effects import StatusManager, StatusType
from .utils.moves_database import Move, get_pokemon_moves, MoveCategory
from .utils.damage_calculator import DamageCalculator


class BattleState(Enum):
    """Battle states."""
    ACTIVE = "active"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class BattleTurn:
    """Represents a single battle turn."""
    turn_number: int
    pokemon1_action: str
    pokemon2_action: str
    pokemon1_move: Optional[Move]
    pokemon2_move: Optional[Move]
    damage_dealt: Dict[str, int]
    status_effects: List[str]
    turn_summary: str
    pokemon1_hp_after: int
    pokemon2_hp_after: int


class BattlePokemon:
    """Enhanced Pokemon class for battle with all mechanics."""
    
    def __init__(self, pokemon_data: PokemonData, level: int = 50):
        self.name = pokemon_data.name.capitalize()
        self.types = pokemon_data.types
        self.level = level
        self.pokemon_id = pokemon_data.id
        
        # Calculate stats at given level
        self.stats = self._calculate_stats(pokemon_data.stats, level)
        
        # HP management
        self.max_hp = self.stats["hp"]
        self.current_hp = self.max_hp
        
        # Status effects
        self.status_manager = StatusManager()
        
        # Moves (random selection from Pokemon's moveset)
        self.moves = get_pokemon_moves(pokemon_data.name, level, 4)
        
        # Battle state
        self.is_fainted = False
        
        # PP tracking for moves
        self.move_pp = {move.name: move.pp for move in self.moves}
    
    def _calculate_stats(self, base_stats: Dict[str, int], level: int) -> Dict[str, int]:
        """Calculate Pokemon stats at given level using official formula."""
        calculated_stats = {}
        
        # HP calculation: ((2 * Base + IV + (EV/4)) * Level / 100) + Level + 10
        # Using IV=31, EV=0 for simplicity
        hp_base = base_stats.get("hp", 45)
        calculated_stats["hp"] = int(((2 * hp_base + 31) * level / 100) + level + 10)
        
        # Other stats: ((2 * Base + IV + (EV/4)) * Level / 100) + 5
        for stat_name in ["attack", "defense", "special_attack", "special_defense", "speed"]:
            base_value = base_stats.get(stat_name, 45)
            calculated_stats[stat_name] = int(((2 * base_value + 31) * level / 100) + 5)
        
        return calculated_stats
    
    def get_effective_stat(self, stat_name: str) -> int:
        """Get stat modified by status effects."""
        base_stat = self.stats.get(stat_name, 0)
        modifier = self.status_manager.get_stat_multiplier(stat_name)
        return int(base_stat * modifier)
    
    def can_use_move(self, move: Move) -> bool:
        """Check if Pokemon can use a move."""
        if self.is_fainted:
            return False
        
        # Check PP
        if self.move_pp.get(move.name, 0) <= 0:
            return False
        
        # Check if status prevents action
        return self.status_manager.can_act(self)
    
    def use_move(self, move: Move) -> bool:
        """Use a move (decreases PP)."""
        if not self.can_use_move(move):
            return False
        
        self.move_pp[move.name] = max(0, self.move_pp[move.name] - 1)
        return True
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken."""
        actual_damage = min(damage, self.current_hp)
        self.current_hp = max(0, self.current_hp - actual_damage)
        
        if self.current_hp == 0:
            self.is_fainted = True
        
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal Pokemon and return actual healing done."""
        if self.is_fainted:
            return 0
        
        actual_healing = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual_healing
        return actual_healing
    
    def get_available_moves(self) -> List[Move]:
        """Get list of moves Pokemon can currently use."""
        return [move for move in self.moves if self.can_use_move(move)]
    
    def get_hp_percentage(self) -> float:
        """Get HP as percentage."""
        return (self.current_hp / self.max_hp) * 100 if self.max_hp > 0 else 0.0


class EnhancedBattleSimulator:
    """Comprehensive Pokemon battle simulator."""
    
    def __init__(self):
        self.battle_log: List[str] = []
        self.turn_history: List[BattleTurn] = []
        self.damage_calculator = DamageCalculator()
    
    async def simulate_battle(
        self,
        pokemon1_data: PokemonData,
        pokemon2_data: PokemonData,
        level: int = 50,
        max_turns: int = 100
    ) -> Dict[str, Any]:
        """Simulate a complete battle between two Pokemon."""
        
        # Initialize battle Pokemon
        pokemon1 = BattlePokemon(pokemon1_data, level)
        pokemon2 = BattlePokemon(pokemon2_data, level)
        
        self.battle_log = []
        self.turn_history = []
        
        # Battle setup log
        self._log(f"🔥 POKEMON BATTLE BEGINS! 🔥")
        self._log(f"{pokemon1.name} (Level {level}) vs {pokemon2.name} (Level {level})")
        self._log(f"{pokemon1.name}: {pokemon1.max_hp} HP, Types: {', '.join(pokemon1.types).title()}")
        self._log(f"{pokemon2.name}: {pokemon2.max_hp} HP, Types: {', '.join(pokemon2.types).title()}")
        self._log(f"")
        
        # Battle loop
        turn_number = 0
        battle_state = BattleState.ACTIVE
        
        while battle_state == BattleState.ACTIVE and turn_number < max_turns:
            turn_number += 1
            
            # Process turn
            turn_result = await self._process_turn(pokemon1, pokemon2, turn_number)
            self.turn_history.append(turn_result)
            
            # Check win conditions
            if pokemon1.is_fainted or pokemon2.is_fainted:
                battle_state = BattleState.FINISHED
            elif turn_number >= max_turns:
                battle_state = BattleState.FINISHED
                self._log("⏰ Battle timed out!")
        
        # Battle conclusion
        winner = self._determine_winner(pokemon1, pokemon2)
        
        # Comprehensive battle summary
        summary = self._generate_battle_summary(pokemon1, pokemon2, winner, turn_number)
        
        return {
            "winner": winner,
            "turns": turn_number,
            "battle_log": self.battle_log,
            "turn_history": [self._turn_to_dict(turn) for turn in self.turn_history],
            "final_stats": {
                pokemon1.name: {
                    "hp": pokemon1.current_hp,
                    "max_hp": pokemon1.max_hp,
                    "hp_percentage": pokemon1.get_hp_percentage(),
                    "status": pokemon1.status_manager.get_active_statuses(),
                    "is_fainted": pokemon1.is_fainted
                },
                pokemon2.name: {
                    "hp": pokemon2.current_hp,
                    "max_hp": pokemon2.max_hp,
                    "hp_percentage": pokemon2.get_hp_percentage(),
                    "status": pokemon2.status_manager.get_active_statuses(),
                    "is_fainted": pokemon2.is_fainted
                }
            },
            "summary": summary,
            "battle_mechanics": self._get_battle_mechanics_summary()
        }
    
    async def _process_turn(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon, turn_number: int) -> BattleTurn:
        """Process a complete battle turn."""
        self._log(f"🔄 Turn {turn_number}")
        
        # Status effects at start of turn
        status_messages = []
        
        # Process status effects for both Pokemon
        for pokemon in [pokemon1, pokemon2]:
            status_msg = pokemon.status_manager.process_turn_effects(pokemon)
            if status_msg:
                status_messages.append(status_msg)
                self._log(f"   {status_msg}")
        
        # Determine move order based on priority and speed
        actions = self._determine_move_order(pokemon1, pokemon2)
        
        damage_dealt = {pokemon1.name: 0, pokemon2.name: 0}
        pokemon1_action = "No action"
        pokemon2_action = "No action"
        pokemon1_move = None
        pokemon2_move = None
        
        # Execute moves in order
        for attacker, defender, is_first_pokemon in actions:
            if attacker.is_fainted:
                continue
            
            # Select random move from available moves
            available_moves = attacker.get_available_moves()
            if not available_moves:
                action = f"{attacker.name} has no available moves!"
                self._log(f"   {action}")
                continue
            
            selected_move = random.choice(available_moves)
            
            # Check if Pokemon can act (not prevented by status)
            if not attacker.status_manager.can_act(attacker):
                action = f"{attacker.name} is unable to move!"
                self._log(f"   {action}")
                
                if is_first_pokemon:
                    pokemon1_action = action
                else:
                    pokemon2_action = action
                continue
            
            # Use the move
            if attacker.use_move(selected_move):
                # Calculate damage and effects
                move_result = await self._execute_move(attacker, defender, selected_move)
                
                action = move_result["description"]
                self._log(f"   {action}")
                
                # Track damage
                damage_dealt[defender.name] += move_result["damage"]
                
                # Apply status effects if any
                if move_result.get("status_applied"):
                    status_messages.append(move_result["status_message"])
                    self._log(f"   {move_result['status_message']}")
                
                # Store move info
                if is_first_pokemon:
                    pokemon1_action = action
                    pokemon1_move = selected_move
                else:
                    pokemon2_action = action
                    pokemon2_move = selected_move
        
        turn_summary = f"Turn {turn_number}: {pokemon1.name} {pokemon1.current_hp}/{pokemon1.max_hp} HP, {pokemon2.name} {pokemon2.current_hp}/{pokemon2.max_hp} HP"
        self._log("")
        
        return BattleTurn(
            turn_number=turn_number,
            pokemon1_action=pokemon1_action,
            pokemon2_action=pokemon2_action,
            pokemon1_move=pokemon1_move,
            pokemon2_move=pokemon2_move,
            damage_dealt=damage_dealt,
            status_effects=status_messages,
            turn_summary=turn_summary,
            pokemon1_hp_after=pokemon1.current_hp,
            pokemon2_hp_after=pokemon2.current_hp
        )
    
    def _determine_move_order(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> List[Tuple]:
        """Determine move order based on priority and speed."""
        # For now, randomly select moves to determine priority
        p1_moves = pokemon1.get_available_moves()
        p2_moves = pokemon2.get_available_moves()
        
        p1_priority = 0
        p2_priority = 0
        
        if p1_moves:
            p1_priority = random.choice(p1_moves).priority
        if p2_moves:
            p2_priority = random.choice(p2_moves).priority
        
        # Higher priority goes first
        if p1_priority > p2_priority:
            return [(pokemon1, pokemon2, True), (pokemon2, pokemon1, False)]
        elif p2_priority > p1_priority:
            return [(pokemon2, pokemon1, False), (pokemon1, pokemon2, True)]
        else:
            # Same priority - check speed
            p1_speed = pokemon1.get_effective_stat("speed")
            p2_speed = pokemon2.get_effective_stat("speed")
            
            if p1_speed > p2_speed:
                return [(pokemon1, pokemon2, True), (pokemon2, pokemon1, False)]
            elif p2_speed > p1_speed:
                return [(pokemon2, pokemon1, False), (pokemon1, pokemon2, True)]
            else:
                # Same speed - random order
                if random.choice([True, False]):
                    return [(pokemon1, pokemon2, True), (pokemon2, pokemon1, False)]
                else:
                    return [(pokemon2, pokemon1, False), (pokemon1, pokemon2, True)]
    
    async def _execute_move(self, attacker: BattlePokemon, defender: BattlePokemon, move: Move) -> Dict[str, Any]:
        """Execute a move and return results."""
        result = {
            "damage": 0,
            "description": "",
            "status_applied": False,
            "status_message": "",
            "effectiveness": 1.0
        }
        
        # Miss calculation
        if random.randint(1, 100) > move.accuracy:
            result["description"] = f"{attacker.name} used {move.name}, but it missed!"
            return result
        
        if move.category == MoveCategory.STATUS:
            # Status moves
            if move.status_effect:
                status_msg = defender.status_manager.apply_status(defender, move.status_effect)
                result["status_applied"] = True
                result["status_message"] = status_msg
                result["description"] = f"{attacker.name} used {move.name}!"
            else:
                result["description"] = f"{attacker.name} used {move.name}!"
        else:
            # Damage calculation
            damage_result = self.damage_calculator.calculate_damage(attacker, defender, move)
            damage = damage_result["damage"]
            
            # Apply damage
            actual_damage = defender.take_damage(damage)
            result["damage"] = actual_damage
            result["effectiveness"] = damage_result["effectiveness"]
            
            # Build description
            description = f"{attacker.name} used {move.name}!"
            if actual_damage > 0:
                description += f" It dealt {actual_damage} damage."
                
                # Add effectiveness text
                effectiveness_text = self.damage_calculator._get_effectiveness_text(damage_result["effectiveness"])
                if effectiveness_text:
                    description += f" {effectiveness_text}"
                
                # Critical hit
                if damage_result["is_critical"]:
                    description += " Critical hit!"
                    
                # STAB
                if damage_result["stab"] > 1.0:
                    description += " (STAB)"
            
            result["description"] = description
            
            # Status effect chance
            if move.status_effect and move.status_chance > 0:
                if random.random() < move.status_chance:
                    status_msg = defender.status_manager.apply_status(defender, move.status_effect)
                    result["status_applied"] = True
                    result["status_message"] = status_msg
        
        return result
    
    def _determine_winner(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
        """Determine battle winner."""
        if pokemon1.is_fainted and pokemon2.is_fainted:
            return "Draw"
        elif pokemon1.is_fainted:
            return pokemon2.name
        elif pokemon2.is_fainted:
            return pokemon1.name
        else:
            # Battle didn't end in knockout - determine by HP percentage
            p1_hp_percent = pokemon1.get_hp_percentage()
            p2_hp_percent = pokemon2.get_hp_percentage()
            
            if p1_hp_percent > p2_hp_percent:
                return pokemon1.name
            elif p2_hp_percent > p1_hp_percent:
                return pokemon2.name
            else:
                return "Draw"
    
    def _generate_battle_summary(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon, winner: str, turns: int) -> str:
        """Generate comprehensive battle summary."""
        summary_lines = []
        summary_lines.append("🏆 BATTLE RESULTS 🏆")
        summary_lines.append(f"Winner: {winner}")
        summary_lines.append(f"Turns: {turns}")
        summary_lines.append("")
        
        summary_lines.append("📊 Final Stats:")
        for pokemon in [pokemon1, pokemon2]:
            status_text = ""
            if pokemon.status_manager.get_active_statuses():
                status_text = f" ({', '.join(pokemon.status_manager.get_active_statuses()).title()})"
            
            if pokemon.is_fainted:
                summary_lines.append(f"• {pokemon.name}: Fainted{status_text}")
            else:
                hp_percent = pokemon.get_hp_percentage()
                summary_lines.append(f"• {pokemon.name}: {pokemon.current_hp}/{pokemon.max_hp} HP ({hp_percent:.1f}%){status_text}")
        
        summary_lines.append("")
        summary_lines.append("📜 Battle Highlights:")
        
        # Show key moments from battle
        for turn in self.turn_history[-3:]:  # Last 3 turns
            if turn.pokemon1_move:
                summary_lines.append(f"• Turn {turn.turn_number}: {turn.pokemon1_action}")
            if turn.pokemon2_move:
                summary_lines.append(f"• Turn {turn.turn_number}: {turn.pokemon2_action}")
        
        return "\n".join(summary_lines)
    
    def _get_battle_mechanics_summary(self) -> Dict[str, Any]:
        """Get summary of battle mechanics used."""
        return {
            "features_implemented": [
                "Official damage calculation formula",
                "Type effectiveness system (18 types)",
                "Status effects (Paralysis, Burn, Poison, Freeze, Sleep)",
                "STAB (Same Type Attack Bonus)",
                "Critical hits with proper rates",
                "Speed-based turn order",
                "Move priority system",
                "Accuracy and miss calculations",
                "PP (Power Points) tracking",
                "Type immunities for status effects",
                "Random move selection per turn",
                "Pokemon-specific movesets"
            ],
            "status_effects_available": [
                "Paralysis (25% skip chance, -50% speed)",
                "Burn (1/16 HP damage, -50% attack)",
                "Poison (1/8 HP damage)",
                "Freeze (prevents action, 20% thaw chance)",
                "Sleep (prevents action, 1-3 turns duration)"
            ],
            "damage_formula": "((2×Level÷5+2)×Power×A÷D)÷50+2) × Modifiers"
        }
    
    def _turn_to_dict(self, turn: BattleTurn) -> Dict[str, Any]:
        """Convert BattleTurn to dictionary."""
        return {
            "turn_number": turn.turn_number,
            "pokemon1_action": turn.pokemon1_action,
            "pokemon2_action": turn.pokemon2_action,
            "pokemon1_move": turn.pokemon1_move.name if turn.pokemon1_move else None,
            "pokemon2_move": turn.pokemon2_move.name if turn.pokemon2_move else None,
            "damage_dealt": turn.damage_dealt,
            "status_effects": turn.status_effects,
            "turn_summary": turn.turn_summary,
            "pokemon1_hp_after": turn.pokemon1_hp_after,
            "pokemon2_hp_after": turn.pokemon2_hp_after
        }
    
    def _log(self, message: str):
        """Add message to battle log."""
        self.battle_log.append(message)