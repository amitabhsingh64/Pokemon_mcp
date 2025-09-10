"""Battle simulation tool for MCP server."""

import random
import logging
from typing import Dict, Any, List
from fastapi import HTTPException
from dataclasses import dataclass

from ..utils.pokeapi_client import get_client, PokemonData
from ..utils.type_chart import (
    get_dual_type_effectiveness,
    calculate_stab_multiplier,
    get_effectiveness_description
)
from ..utils.status_effects import StatusManager, StatusType

logger = logging.getLogger(__name__)


@dataclass
class BattlePokemon:
    """Pokemon configured for battle."""
    name: str
    types: List[str]
    stats: Dict[str, int]
    level: int
    current_hp: int
    max_hp: int
    status_manager: StatusManager
    
    @property
    def is_fainted(self) -> bool:
        return self.current_hp <= 0
    
    def get_effective_stat(self, stat_name: str) -> int:
        """Get stat with level scaling and status modifiers."""
        base_stat = self.stats.get(stat_name, 50)
        
        if stat_name == "hp":
            return self.max_hp
        
        # Calculate stat at current level
        level_stat = int(((2 * base_stat * self.level) / 100) + 5)
        
        # Apply status modifiers
        modifier = self.status_manager.get_stat_multiplier(stat_name)
        return max(1, int(level_stat * modifier))


@dataclass 
class Move:
    """Simplified move for battles."""
    name: str
    type: str
    power: int
    accuracy: int
    damage_class: str  # physical or special


class BattleTool:
    """Battle simulation tool."""
    
    def __init__(self):
        # Basic move database for simulation
        self.moves = {
            "tackle": Move("tackle", "normal", 40, 100, "physical"),
            "scratch": Move("scratch", "normal", 40, 100, "physical"),
            "ember": Move("ember", "fire", 40, 100, "special"),
            "water-gun": Move("water-gun", "water", 40, 100, "special"),
            "vine-whip": Move("vine-whip", "grass", 45, 100, "physical"),
            "thundershock": Move("thundershock", "electric", 40, 100, "special"),
            "flamethrower": Move("flamethrower", "fire", 90, 100, "special"),
            "surf": Move("surf", "water", 90, 100, "special"),
            "earthquake": Move("earthquake", "ground", 100, 100, "physical"),
            "thunderbolt": Move("thunderbolt", "electric", 90, 100, "special"),
        }
    
    def _create_battle_pokemon(self, pokemon_data: PokemonData, level: int) -> BattlePokemon:
        """Create a battle-ready Pokemon."""
        # Calculate HP at level
        hp_stat = pokemon_data.stats.get("hp", 50)
        max_hp = int(((2 * hp_stat * level) / 100) + level + 10)
        
        return BattlePokemon(
            name=pokemon_data.name,
            types=pokemon_data.types,
            stats=pokemon_data.stats,
            level=level,
            current_hp=max_hp,
            max_hp=max_hp,
            status_manager=StatusManager()
        )
    
    def _select_move(self, pokemon: BattlePokemon) -> Move:
        """Select a random appropriate move for Pokemon."""
        # Try to match a move to Pokemon's type
        for move_name, move in self.moves.items():
            if move.type in pokemon.types:
                return move
        
        # Default to tackle
        return self.moves["tackle"]
    
    def _calculate_damage(self, attacker: BattlePokemon, defender: BattlePokemon, move: Move) -> Dict[str, Any]:
        """Calculate damage using Pokemon formula."""
        # Check accuracy
        if random.randint(1, 100) > move.accuracy:
            return {
                "damage": 0,
                "missed": True,
                "message": f"{attacker.name} used {move.name}, but it missed!"
            }
        
        # Get attack and defense stats
        if move.damage_class == "physical":
            attack = attacker.get_effective_stat("attack")
            defense = defender.get_effective_stat("defense")
        else:
            attack = attacker.get_effective_stat("special_attack")
            defense = defender.get_effective_stat("special_defense")
        
        # Base damage calculation
        level = attacker.level
        power = move.power
        
        # Core formula: (((2 × Level ÷ 5 + 2) × Power × A ÷ D) ÷ 50 + 2)
        base_damage = (((2 * level / 5 + 2) * power * attack / defense) / 50 + 2)
        
        # Apply modifiers
        stab_multiplier = calculate_stab_multiplier(move.type, attacker.types)
        type_effectiveness = get_dual_type_effectiveness(move.type, defender.types)
        
        # Critical hit (simplified)
        is_critical = random.randint(1, 24) == 1
        critical_multiplier = 1.5 if is_critical else 1.0
        
        # Random factor (85-100%)
        random_factor = random.randint(85, 100) / 100
        
        # Final damage
        final_damage = int(base_damage * stab_multiplier * type_effectiveness * critical_multiplier * random_factor)
        final_damage = max(1, final_damage)  # Minimum 1 damage
        
        # Create message
        message_parts = [f"{attacker.name} used {move.name}!"]
        
        if is_critical:
            message_parts.append("A critical hit!")
        
        effectiveness_msg = get_effectiveness_description(type_effectiveness)
        if effectiveness_msg:
            message_parts.append(f"It {effectiveness_msg}!")
        
        return {
            "damage": final_damage,
            "missed": False,
            "is_critical": is_critical,
            "type_effectiveness": type_effectiveness,
            "stab_applied": stab_multiplier > 1.0,
            "message": " ".join(message_parts)
        }
    
    def _get_turn_order(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> tuple:
        """Determine turn order based on speed."""
        speed1 = pokemon1.get_effective_stat("speed")
        speed2 = pokemon2.get_effective_stat("speed")
        
        if speed1 > speed2:
            return pokemon1, pokemon2
        elif speed2 > speed1:
            return pokemon2, pokemon1
        else:
            # Random on speed tie
            return random.choice([(pokemon1, pokemon2), (pokemon2, pokemon1)])
    
    async def simulate_battle(
        self,
        pokemon1_name: str,
        pokemon2_name: str,
        level: int = 50
    ) -> Dict[str, Any]:
        """Simulate a complete Pokemon battle."""
        try:
            # Validate level
            level = max(1, min(100, level))
            
            # Fetch Pokemon data
            async with await get_client() as client:
                pokemon1_data = await client.get_pokemon(pokemon1_name)
                pokemon2_data = await client.get_pokemon(pokemon2_name)
            
            # Create battle Pokemon
            pokemon1 = self._create_battle_pokemon(pokemon1_data, level)
            pokemon2 = self._create_battle_pokemon(pokemon2_data, level)
            
            # Battle log
            battle_log = []
            turn = 0
            max_turns = 50  # Prevent infinite battles
            
            battle_log.append({
                "turn": 0,
                "action": "battle_start",
                "message": f"Battle begins! {pokemon1.name} vs {pokemon2.name}!"
            })
            
            # Battle loop
            while not pokemon1.is_fainted and not pokemon2.is_fainted and turn < max_turns:
                turn += 1
                
                # Process status effects
                for pokemon in [pokemon1, pokemon2]:
                    if pokemon.status_manager.active_effects:
                        status_msg = pokemon.status_manager.process_turn_effects(pokemon)
                        if status_msg:
                            battle_log.append({
                                "turn": turn,
                                "action": "status_effect",
                                "message": status_msg
                            })
                
                # Check if anyone fainted from status
                if pokemon1.is_fainted or pokemon2.is_fainted:
                    break
                
                # Determine turn order
                first, second = self._get_turn_order(pokemon1, pokemon2)
                
                # First Pokemon's turn
                if not first.is_fainted and first.status_manager.can_act(first):
                    defender = pokemon2 if first == pokemon1 else pokemon1
                    move = self._select_move(first)
                    damage_result = self._calculate_damage(first, defender, move)
                    
                    if not damage_result["missed"]:
                        defender.current_hp = max(0, defender.current_hp - damage_result["damage"])
                        
                        battle_log.append({
                            "turn": turn,
                            "action": "attack",
                            "attacker": first.name,
                            "defender": defender.name,
                            "move": move.name,
                            "damage": damage_result["damage"],
                            "critical": damage_result["is_critical"],
                            "message": damage_result["message"]
                        })
                        
                        if defender.is_fainted:
                            battle_log.append({
                                "turn": turn,
                                "action": "faint",
                                "message": f"{defender.name} fainted!"
                            })
                            break
                    else:
                        battle_log.append({
                            "turn": turn,
                            "action": "miss",
                            "attacker": first.name,
                            "message": damage_result["message"]
                        })
                
                # Second Pokemon's turn (if still able)
                if not second.is_fainted and second.status_manager.can_act(second):
                    defender = pokemon1 if second == pokemon2 else pokemon2
                    if not defender.is_fainted:
                        move = self._select_move(second)
                        damage_result = self._calculate_damage(second, defender, move)
                        
                        if not damage_result["missed"]:
                            defender.current_hp = max(0, defender.current_hp - damage_result["damage"])
                            
                            battle_log.append({
                                "turn": turn,
                                "action": "attack",
                                "attacker": second.name,
                                "defender": defender.name,
                                "move": move.name,
                                "damage": damage_result["damage"],
                                "critical": damage_result["is_critical"],
                                "message": damage_result["message"]
                            })
                            
                            if defender.is_fainted:
                                battle_log.append({
                                    "turn": turn,
                                    "action": "faint",
                                    "message": f"{defender.name} fainted!"
                                })
                                break
                        else:
                            battle_log.append({
                                "turn": turn,
                                "action": "miss",
                                "attacker": second.name,
                                "message": damage_result["message"]
                            })
            
            # Determine winner
            if pokemon1.is_fainted and pokemon2.is_fainted:
                winner = "draw"
                loser = "draw"
            elif pokemon1.is_fainted:
                winner = pokemon2.name
                loser = pokemon1.name
            elif pokemon2.is_fainted:
                winner = pokemon1.name
                loser = pokemon2.name
            else:
                # Battle ended due to turn limit - winner has more HP%
                hp_pct1 = pokemon1.current_hp / pokemon1.max_hp
                hp_pct2 = pokemon2.current_hp / pokemon2.max_hp
                if hp_pct1 > hp_pct2:
                    winner = pokemon1.name
                    loser = pokemon2.name
                else:
                    winner = pokemon2.name
                    loser = pokemon1.name
            
            return {
                "battle_result": {
                    "winner": winner,
                    "loser": loser,
                    "total_turns": turn,
                    "battle_log": battle_log
                },
                "final_stats": {
                    pokemon1.name: {
                        "hp": pokemon1.current_hp,
                        "max_hp": pokemon1.max_hp,
                        "fainted": pokemon1.is_fainted
                    },
                    pokemon2.name: {
                        "hp": pokemon2.current_hp,
                        "max_hp": pokemon2.max_hp,
                        "fainted": pokemon2.is_fainted
                    }
                }
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Battle simulation failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def predict_battle(
        self,
        pokemon1_name: str,
        pokemon2_name: str,
        level: int = 50
    ) -> Dict[str, Any]:
        """Predict battle outcome without full simulation."""
        try:
            level = max(1, min(100, level))
            
            # Fetch Pokemon data
            async with await get_client() as client:
                pokemon1_data = await client.get_pokemon(pokemon1_name)
                pokemon2_data = await client.get_pokemon(pokemon2_name)
            
            # Create battle Pokemon for analysis
            pokemon1 = self._create_battle_pokemon(pokemon1_data, level)
            pokemon2 = self._create_battle_pokemon(pokemon2_data, level)
            
            # Analyze various factors
            factors = {
                "speed_advantage": self._analyze_speed_advantage(pokemon1, pokemon2),
                "offensive_advantage": self._analyze_offensive_advantage(pokemon1, pokemon2),
                "defensive_advantage": self._analyze_defensive_advantage(pokemon1, pokemon2),
                "type_advantage": self._analyze_type_advantage(pokemon1, pokemon2)
            }
            
            # Calculate prediction score
            p1_score = self._calculate_prediction_score(pokemon1, pokemon2, factors)
            p2_score = 100 - p1_score
            
            return {
                "prediction": {
                    "pokemon1": {
                        "name": pokemon1.name,
                        "win_chance": f"{p1_score}%",
                        "advantages": [k for k, v in factors.items() if v == pokemon1.name]
                    },
                    "pokemon2": {
                        "name": pokemon2.name,
                        "win_chance": f"{p2_score}%",
                        "advantages": [k for k, v in factors.items() if v == pokemon2.name]
                    },
                    "predicted_winner": pokemon1.name if p1_score > p2_score else pokemon2.name,
                    "confidence": "high" if abs(p1_score - p2_score) > 30 else "medium" if abs(p1_score - p2_score) > 15 else "low"
                },
                "analysis": factors
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Battle prediction failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def _analyze_speed_advantage(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
        """Analyze speed advantage."""
        speed1 = pokemon1.get_effective_stat("speed")
        speed2 = pokemon2.get_effective_stat("speed")
        
        if speed1 > speed2:
            return pokemon1.name
        elif speed2 > speed1:
            return pokemon2.name
        else:
            return "tie"
    
    def _analyze_offensive_advantage(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
        """Analyze offensive capability."""
        offense1 = pokemon1.get_effective_stat("attack") + pokemon1.get_effective_stat("special_attack")
        offense2 = pokemon2.get_effective_stat("attack") + pokemon2.get_effective_stat("special_attack")
        
        if offense1 > offense2:
            return pokemon1.name
        elif offense2 > offense1:
            return pokemon2.name
        else:
            return "tie"
    
    def _analyze_defensive_advantage(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
        """Analyze defensive capability."""
        defense1 = pokemon1.max_hp + pokemon1.get_effective_stat("defense") + pokemon1.get_effective_stat("special_defense")
        defense2 = pokemon2.max_hp + pokemon2.get_effective_stat("defense") + pokemon2.get_effective_stat("special_defense")
        
        if defense1 > defense2:
            return pokemon1.name
        elif defense2 > defense1:
            return pokemon2.name
        else:
            return "tie"
    
    def _analyze_type_advantage(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
        """Analyze type matchup."""
        # Get best type effectiveness for each Pokemon
        best_p1_effectiveness = 1.0
        best_p2_effectiveness = 1.0
        
        for type1 in pokemon1.types:
            effectiveness = get_dual_type_effectiveness(type1, pokemon2.types)
            best_p1_effectiveness = max(best_p1_effectiveness, effectiveness)
        
        for type2 in pokemon2.types:
            effectiveness = get_dual_type_effectiveness(type2, pokemon1.types)
            best_p2_effectiveness = max(best_p2_effectiveness, effectiveness)
        
        if best_p1_effectiveness > best_p2_effectiveness:
            return pokemon1.name
        elif best_p2_effectiveness > best_p1_effectiveness:
            return pokemon2.name
        else:
            return "neutral"
    
    def _calculate_prediction_score(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon, factors: Dict) -> int:
        """Calculate prediction score (0-100) for pokemon1."""
        base_score = 50
        
        # Each advantage is worth 10-15 points
        for factor, advantage in factors.items():
            if advantage == pokemon1.name:
                if factor == "type_advantage":
                    base_score += 15  # Type advantage is most important
                else:
                    base_score += 10
            elif advantage == pokemon2.name:
                if factor == "type_advantage":
                    base_score -= 15
                else:
                    base_score -= 10
        
        return max(5, min(95, base_score))