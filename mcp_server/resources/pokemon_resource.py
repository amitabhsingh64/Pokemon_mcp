"""Pokemon data resource for MCP server."""

import logging
from typing import Dict, Any, List
from fastapi import HTTPException

from ..utils.pokeapi_client import get_client, PokemonData
from ..utils.type_chart import (
    get_type_weaknesses, 
    get_type_resistances,
    analyze_matchup
)

logger = logging.getLogger(__name__)


class PokemonResource:
    """Pokemon data resource handler."""
    
    async def get_pokemon(self, name: str) -> Dict[str, Any]:
        """Get detailed Pokemon information."""
        try:
            async with await get_client() as client:
                pokemon = await client.get_pokemon(name)
                
                return {
                    "id": pokemon.id,
                    "name": pokemon.name,
                    "types": pokemon.types,
                    "stats": pokemon.stats,
                    "abilities": pokemon.abilities,
                    "height": pokemon.height / 10,  # Convert to meters
                    "weight": pokemon.weight / 10,  # Convert to kg
                    "battle_info": {
                        "weaknesses": get_type_weaknesses(pokemon.types),
                        "resistances": get_type_resistances(pokemon.types),
                        "stat_total": sum(pokemon.stats.values())
                    }
                }
                
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get Pokemon {name}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def list_pokemon(self, limit: int = 151) -> Dict[str, Any]:
        """List Pokemon names."""
        try:
            # Return first generation Pokemon for simplicity
            pokemon_names = [
                "bulbasaur", "ivysaur", "venusaur", "charmander", "charmeleon", 
                "charizard", "squirtle", "wartortle", "blastoise", "caterpie",
                "metapod", "butterfree", "weedle", "kakuna", "beedrill",
                "pidgey", "pidgeotto", "pidgeot", "rattata", "raticate",
                "spearow", "fearow", "ekans", "arbok", "pikachu",
                "raichu", "sandshrew", "sandslash", "nidoran-f", "nidorina",
                "nidoqueen", "nidoran-m", "nidorino", "nidoking", "clefairy",
                "clefable", "vulpix", "ninetales", "jigglypuff", "wigglytuff",
                "zubat", "golbat", "oddish", "gloom", "vileplume",
                "paras", "parasect", "venonat", "venomoth", "diglett",
                "dugtrio", "meowth", "persian", "psyduck", "golduck",
                "mankey", "primeape", "growlithe", "arcanine", "poliwag",
                "poliwhirl", "poliwrath", "abra", "kadabra", "alakazam",
                "machop", "machoke", "machamp", "bellsprout", "weepinbell",
                "victreebel", "tentacool", "tentacruel", "geodude", "graveler",
                "golem", "ponyta", "rapidash", "slowpoke", "slowbro",
                "magnemite", "magneton", "farfetchd", "doduo", "dodrio",
                "seel", "dewgong", "grimer", "muk", "shellder",
                "cloyster", "gastly", "haunter", "gengar", "onix",
                "drowzee", "hypno", "krabby", "kingler", "voltorb",
                "electrode", "exeggcute", "exeggutor", "cubone", "marowak",
                "hitmonlee", "hitmonchan", "lickitung", "koffing", "weezing",
                "rhyhorn", "rhydon", "chansey", "tangela", "kangaskhan",
                "horsea", "seadra", "goldeen", "seaking", "staryu",
                "starmie", "mr-mime", "scyther", "jynx", "electabuzz",
                "magmar", "pinsir", "tauros", "magikarp", "gyarados",
                "lapras", "ditto", "eevee", "vaporeon", "jolteon",
                "flareon", "porygon", "omanyte", "omastar", "kabuto",
                "kabutops", "aerodactyl", "snorlax", "articuno", "zapdos",
                "moltres", "dratini", "dragonair", "dragonite", "mewtwo", "mew"
            ]
            
            return {
                "pokemon": pokemon_names[:limit],
                "total_count": len(pokemon_names[:limit]),
                "description": f"First {min(limit, len(pokemon_names))} Pokemon"
            }
            
        except Exception as e:
            logger.error(f"Failed to list Pokemon: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def search_pokemon(self, query: str) -> Dict[str, Any]:
        """Search for Pokemon by name."""
        try:
            async with await get_client() as client:
                matches = await client.search_pokemon(query, limit=20)
                
                return {
                    "query": query,
                    "matches": matches,
                    "total_matches": len(matches)
                }
                
        except Exception as e:
            logger.error(f"Failed to search Pokemon: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def compare_pokemon(self, name1: str, name2: str) -> Dict[str, Any]:
        """Compare two Pokemon."""
        try:
            async with await get_client() as client:
                pokemon1 = await client.get_pokemon(name1)
                pokemon2 = await client.get_pokemon(name2)
                
                # Compare stats
                stat_comparison = {}
                for stat_name in pokemon1.stats.keys():
                    val1 = pokemon1.stats[stat_name]
                    val2 = pokemon2.stats.get(stat_name, 0)
                    
                    stat_comparison[stat_name] = {
                        pokemon1.name: val1,
                        pokemon2.name: val2,
                        "advantage": pokemon1.name if val1 > val2 else pokemon2.name if val2 > val1 else "tie"
                    }
                
                # Type matchup analysis
                matchup1vs2 = analyze_matchup(pokemon1.types, pokemon2.types)
                matchup2vs1 = analyze_matchup(pokemon2.types, pokemon1.types)
                
                return {
                    "pokemon1": {
                        "name": pokemon1.name,
                        "types": pokemon1.types,
                        "stat_total": sum(pokemon1.stats.values())
                    },
                    "pokemon2": {
                        "name": pokemon2.name,
                        "types": pokemon2.types,
                        "stat_total": sum(pokemon2.stats.values())
                    },
                    "stat_comparison": stat_comparison,
                    "type_matchup": {
                        f"{pokemon1.name}_vs_{pokemon2.name}": matchup1vs2,
                        f"{pokemon2.name}_vs_{pokemon1.name}": matchup2vs1
                    }
                }
                
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to compare Pokemon: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_type_chart(self) -> Dict[str, Any]:
        """Get complete type effectiveness chart."""
        try:
            from ..utils.type_chart import TYPE_CHART, POKEMON_TYPES
            
            return {
                "types": POKEMON_TYPES,
                "type_chart": TYPE_CHART,
                "description": "Complete Pokemon type effectiveness chart"
            }
            
        except Exception as e:
            logger.error(f"Failed to get type chart: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")