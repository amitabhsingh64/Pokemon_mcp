"""Enhanced Pokemon battle simulation tool for MCP server."""

from typing import Dict, Any
import logging

from ..utils.pokeapi_client import get_client
from ..battle import EnhancedBattleSimulator

logger = logging.getLogger(__name__)


class BattleTool:
    """Enhanced battle simulation tool with comprehensive mechanics."""
    
    def __init__(self):
        self.battle_simulator = EnhancedBattleSimulator()
    
    async def simulate_battle(
        self,
        pokemon1_name: str,
        pokemon2_name: str,
        level: int = 50
    ) -> Dict[str, Any]:
        """Simulate a comprehensive Pokemon battle."""
        try:
            # Validate level
            level = max(1, min(100, level))
            
            # Fetch Pokemon data
            async with await get_client() as client:
                pokemon1_data = await client.get_pokemon(pokemon1_name)
                pokemon2_data = await client.get_pokemon(pokemon2_name)
            
            # Run enhanced battle simulation
            battle_result = await self.battle_simulator.simulate_battle(
                pokemon1_data, pokemon2_data, level
            )
            
            return battle_result
            
        except ValueError as e:
            logger.error(f"Pokemon not found: {e}")
            return {
                "error": f"Pokemon not found: {e}",
                "suggestion": "Please check the spelling and try again"
            }
        except Exception as e:
            logger.error(f"Battle simulation failed: {e}")
            return {
                "error": "Battle simulation failed",
                "details": str(e)
            }
    
    async def predict_battle(
        self,
        pokemon1_name: str,
        pokemon2_name: str,
        level: int = 50
    ) -> Dict[str, Any]:
        """Quick battle prediction without full simulation."""
        try:
            # Validate level
            level = max(1, min(100, level))
            
            # Fetch Pokemon data
            async with await get_client() as client:
                pokemon1_data = await client.get_pokemon(pokemon1_name)
                pokemon2_data = await client.get_pokemon(pokemon2_name)
            
            # Create temporary battle Pokemon for analysis
            from ..battle import BattlePokemon
            pokemon1 = BattlePokemon(pokemon1_data, level)
            pokemon2 = BattlePokemon(pokemon2_data, level)
            
            # Analyze factors
            factors = {
                "speed_advantage": self._analyze_speed(pokemon1, pokemon2),
                "offensive_power": self._analyze_offense(pokemon1, pokemon2),
                "defensive_bulk": self._analyze_defense(pokemon1, pokemon2),
                "type_matchup": self._analyze_types(pokemon1, pokemon2),
                "stat_total": self._analyze_stats(pokemon1, pokemon2)
            }
            
            # Calculate win probability
            p1_score = self._calculate_win_probability(pokemon1, pokemon2, factors)
            p2_score = 100 - p1_score
            
            # Determine predicted winner
            predicted_winner = pokemon1.name if p1_score > p2_score else pokemon2.name
            confidence = self._get_confidence_level(abs(p1_score - p2_score))
            
            return {
                "prediction": {
                    "winner": predicted_winner,
                    "confidence": confidence,
                    "win_probabilities": {
                        pokemon1.name: f"{p1_score:.1f}%",
                        pokemon2.name: f"{p2_score:.1f}%"
                    }
                },
                "analysis": {
                    "factors": factors,
                    "key_advantages": {
                        pokemon1.name: [k for k, v in factors.items() if v == pokemon1.name],
                        pokemon2.name: [k for k, v in factors.items() if v == pokemon2.name]
                    }
                },
                "pokemon_stats": {
                    pokemon1.name: {
                        "level": level,
                        "types": pokemon1.types,
                        "hp": pokemon1.max_hp,
                        "attack": pokemon1.get_effective_stat("attack"),
                        "defense": pokemon1.get_effective_stat("defense"),
                        "special_attack": pokemon1.get_effective_stat("special_attack"),
                        "special_defense": pokemon1.get_effective_stat("special_defense"),
                        "speed": pokemon1.get_effective_stat("speed")
                    },
                    pokemon2.name: {
                        "level": level,
                        "types": pokemon2.types,
                        "hp": pokemon2.max_hp,
                        "attack": pokemon2.get_effective_stat("attack"),
                        "defense": pokemon2.get_effective_stat("defense"),
                        "special_attack": pokemon2.get_effective_stat("special_attack"),
                        "special_defense": pokemon2.get_effective_stat("special_defense"),
                        "speed": pokemon2.get_effective_stat("speed")
                    }
                }
            }
            
        except ValueError as e:
            logger.error(f"Pokemon not found: {e}")
            return {
                "error": f"Pokemon not found: {e}",
                "suggestion": "Please check the spelling and try again"
            }
        except Exception as e:
            logger.error(f"Battle prediction failed: {e}")
            return {
                "error": "Battle prediction failed",
                "details": str(e)
            }
    
    def _analyze_speed(self, pokemon1, pokemon2) -> str:
        """Analyze speed advantage."""
        speed1 = pokemon1.get_effective_stat("speed")
        speed2 = pokemon2.get_effective_stat("speed")
        
        if speed1 > speed2:
            return pokemon1.name
        elif speed2 > speed1:
            return pokemon2.name
        else:
            return "tied"
    
    def _analyze_offense(self, pokemon1, pokemon2) -> str:
        """Analyze offensive capabilities."""
        offense1 = pokemon1.get_effective_stat("attack") + pokemon1.get_effective_stat("special_attack")
        offense2 = pokemon2.get_effective_stat("attack") + pokemon2.get_effective_stat("special_attack")
        
        if offense1 > offense2:
            return pokemon1.name
        elif offense2 > offense1:
            return pokemon2.name
        else:
            return "tied"
    
    def _analyze_defense(self, pokemon1, pokemon2) -> str:
        """Analyze defensive capabilities."""
        defense1 = pokemon1.max_hp + pokemon1.get_effective_stat("defense") + pokemon1.get_effective_stat("special_defense")
        defense2 = pokemon2.max_hp + pokemon2.get_effective_stat("defense") + pokemon2.get_effective_stat("special_defense")
        
        if defense1 > defense2:
            return pokemon1.name
        elif defense2 > defense1:
            return pokemon2.name
        else:
            return "tied"
    
    def _analyze_types(self, pokemon1, pokemon2) -> str:
        """Analyze type matchup advantages."""
        from ..utils.type_chart import get_dual_type_effectiveness
        
        # Calculate best type effectiveness for each Pokemon
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
    
    def _analyze_stats(self, pokemon1, pokemon2) -> str:
        """Analyze overall stat totals."""
        stats1 = sum([
            pokemon1.max_hp,
            pokemon1.get_effective_stat("attack"),
            pokemon1.get_effective_stat("defense"),
            pokemon1.get_effective_stat("special_attack"),
            pokemon1.get_effective_stat("special_defense"),
            pokemon1.get_effective_stat("speed")
        ])
        
        stats2 = sum([
            pokemon2.max_hp,
            pokemon2.get_effective_stat("attack"),
            pokemon2.get_effective_stat("defense"),
            pokemon2.get_effective_stat("special_attack"),
            pokemon2.get_effective_stat("special_defense"),
            pokemon2.get_effective_stat("speed")
        ])
        
        if stats1 > stats2:
            return pokemon1.name
        elif stats2 > stats1:
            return pokemon2.name
        else:
            return "tied"
    
    def _calculate_win_probability(self, pokemon1, pokemon2, factors: Dict[str, str]) -> float:
        """Calculate win probability for pokemon1 (0-100)."""
        base_score = 50.0
        
        # Weight different factors
        factor_weights = {
            "speed_advantage": 10.0,
            "offensive_power": 15.0,
            "defensive_bulk": 12.0,
            "type_matchup": 18.0,  # Most important
            "stat_total": 8.0
        }
        
        for factor, winner in factors.items():
            weight = factor_weights.get(factor, 10.0)
            if winner == pokemon1.name:
                base_score += weight
            elif winner == pokemon2.name:
                base_score -= weight
            # No change for "tied", "neutral"
        
        # Ensure score is within bounds
        return max(5.0, min(95.0, base_score))
    
    def _get_confidence_level(self, score_difference: float) -> str:
        """Get confidence level based on score difference."""
        if score_difference >= 30:
            return "high"
        elif score_difference >= 15:
            return "medium"
        else:
            return "low"


# Global battle tool instance
battle_tool = BattleTool()