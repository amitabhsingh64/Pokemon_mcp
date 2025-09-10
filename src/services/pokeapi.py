import asyncio
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from ..models.pokemon import (
    Pokemon, PokemonStats, PokemonAbility, PokemonMove, MoveDetails, EvolutionChain
)

logger = logging.getLogger(__name__)


class PokeAPIError(Exception):
    """Custom exception for PokeAPI related errors"""
    pass


class PokeAPIClient:
    """Async client for fetching Pokémon data from PokeAPI"""
    
    def __init__(self, base_url: str = "https://pokeapi.co/api/v2/", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising error if not initialized"""
        if not self._client:
            raise PokeAPIError("Client not initialized. Use async context manager.")
        return self._client
    
    async def _fetch_json(self, endpoint: str) -> Dict[str, Any]:
        """Fetch JSON data from PokeAPI endpoint"""
        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise PokeAPIError(f"Resource not found: {endpoint}")
            raise PokeAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise PokeAPIError(f"Request error: {str(e)}")
        except Exception as e:
            raise PokeAPIError(f"Unexpected error: {str(e)}")
    
    def _normalize_name(self, name: str) -> str:
        """Normalize Pokémon name for API queries"""
        return name.lower().strip().replace(" ", "-")
    
    def _extract_stat_value(self, stats_data: List[Dict], stat_name: str) -> int:
        """Extract a specific stat value from API response"""
        for stat in stats_data:
            if stat["stat"]["name"] == stat_name:
                return stat["base_stat"]
        return 0
    
    async def get_pokemon(self, identifier: str) -> Pokemon:
        """
        Fetch complete Pokémon data by name or ID
        
        Args:
            identifier: Pokémon name or ID
            
        Returns:
            Pokemon model with complete data
            
        Raises:
            PokeAPIError: If Pokémon not found or API error occurs
        """
        try:
            # Normalize identifier for API
            if isinstance(identifier, str):
                identifier = self._normalize_name(identifier)
            
            # Fetch basic Pokémon data
            pokemon_data = await self._fetch_json(f"pokemon/{identifier}")
            species_data = await self._fetch_json(pokemon_data["species"]["url"].replace(self.base_url, ""))
            
            # Extract stats
            stats_raw = pokemon_data["stats"]
            stats = PokemonStats(
                hp=self._extract_stat_value(stats_raw, "hp"),
                attack=self._extract_stat_value(stats_raw, "attack"),
                defense=self._extract_stat_value(stats_raw, "defense"),
                special_attack=self._extract_stat_value(stats_raw, "special-attack"),
                special_defense=self._extract_stat_value(stats_raw, "special-defense"),
                speed=self._extract_stat_value(stats_raw, "speed")
            )
            
            # Extract types
            types = [type_info["type"]["name"] for type_info in pokemon_data["types"]]
            
            # Extract abilities
            abilities = []
            for ability_info in pokemon_data["abilities"]:
                abilities.append(PokemonAbility(
                    name=ability_info["ability"]["name"],
                    url=ability_info["ability"]["url"],
                    is_hidden=ability_info.get("is_hidden", False),
                    slot=ability_info["slot"]
                ))
            
            # Extract moves (limit to level-up moves for performance)
            moves = []
            for move_info in pokemon_data["moves"]:
                move_name = move_info["move"]["name"]
                
                # Find level-up learn method
                level_learned = 0
                learn_method = "other"
                
                for version_detail in move_info["version_group_details"]:
                    if version_detail["move_learn_method"]["name"] == "level-up":
                        level_learned = version_detail["level_learned_at"]
                        learn_method = "level-up"
                        break
                
                if learn_method == "level-up":  # Only include level-up moves
                    moves.append(PokemonMove(
                        name=move_name,
                        url=move_info["move"]["url"],
                        level_learned=level_learned,
                        learn_method=learn_method
                    ))
            
            # Sort moves by level learned
            moves.sort(key=lambda m: m.level_learned)
            
            return Pokemon(
                id=pokemon_data["id"],
                name=pokemon_data["name"],
                height=pokemon_data["height"],
                weight=pokemon_data["weight"],
                base_experience=pokemon_data["base_experience"] or 0,
                types=types,
                abilities=abilities,
                stats=stats,
                moves=moves,
                species_url=pokemon_data["species"]["url"]
            )
            
        except ValidationError as e:
            raise PokeAPIError(f"Data validation error for {identifier}: {e}")
        except Exception as e:
            if isinstance(e, PokeAPIError):
                raise
            raise PokeAPIError(f"Failed to fetch Pokémon {identifier}: {str(e)}")
    
    async def get_move_details(self, move_identifier: str) -> MoveDetails:
        """
        Fetch detailed move information
        
        Args:
            move_identifier: Move name or ID
            
        Returns:
            MoveDetails model
        """
        try:
            if isinstance(move_identifier, str):
                move_identifier = self._normalize_name(move_identifier)
                
            move_data = await self._fetch_json(f"move/{move_identifier}")
            
            return MoveDetails(
                name=move_data["name"],
                power=move_data["power"],
                accuracy=move_data["accuracy"],
                pp=move_data["pp"],
                priority=move_data["priority"],
                damage_class=move_data["damage_class"]["name"],
                type=move_data["type"]["name"],
                target=move_data["target"]["name"],
                effect_chance=move_data.get("effect_chance"),
                effect_entries=move_data.get("effect_entries", [])
            )
            
        except Exception as e:
            if isinstance(e, PokeAPIError):
                raise
            raise PokeAPIError(f"Failed to fetch move {move_identifier}: {str(e)}")
    
    async def get_type_effectiveness(self, type_name: str) -> Dict[str, float]:
        """
        Get type effectiveness chart for a given type
        
        Args:
            type_name: The attacking type name
            
        Returns:
            Dict mapping defending type names to effectiveness multipliers
        """
        try:
            type_data = await self._fetch_json(f"type/{type_name}")
            
            effectiveness = {}
            
            # Super effective (2x damage)
            for relation in type_data["damage_relations"]["double_damage_to"]:
                effectiveness[relation["name"]] = 2.0
                
            # Not very effective (0.5x damage)  
            for relation in type_data["damage_relations"]["half_damage_to"]:
                effectiveness[relation["name"]] = 0.5
                
            # No effect (0x damage)
            for relation in type_data["damage_relations"]["no_damage_to"]:
                effectiveness[relation["name"]] = 0.0
                
            return effectiveness
            
        except Exception as e:
            if isinstance(e, PokeAPIError):
                raise
            raise PokeAPIError(f"Failed to fetch type effectiveness for {type_name}: {str(e)}")
    
    async def get_pokemon_by_type(self, type_name: str, limit: int = 20) -> List[str]:
        """
        Get list of Pokémon names by type
        
        Args:
            type_name: Type name (e.g., "fire", "water")
            limit: Maximum number of Pokémon to return
            
        Returns:
            List of Pokémon names
        """
        try:
            type_data = await self._fetch_json(f"type/{type_name}")
            pokemon_list = []
            
            for pokemon_info in type_data["pokemon"][:limit]:
                pokemon_list.append(pokemon_info["pokemon"]["name"])
                
            return pokemon_list
            
        except Exception as e:
            if isinstance(e, PokeAPIError):
                raise
            raise PokeAPIError(f"Failed to fetch Pokémon by type {type_name}: {str(e)}")
    
    async def get_evolution_chain(self, pokemon_name: str) -> Optional[EvolutionChain]:
        """
        Get evolution chain for a Pokémon
        
        Args:
            pokemon_name: Name of the Pokémon
            
        Returns:
            EvolutionChain or None if not found
        """
        try:
            pokemon_data = await self._fetch_json(f"pokemon/{self._normalize_name(pokemon_name)}")
            species_data = await self._fetch_json(pokemon_data["species"]["url"].replace(self.base_url, ""))
            
            if not species_data.get("evolution_chain"):
                return None
                
            evolution_data = await self._fetch_json(species_data["evolution_chain"]["url"].replace(self.base_url, ""))
            
            def parse_evolution_chain(chain_data: Dict) -> EvolutionChain:
                """Recursively parse evolution chain data"""
                evolves_to = []
                
                for evolution in chain_data.get("evolves_to", []):
                    evolves_to.append(parse_evolution_chain(evolution))
                
                return EvolutionChain(
                    species_name=chain_data["species"]["name"],
                    evolves_to=evolves_to,
                    evolution_details=chain_data.get("evolution_details", [])
                )
            
            return parse_evolution_chain(evolution_data["chain"])
            
        except Exception as e:
            logger.warning(f"Failed to fetch evolution chain for {pokemon_name}: {str(e)}")
            return None
    
    async def search_pokemon(self, query: str, limit: int = 10) -> List[str]:
        """
        Search for Pokémon names matching query
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching Pokémon names
        """
        try:
            # Get list of all Pokémon (this endpoint is cached by PokeAPI)
            pokemon_list = await self._fetch_json("pokemon?limit=2000")
            
            query_lower = query.lower()
            matches = []
            
            for pokemon in pokemon_list["results"]:
                if query_lower in pokemon["name"] and len(matches) < limit:
                    matches.append(pokemon["name"])
            
            return matches
            
        except Exception as e:
            logger.warning(f"Pokemon search failed for query '{query}': {str(e)}")
            return []


# Convenience functions for common operations
async def fetch_pokemon(name_or_id: str) -> Pokemon:
    """Convenience function to fetch a single Pokémon"""
    async with PokeAPIClient() as client:
        return await client.get_pokemon(name_or_id)


async def fetch_multiple_pokemon(names_or_ids: List[str]) -> List[Pokemon]:
    """Convenience function to fetch multiple Pokémon concurrently"""
    async with PokeAPIClient() as client:
        tasks = [client.get_pokemon(identifier) for identifier in names_or_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        pokemon_list = []
        for result in results:
            if isinstance(result, Pokemon):
                pokemon_list.append(result)
            else:
                logger.warning(f"Failed to fetch Pokémon: {result}")
                
        return pokemon_list