import asyncio
import logging
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context

from ..services.pokeapi import PokeAPIClient, PokeAPIError
from ..services.cache import CachedPokeAPIClient, get_global_cache
from ..models.pokemon import BattlePokemon, BattleResult
from ..battle.engine import BattleEngine
from ..battle.types import PokemonTypes

logger = logging.getLogger(__name__)


def setup_battle_tools(mcp: FastMCP) -> None:
    """Setup all battle simulation MCP tools"""
    
    @mcp.tool
    async def simulate_battle(
        pokemon1_name: str,
        pokemon2_name: str,
        level: int = 50,
        detailed_log: bool = True,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Simulate a Pokemon battle between two Pokemon
        
        This tool allows you to simulate a complete battle between any two Pokemon,
        providing detailed turn-by-turn logs, damage calculations, and final results.
        
        Args:
            pokemon1_name: Name of the first Pokemon (e.g., "pikachu", "charizard")
            pokemon2_name: Name of the second Pokemon (e.g., "blastoise", "venusaur") 
            level: Level for both Pokemon (default: 50, range: 1-100)
            detailed_log: Whether to include detailed battle log (default: True)
            ctx: FastMCP context for logging
            
        Returns:
            Complete battle simulation results including winner, turn log, and statistics
        """
        if ctx:
            await ctx.info(f"Starting battle simulation: {pokemon1_name} vs {pokemon2_name}")
        
        try:
            # Validate level
            level = max(1, min(100, level))
            
            # Get cached client
            cached_client = CachedPokeAPIClient(get_global_cache())
            
            # Fetch Pokemon data
            async with PokeAPIClient() as client:
                if ctx:
                    await ctx.info("Fetching Pokemon data...")
                
                try:
                    pokemon1_data, pokemon2_data = await asyncio.gather(
                        cached_client.get_pokemon(client, pokemon1_name),
                        cached_client.get_pokemon(client, pokemon2_name)
                    )
                except Exception as e:
                    error_msg = f"Failed to fetch Pokemon data: {str(e)}"
                    if ctx:
                        await ctx.error(error_msg)
                    return {
                        "error": error_msg,
                        "pokemon1": pokemon1_name,
                        "pokemon2": pokemon2_name
                    }
                
                # Create battle Pokemon instances
                battle_pokemon1 = BattlePokemon(pokemon1_data, level)
                battle_pokemon2 = BattlePokemon(pokemon2_data, level)
                
                if ctx:
                    await ctx.info(f"Battle setup complete - Level {level} battle")
                
                # Create battle engine and simulate
                battle_engine = BattleEngine()
                
                if ctx:
                    await ctx.info("Simulating battle...")
                
                result = await battle_engine.simulate_battle(
                    battle_pokemon1,
                    battle_pokemon2,
                    ai_strategy="random"
                )
                
                # Format response
                response = {
                    "battle_info": {
                        "pokemon1": {
                            "name": pokemon1_data.name,
                            "level": level,
                            "types": pokemon1_data.types,
                            "stats": {
                                "hp": battle_pokemon1.max_hp,
                                "attack": battle_pokemon1.get_effective_stat("attack"),
                                "defense": battle_pokemon1.get_effective_stat("defense"),
                                "special_attack": battle_pokemon1.get_effective_stat("special_attack"),
                                "special_defense": battle_pokemon1.get_effective_stat("special_defense"),
                                "speed": battle_pokemon1.get_effective_stat("speed")
                            }
                        },
                        "pokemon2": {
                            "name": pokemon2_data.name,
                            "level": level,
                            "types": pokemon2_data.types,
                            "stats": {
                                "hp": battle_pokemon2.max_hp,
                                "attack": battle_pokemon2.get_effective_stat("attack"),
                                "defense": battle_pokemon2.get_effective_stat("defense"),
                                "special_attack": battle_pokemon2.get_effective_stat("special_attack"),
                                "special_defense": battle_pokemon2.get_effective_stat("special_defense"),
                                "speed": battle_pokemon2.get_effective_stat("speed")
                            }
                        }
                    },
                    "battle_result": {
                        "winner": result.winner,
                        "loser": result.loser,
                        "total_turns": result.total_turns,
                        "victory_type": "knockout" if any(stats["fainted"] for stats in result.final_stats.values()) else "decision"
                    },
                    "final_stats": result.final_stats,
                    "battle_summary": {
                        "total_actions": len([log for log in result.battle_log if log.action == "attack"]),
                        "critical_hits": len([log for log in result.battle_log if log.critical_hit]),
                        "status_effects_applied": len([log for log in result.battle_log if log.status_applied]),
                        "average_damage": _calculate_average_damage(result.battle_log),
                        "type_advantages": _analyze_type_advantages(result.battle_log)
                    }
                }
                
                # Add detailed log if requested
                if detailed_log:
                    response["detailed_log"] = [
                        {
                            "turn": log.turn,
                            "action": log.action,
                            "attacker": log.attacker,
                            "defender": log.defender,
                            "move_used": log.move_used,
                            "damage": log.damage,
                            "effectiveness": log.effectiveness,
                            "critical_hit": log.critical_hit,
                            "status_applied": log.status_applied,
                            "message": log.message
                        }
                        for log in result.battle_log
                    ]
                else:
                    # Provide key moments only
                    response["key_moments"] = [
                        {
                            "turn": log.turn,
                            "message": log.message
                        }
                        for log in result.battle_log 
                        if log.action in ["battle_start", "attack", "faint"] and log.critical_hit or log.status_applied
                    ]
                
                if ctx:
                    await ctx.info(f"Battle complete! Winner: {result.winner} in {result.total_turns} turns")
                
                return response
                
        except PokeAPIError as e:
            error_msg = f"Pokemon data error: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            return {
                "error": error_msg,
                "suggestion": "Check Pokemon names spelling. Use lowercase names like 'pikachu' or 'charizard'"
            }
        
        except Exception as e:
            error_msg = f"Battle simulation failed: {str(e)}"
            logger.error(f"Battle simulation error: {e}", exc_info=True)
            if ctx:
                await ctx.error(error_msg)
            return {
                "error": error_msg,
                "pokemon1": pokemon1_name,
                "pokemon2": pokemon2_name
            }
    
    @mcp.tool
    async def predict_battle_outcome(
        pokemon1_name: str,
        pokemon2_name: str,
        level: int = 50,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Predict battle outcome based on stats and type matchups without full simulation
        
        Provides quick battle analysis and prediction based on Pokemon stats,
        types, and theoretical calculations.
        
        Args:
            pokemon1_name: Name of the first Pokemon
            pokemon2_name: Name of the second Pokemon  
            level: Level for analysis (default: 50)
            ctx: FastMCP context for logging
            
        Returns:
            Battle prediction with probability estimates and key factors
        """
        if ctx:
            await ctx.info(f"Analyzing matchup: {pokemon1_name} vs {pokemon2_name}")
        
        try:
            level = max(1, min(100, level))
            cached_client = CachedPokeAPIClient(get_global_cache())
            
            async with PokeAPIClient() as client:
                # Fetch Pokemon data
                pokemon1_data, pokemon2_data = await asyncio.gather(
                    cached_client.get_pokemon(client, pokemon1_name),
                    cached_client.get_pokemon(client, pokemon2_name)
                )
                
                # Create battle instances for stat calculation
                battle_pokemon1 = BattlePokemon(pokemon1_data, level)
                battle_pokemon2 = BattlePokemon(pokemon2_data, level)
                
                # Type effectiveness analysis
                type_system = PokemonTypes()
                p1_vs_p2_effectiveness = type_system.analyze_matchup(pokemon1_data.types, pokemon2_data.types)
                p2_vs_p1_effectiveness = type_system.analyze_matchup(pokemon2_data.types, pokemon1_data.types)
                
                # Calculate various factors
                factors = {
                    "speed_advantage": _analyze_speed_advantage(battle_pokemon1, battle_pokemon2),
                    "type_advantage": _analyze_type_advantage(p1_vs_p2_effectiveness, p2_vs_p1_effectiveness),
                    "stat_advantage": _analyze_stat_advantage(battle_pokemon1, battle_pokemon2),
                    "bulk_advantage": _analyze_bulk_advantage(battle_pokemon1, battle_pokemon2)
                }
                
                # Calculate prediction scores (0-100 for each Pokemon)
                p1_score = _calculate_prediction_score(battle_pokemon1, battle_pokemon2, factors, True)
                p2_score = 100 - p1_score
                
                # Determine confidence level
                score_difference = abs(p1_score - p2_score)
                if score_difference > 30:
                    confidence = "high"
                elif score_difference > 15:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                return {
                    "matchup_analysis": {
                        "pokemon1": {
                            "name": pokemon1_data.name,
                            "types": pokemon1_data.types,
                            "predicted_win_chance": f"{p1_score}%",
                            "key_advantages": _get_key_advantages(factors, True)
                        },
                        "pokemon2": {
                            "name": pokemon2_data.name,
                            "types": pokemon2_data.types,
                            "predicted_win_chance": f"{p2_score}%",
                            "key_advantages": _get_key_advantages(factors, False)
                        }
                    },
                    "prediction": {
                        "predicted_winner": pokemon1_data.name if p1_score > p2_score else pokemon2_data.name,
                        "confidence_level": confidence,
                        "decisive_factors": _get_decisive_factors(factors),
                        "reasoning": _generate_prediction_reasoning(battle_pokemon1, battle_pokemon2, factors)
                    },
                    "type_matchup": {
                        f"{pokemon1_data.name}_attacking": {
                            type_name: effectiveness 
                            for type_name, effectiveness in p1_vs_p2_effectiveness.items()
                            if effectiveness != 1.0
                        },
                        f"{pokemon2_data.name}_attacking": {
                            type_name: effectiveness 
                            for type_name, effectiveness in p2_vs_p1_effectiveness.items()
                            if effectiveness != 1.0
                        }
                    },
                    "stat_comparison": {
                        "hp": {pokemon1_data.name: battle_pokemon1.max_hp, pokemon2_data.name: battle_pokemon2.max_hp},
                        "attack": {pokemon1_data.name: battle_pokemon1.get_effective_stat("attack"), pokemon2_data.name: battle_pokemon2.get_effective_stat("attack")},
                        "defense": {pokemon1_data.name: battle_pokemon1.get_effective_stat("defense"), pokemon2_data.name: battle_pokemon2.get_effective_stat("defense")},
                        "special_attack": {pokemon1_data.name: battle_pokemon1.get_effective_stat("special_attack"), pokemon2_data.name: battle_pokemon2.get_effective_stat("special_attack")},
                        "special_defense": {pokemon1_data.name: battle_pokemon1.get_effective_stat("special_defense"), pokemon2_data.name: battle_pokemon2.get_effective_stat("special_defense")},
                        "speed": {pokemon1_data.name: battle_pokemon1.get_effective_stat("speed"), pokemon2_data.name: battle_pokemon2.get_effective_stat("speed")}
                    }
                }
                
        except Exception as e:
            error_msg = f"Battle prediction failed: {str(e)}"
            logger.error(f"Battle prediction error: {e}")
            if ctx:
                await ctx.error(error_msg)
            return {
                "error": error_msg,
                "pokemon1": pokemon1_name,
                "pokemon2": pokemon2_name
            }
    
    @mcp.tool
    async def battle_multiple_pokemon(
        pokemon_list: List[str],
        level: int = 50,
        tournament_style: bool = True,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Simulate battles between multiple Pokemon
        
        Run either a round-robin tournament or sequential battles between a list of Pokemon.
        
        Args:
            pokemon_list: List of Pokemon names (minimum 2, maximum 8)
            level: Level for all Pokemon (default: 50)
            tournament_style: If True, each Pokemon battles every other Pokemon once
            ctx: FastMCP context for logging
            
        Returns:
            Tournament results with rankings and individual battle outcomes
        """
        if ctx:
            await ctx.info(f"Starting multi-Pokemon battle with {len(pokemon_list)} contestants")
        
        try:
            # Validate input
            if len(pokemon_list) < 2:
                return {"error": "Need at least 2 Pokemon for battles"}
            if len(pokemon_list) > 8:
                return {"error": "Maximum 8 Pokemon allowed to prevent excessive API calls"}
            
            level = max(1, min(100, level))
            results = {"battles": [], "rankings": {}, "statistics": {}}
            
            if tournament_style:
                # Round-robin tournament
                total_battles = len(pokemon_list) * (len(pokemon_list) - 1) // 2
                battle_count = 0
                
                if ctx:
                    await ctx.info(f"Running round-robin tournament with {total_battles} battles")
                
                win_counts = {name: 0 for name in pokemon_list}
                
                for i in range(len(pokemon_list)):
                    for j in range(i + 1, len(pokemon_list)):
                        pokemon1 = pokemon_list[i]
                        pokemon2 = pokemon_list[j]
                        battle_count += 1
                        
                        if ctx:
                            await ctx.info(f"Battle {battle_count}/{total_battles}: {pokemon1} vs {pokemon2}")
                        
                        # Simulate battle
                        battle_result = await simulate_battle(
                            pokemon1, pokemon2, level, detailed_log=False, ctx=None
                        )
                        
                        if "error" not in battle_result:
                            winner = battle_result["battle_result"]["winner"]
                            win_counts[winner] += 1
                            
                            results["battles"].append({
                                "battle_number": battle_count,
                                "pokemon1": pokemon1,
                                "pokemon2": pokemon2,
                                "winner": winner,
                                "turns": battle_result["battle_result"]["total_turns"]
                            })
                        else:
                            results["battles"].append({
                                "battle_number": battle_count,
                                "pokemon1": pokemon1,
                                "pokemon2": pokemon2,
                                "error": battle_result["error"]
                            })
                
                # Calculate rankings
                sorted_pokemon = sorted(win_counts.items(), key=lambda x: x[1], reverse=True)
                results["rankings"] = {
                    rank + 1: {"name": name, "wins": wins, "losses": len(pokemon_list) - 1 - wins}
                    for rank, (name, wins) in enumerate(sorted_pokemon)
                }
                
                results["tournament_winner"] = sorted_pokemon[0][0]
                
            else:
                # Sequential battles (battle royale style)
                if ctx:
                    await ctx.info("Running sequential elimination battles")
                
                remaining_pokemon = pokemon_list.copy()
                battle_count = 0
                
                while len(remaining_pokemon) > 1:
                    pokemon1 = remaining_pokemon[0]
                    pokemon2 = remaining_pokemon[1]
                    battle_count += 1
                    
                    if ctx:
                        await ctx.info(f"Battle {battle_count}: {pokemon1} vs {pokemon2}")
                    
                    battle_result = await simulate_battle(
                        pokemon1, pokemon2, level, detailed_log=False, ctx=None
                    )
                    
                    if "error" not in battle_result:
                        winner = battle_result["battle_result"]["winner"]
                        loser = battle_result["battle_result"]["loser"]
                        
                        results["battles"].append({
                            "battle_number": battle_count,
                            "pokemon1": pokemon1,
                            "pokemon2": pokemon2,
                            "winner": winner,
                            "eliminated": loser,
                            "turns": battle_result["battle_result"]["total_turns"]
                        })
                        
                        # Remove loser, keep winner at front
                        remaining_pokemon.remove(loser)
                        if remaining_pokemon[0] != winner:
                            remaining_pokemon.remove(winner)
                            remaining_pokemon.insert(0, winner)
                    else:
                        results["battles"].append({
                            "battle_number": battle_count,
                            "pokemon1": pokemon1,
                            "pokemon2": pokemon2,
                            "error": battle_result["error"]
                        })
                        # Remove both Pokemon on error
                        remaining_pokemon = remaining_pokemon[2:]
                
                if remaining_pokemon:
                    results["final_winner"] = remaining_pokemon[0]
                
            # Calculate statistics
            successful_battles = [b for b in results["battles"] if "error" not in b]
            if successful_battles:
                results["statistics"] = {
                    "total_battles": len(results["battles"]),
                    "successful_battles": len(successful_battles),
                    "average_battle_length": sum(b["turns"] for b in successful_battles) / len(successful_battles),
                    "longest_battle": max(successful_battles, key=lambda x: x["turns"]),
                    "shortest_battle": min(successful_battles, key=lambda x: x["turns"])
                }
            
            return results
            
        except Exception as e:
            error_msg = f"Multi-Pokemon battle failed: {str(e)}"
            logger.error(f"Multi-Pokemon battle error: {e}")
            if ctx:
                await ctx.error(error_msg)
            return {"error": error_msg}


# Helper functions for battle analysis
def _calculate_average_damage(battle_log: List) -> float:
    """Calculate average damage from battle log"""
    damage_entries = [log.damage for log in battle_log if log.damage and log.damage > 0]
    return sum(damage_entries) / len(damage_entries) if damage_entries else 0.0


def _analyze_type_advantages(battle_log: List) -> Dict[str, int]:
    """Analyze type advantage occurrences"""
    advantages = {"super_effective": 0, "not_very_effective": 0, "no_effect": 0}
    for log in battle_log:
        if log.effectiveness:
            if "super effective" in log.effectiveness:
                advantages["super_effective"] += 1
            elif "not very effective" in log.effectiveness:
                advantages["not_very_effective"] += 1
            elif "no effect" in log.effectiveness:
                advantages["no_effect"] += 1
    return advantages


def _analyze_speed_advantage(pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
    """Analyze speed advantage"""
    speed1 = pokemon1.get_effective_stat("speed")
    speed2 = pokemon2.get_effective_stat("speed")
    
    if speed1 > speed2:
        return pokemon1.pokemon.name
    elif speed2 > speed1:
        return pokemon2.pokemon.name
    else:
        return "tie"


def _analyze_type_advantage(matchup1: Dict, matchup2: Dict) -> str:
    """Analyze overall type advantage"""
    max_advantage1 = max(matchup1.values()) if matchup1.values() else 1.0
    max_advantage2 = max(matchup2.values()) if matchup2.values() else 1.0
    
    if max_advantage1 > max_advantage2:
        return "pokemon1"
    elif max_advantage2 > max_advantage1:
        return "pokemon2"
    else:
        return "neutral"


def _analyze_stat_advantage(pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
    """Analyze overall stat advantage"""
    stats1 = sum([
        pokemon1.get_effective_stat("attack"),
        pokemon1.get_effective_stat("defense"),
        pokemon1.get_effective_stat("special_attack"),
        pokemon1.get_effective_stat("special_defense"),
        pokemon1.get_effective_stat("speed")
    ])
    
    stats2 = sum([
        pokemon2.get_effective_stat("attack"),
        pokemon2.get_effective_stat("defense"),
        pokemon2.get_effective_stat("special_attack"),
        pokemon2.get_effective_stat("special_defense"),
        pokemon2.get_effective_stat("speed")
    ])
    
    if stats1 > stats2:
        return pokemon1.pokemon.name
    elif stats2 > stats1:
        return pokemon2.pokemon.name
    else:
        return "tie"


def _analyze_bulk_advantage(pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> str:
    """Analyze defensive bulk advantage"""
    bulk1 = pokemon1.max_hp * (pokemon1.get_effective_stat("defense") + pokemon1.get_effective_stat("special_defense"))
    bulk2 = pokemon2.max_hp * (pokemon2.get_effective_stat("defense") + pokemon2.get_effective_stat("special_defense"))
    
    if bulk1 > bulk2:
        return pokemon1.pokemon.name
    elif bulk2 > bulk1:
        return pokemon2.pokemon.name
    else:
        return "tie"


def _calculate_prediction_score(pokemon1: BattlePokemon, pokemon2: BattlePokemon, factors: Dict, for_pokemon1: bool) -> int:
    """Calculate prediction score based on various factors"""
    base_score = 50
    
    # Speed advantage (+/-10)
    if factors["speed_advantage"] == pokemon1.pokemon.name:
        base_score += 10 if for_pokemon1 else -10
    elif factors["speed_advantage"] == pokemon2.pokemon.name:
        base_score -= 10 if for_pokemon1 else -10
    
    # Type advantage (+/-15)
    if factors["type_advantage"] == "pokemon1":
        base_score += 15 if for_pokemon1 else -15
    elif factors["type_advantage"] == "pokemon2":
        base_score -= 15 if for_pokemon1 else -15
    
    # Stat advantage (+/-10)
    if factors["stat_advantage"] == pokemon1.pokemon.name:
        base_score += 10 if for_pokemon1 else -10
    elif factors["stat_advantage"] == pokemon2.pokemon.name:
        base_score -= 10 if for_pokemon1 else -10
    
    # Bulk advantage (+/-10)
    if factors["bulk_advantage"] == pokemon1.pokemon.name:
        base_score += 10 if for_pokemon1 else -10
    elif factors["bulk_advantage"] == pokemon2.pokemon.name:
        base_score -= 10 if for_pokemon1 else -10
    
    return max(5, min(95, base_score))


def _get_key_advantages(factors: Dict, for_pokemon1: bool) -> List[str]:
    """Get key advantages for a Pokemon"""
    advantages = []
    
    for factor, value in factors.items():
        if for_pokemon1 and value != "tie" and ("pokemon1" in str(value) or value.startswith(factors.get("pokemon1_name", ""))):
            advantages.append(factor.replace("_", " ").title())
        elif not for_pokemon1 and value != "tie" and ("pokemon2" in str(value) or value.startswith(factors.get("pokemon2_name", ""))):
            advantages.append(factor.replace("_", " ").title())
    
    return advantages


def _get_decisive_factors(factors: Dict) -> List[str]:
    """Get the most decisive factors in the matchup"""
    decisive = []
    
    if factors["type_advantage"] != "neutral":
        decisive.append("Type advantage")
    if factors["speed_advantage"] != "tie":
        decisive.append("Speed advantage")
    if factors["stat_advantage"] != "tie":
        decisive.append("Overall stats")
    
    return decisive or ["Even matchup"]


def _generate_prediction_reasoning(pokemon1: BattlePokemon, pokemon2: BattlePokemon, factors: Dict) -> str:
    """Generate reasoning for the prediction"""
    reasoning_parts = []
    
    if factors["speed_advantage"] != "tie":
        reasoning_parts.append(f"{factors['speed_advantage']} has the speed advantage")
    
    if factors["type_advantage"] != "neutral":
        advantage_pokemon = "Pokemon 1" if factors["type_advantage"] == "pokemon1" else "Pokemon 2"
        reasoning_parts.append(f"{advantage_pokemon} has type advantage")
    
    if factors["stat_advantage"] != "tie":
        reasoning_parts.append(f"{factors['stat_advantage']} has superior overall stats")
    
    if not reasoning_parts:
        reasoning_parts.append("This appears to be an even matchup")
    
    return ". ".join(reasoning_parts) + "."