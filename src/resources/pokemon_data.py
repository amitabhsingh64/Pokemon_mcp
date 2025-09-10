import asyncio
import logging
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP, Context

from ..services.pokeapi import PokeAPIClient, PokeAPIError
from ..services.cache import CachedPokeAPIClient, get_global_cache
from ..models.pokemon import Pokemon
from ..battle.types import PokemonTypes

logger = logging.getLogger(__name__)

# Global instances
_pokeapi_client: Optional[PokeAPIClient] = None
_cached_client: Optional[CachedPokeAPIClient] = None


async def get_pokeapi_client() -> PokeAPIClient:
    """Get or create PokeAPI client"""
    global _pokeapi_client
    if _pokeapi_client is None:
        _pokeapi_client = PokeAPIClient()
    return _pokeapi_client


async def get_cached_client() -> CachedPokeAPIClient:
    """Get or create cached PokeAPI client"""
    global _cached_client
    if _cached_client is None:
        cache = get_global_cache()
        _cached_client = CachedPokeAPIClient(cache)
    return _cached_client


def setup_pokemon_resources(mcp: FastMCP) -> None:
    """Setup all Pokemon-related MCP resources"""
    
    @mcp.resource("pokemon://list")
    async def list_pokemon() -> Dict[str, Any]:
        """
        List available Pokemon (first 151 for performance)
        
        Returns comprehensive list of Pokemon names and basic info
        """
        try:
            async with PokeAPIClient() as client:
                # Get the first 151 Pokemon (original generation)
                pokemon_list_data = await client._fetch_json("pokemon?limit=151")
                
                pokemon_list = []
                for pokemon in pokemon_list_data["results"]:
                    # Extract ID from URL
                    pokemon_id = pokemon["url"].strip("/").split("/")[-1]
                    pokemon_list.append({
                        "id": int(pokemon_id),
                        "name": pokemon["name"],
                        "url": pokemon["url"]
                    })
                
                return {
                    "pokemon": pokemon_list,
                    "total_count": len(pokemon_list),
                    "description": "List of available Pokemon for data queries and battles"
                }
                
        except Exception as e:
            logger.error(f"Failed to list Pokemon: {e}")
            return {
                "error": f"Failed to retrieve Pokemon list: {str(e)}",
                "pokemon": [],
                "total_count": 0
            }
    
    @mcp.resource("pokemon://info/{name}")
    async def get_pokemon_info(name: str) -> Dict[str, Any]:
        """
        Get comprehensive Pokemon information by name or ID
        
        Provides complete Pokemon data including stats, types, abilities, moves, and evolution info
        """
        try:
            cached_client = await get_cached_client()
            
            async with PokeAPIClient() as client:
                # Get Pokemon data with caching
                pokemon = await cached_client.get_pokemon(client, name)
                
                # Get evolution chain if available
                evolution_chain = await client.get_evolution_chain(name)
                
                # Format the response
                pokemon_data = {
                    "id": pokemon.id,
                    "name": pokemon.name,
                    "height": pokemon.height / 10,  # Convert to meters
                    "weight": pokemon.weight / 10,  # Convert to kg
                    "base_experience": pokemon.base_experience,
                    "types": pokemon.types,
                    "stats": {
                        "hp": pokemon.stats.hp,
                        "attack": pokemon.stats.attack,
                        "defense": pokemon.stats.defense,
                        "special_attack": pokemon.stats.special_attack,
                        "special_defense": pokemon.stats.special_defense,
                        "speed": pokemon.stats.speed,
                        "total": (pokemon.stats.hp + pokemon.stats.attack + 
                                pokemon.stats.defense + pokemon.stats.special_attack +
                                pokemon.stats.special_defense + pokemon.stats.speed)
                    },
                    "abilities": [
                        {
                            "name": ability.name,
                            "is_hidden": ability.is_hidden,
                            "slot": ability.slot
                        }
                        for ability in pokemon.abilities
                    ],
                    "moves": [
                        {
                            "name": move.name,
                            "level_learned": move.level_learned,
                            "learn_method": move.learn_method
                        }
                        for move in pokemon.moves[:20]  # Limit to first 20 moves
                    ],
                    "battle_info": {
                        "primary_type": pokemon.primary_type,
                        "secondary_type": pokemon.secondary_type,
                        "is_dual_type": pokemon.is_dual_type,
                        "weaknesses": PokemonTypes.get_type_weaknesses(pokemon.types),
                        "resistances": PokemonTypes.get_type_resistances(pokemon.types),
                        "immunities": PokemonTypes.get_type_immunities(pokemon.types)
                    }
                }
                
                # Add evolution information if available
                if evolution_chain:
                    pokemon_data["evolution"] = {
                        "species_name": evolution_chain.species_name,
                        "evolves_to": [
                            {"species_name": evo.species_name}
                            for evo in evolution_chain.evolves_to
                        ]
                    }
                
                return pokemon_data
                
        except PokeAPIError as e:
            logger.error(f"PokeAPI error for {name}: {e}")
            return {
                "error": f"Pokemon '{name}' not found or API error: {str(e)}",
                "name": name
            }
        except Exception as e:
            logger.error(f"Unexpected error getting Pokemon info for {name}: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "name": name
            }
    
    @mcp.resource("pokemon://stats/{name}")
    async def get_pokemon_stats(name: str) -> Dict[str, Any]:
        """
        Get Pokemon battle statistics and type effectiveness
        
        Focused on battle-relevant information for AI analysis
        """
        try:
            cached_client = await get_cached_client()
            
            async with PokeAPIClient() as client:
                pokemon = await cached_client.get_pokemon(client, name)
                
                # Calculate stat rankings (approximate)
                stats = pokemon.stats
                total_stats = (stats.hp + stats.attack + stats.defense + 
                             stats.special_attack + stats.special_defense + stats.speed)
                
                return {
                    "name": pokemon.name,
                    "types": pokemon.types,
                    "base_stats": {
                        "hp": stats.hp,
                        "attack": stats.attack,
                        "defense": stats.defense,
                        "special_attack": stats.special_attack,
                        "special_defense": stats.special_defense,
                        "speed": stats.speed,
                        "total": total_stats
                    },
                    "stat_analysis": {
                        "highest_stat": max([
                            ("hp", stats.hp), ("attack", stats.attack), 
                            ("defense", stats.defense), ("sp_attack", stats.special_attack),
                            ("sp_defense", stats.special_defense), ("speed", stats.speed)
                        ], key=lambda x: x[1]),
                        "physical_bias": stats.attack > stats.special_attack,
                        "defensive_bias": (stats.defense + stats.special_defense) > (stats.attack + stats.special_attack),
                        "speed_tier": "fast" if stats.speed > 100 else "medium" if stats.speed > 60 else "slow"
                    },
                    "type_effectiveness": {
                        "weaknesses": PokemonTypes.get_type_weaknesses(pokemon.types),
                        "resistances": PokemonTypes.get_type_resistances(pokemon.types),
                        "immunities": PokemonTypes.get_type_immunities(pokemon.types),
                        "stab_types": pokemon.types  # Types that get STAB bonus
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting stats for {name}: {e}")
            return {
                "error": f"Could not retrieve stats for '{name}': {str(e)}",
                "name": name
            }
    
    @mcp.resource("pokemon://type/{type_name}")
    async def get_pokemon_by_type(type_name: str) -> Dict[str, Any]:
        """
        Get Pokemon by type with battle analysis
        
        Returns Pokemon of a specific type with their battle capabilities
        """
        try:
            async with PokeAPIClient() as client:
                # Get Pokemon of this type
                pokemon_names = await client.get_pokemon_by_type(type_name, limit=50)
                
                if not pokemon_names:
                    return {
                        "error": f"No Pokemon found for type '{type_name}' or invalid type",
                        "type": type_name,
                        "pokemon": []
                    }
                
                # Get basic info for each Pokemon (limit to prevent API overload)
                pokemon_info = []
                cached_client = await get_cached_client()
                
                for name in pokemon_names[:20]:  # Limit to first 20
                    try:
                        pokemon = await cached_client.get_pokemon(client, name)
                        pokemon_info.append({
                            "name": pokemon.name,
                            "id": pokemon.id,
                            "types": pokemon.types,
                            "base_stat_total": (
                                pokemon.stats.hp + pokemon.stats.attack + 
                                pokemon.stats.defense + pokemon.stats.special_attack +
                                pokemon.stats.special_defense + pokemon.stats.speed
                            ),
                            "primary_stats": {
                                "hp": pokemon.stats.hp,
                                "attack": pokemon.stats.attack,
                                "defense": pokemon.stats.defense,
                                "speed": pokemon.stats.speed
                            }
                        })
                    except Exception as e:
                        logger.warning(f"Failed to get info for {name}: {e}")
                        continue
                
                # Type effectiveness analysis
                type_system = PokemonTypes()
                type_analysis = type_system.get_type_chart_summary().get(type_name, {})
                
                return {
                    "type": type_name,
                    "pokemon_count": len(pokemon_info),
                    "pokemon": pokemon_info,
                    "type_analysis": {
                        "offensive_advantages": type_analysis.get("super_effective", []),
                        "offensive_disadvantages": type_analysis.get("not_very_effective", []),
                        "immune_to": type_analysis.get("no_effect", []),
                        "description": f"Pokemon with {type_name} typing"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting Pokemon by type {type_name}: {e}")
            return {
                "error": f"Could not retrieve Pokemon for type '{type_name}': {str(e)}",
                "type": type_name,
                "pokemon": []
            }
    
    @mcp.resource("pokemon://search/{query}")
    async def search_pokemon(query: str) -> Dict[str, Any]:
        """
        Search for Pokemon by name
        
        Fuzzy search functionality for finding Pokemon
        """
        try:
            async with PokeAPIClient() as client:
                matches = await client.search_pokemon(query, limit=15)
                
                if not matches:
                    return {
                        "query": query,
                        "matches": [],
                        "message": f"No Pokemon found matching '{query}'"
                    }
                
                return {
                    "query": query,
                    "matches": [
                        {
                            "name": name,
                            "similarity": "exact" if name == query else "partial"
                        }
                        for name in matches
                    ],
                    "total_matches": len(matches)
                }
                
        except Exception as e:
            logger.error(f"Error searching for Pokemon '{query}': {e}")
            return {
                "error": f"Search failed for '{query}': {str(e)}",
                "query": query,
                "matches": []
            }
    
    @mcp.resource("pokemon://compare/{name1}/{name2}")
    async def compare_pokemon(name1: str, name2: str) -> Dict[str, Any]:
        """
        Compare two Pokemon for battle analysis
        
        Detailed comparison of stats, types, and battle matchup
        """
        try:
            cached_client = await get_cached_client()
            
            async with PokeAPIClient() as client:
                # Fetch both Pokemon concurrently
                pokemon1, pokemon2 = await asyncio.gather(
                    cached_client.get_pokemon(client, name1),
                    cached_client.get_pokemon(client, name2),
                    return_exceptions=True
                )
                
                # Handle errors
                if isinstance(pokemon1, Exception):
                    return {"error": f"Could not find Pokemon '{name1}': {pokemon1}"}
                if isinstance(pokemon2, Exception):
                    return {"error": f"Could not find Pokemon '{name2}': {pokemon2}"}
                
                # Compare stats
                stat_comparison = {}
                for stat_name in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]:
                    val1 = getattr(pokemon1.stats, stat_name)
                    val2 = getattr(pokemon2.stats, stat_name)
                    
                    stat_comparison[stat_name] = {
                        pokemon1.name: val1,
                        pokemon2.name: val2,
                        "advantage": pokemon1.name if val1 > val2 else pokemon2.name if val2 > val1 else "tie"
                    }
                
                # Type matchup analysis
                type_system = PokemonTypes()
                matchup1vs2 = type_system.analyze_matchup(pokemon1.types, pokemon2.types)
                matchup2vs1 = type_system.analyze_matchup(pokemon2.types, pokemon1.types)
                
                return {
                    "pokemon1": {
                        "name": pokemon1.name,
                        "types": pokemon1.types,
                        "stats": {
                            "hp": pokemon1.stats.hp,
                            "attack": pokemon1.stats.attack,
                            "defense": pokemon1.stats.defense,
                            "special_attack": pokemon1.stats.special_attack,
                            "special_defense": pokemon1.stats.special_defense,
                            "speed": pokemon1.stats.speed,
                            "total": (pokemon1.stats.hp + pokemon1.stats.attack + 
                                    pokemon1.stats.defense + pokemon1.stats.special_attack +
                                    pokemon1.stats.special_defense + pokemon1.stats.speed)
                        }
                    },
                    "pokemon2": {
                        "name": pokemon2.name,
                        "types": pokemon2.types,
                        "stats": {
                            "hp": pokemon2.stats.hp,
                            "attack": pokemon2.stats.attack,
                            "defense": pokemon2.stats.defense,
                            "special_attack": pokemon2.stats.special_attack,
                            "special_defense": pokemon2.stats.special_defense,
                            "speed": pokemon2.stats.speed,
                            "total": (pokemon2.stats.hp + pokemon2.stats.attack + 
                                    pokemon2.stats.defense + pokemon2.stats.special_attack +
                                    pokemon2.stats.special_defense + pokemon2.stats.speed)
                        }
                    },
                    "stat_comparison": stat_comparison,
                    "type_matchup": {
                        f"{pokemon1.name}_vs_{pokemon2.name}": matchup1vs2,
                        f"{pokemon2.name}_vs_{pokemon1.name}": matchup2vs1
                    },
                    "battle_prediction": {
                        "speed_advantage": pokemon1.name if pokemon1.stats.speed > pokemon2.stats.speed else pokemon2.name,
                        "offensive_advantage": pokemon1.name if (pokemon1.stats.attack + pokemon1.stats.special_attack) > (pokemon2.stats.attack + pokemon2.stats.special_attack) else pokemon2.name,
                        "defensive_advantage": pokemon1.name if (pokemon1.stats.defense + pokemon1.stats.special_defense + pokemon1.stats.hp) > (pokemon2.stats.defense + pokemon2.stats.special_defense + pokemon2.stats.hp) else pokemon2.name
                    }
                }
                
        except Exception as e:
            logger.error(f"Error comparing {name1} and {name2}: {e}")
            return {
                "error": f"Could not compare Pokemon: {str(e)}",
                "pokemon1": name1,
                "pokemon2": name2
            }
    
    @mcp.resource("pokemon://types")
    async def get_type_chart() -> Dict[str, Any]:
        """
        Get the complete Pokemon type effectiveness chart
        
        Comprehensive type relationships for battle strategy
        """
        try:
            type_system = PokemonTypes()
            
            return {
                "types": type_system.get_all_types(),
                "type_chart": type_system.get_type_chart_summary(),
                "description": "Complete Pokemon type effectiveness relationships",
                "effectiveness_values": {
                    "0.0": "No effect (immune)",
                    "0.5": "Not very effective",
                    "1.0": "Normal damage",
                    "2.0": "Super effective"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting type chart: {e}")
            return {
                "error": f"Could not retrieve type chart: {str(e)}",
                "types": [],
                "type_chart": {}
            }