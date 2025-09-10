"""PokeAPI client with caching for Pokemon data retrieval."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from cachetools import TTLCache
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PokemonData(BaseModel):
    """Pokemon data model."""
    id: int
    name: str
    types: List[str]
    stats: Dict[str, int]
    abilities: List[str]
    height: int
    weight: int


class PokeAPIClient:
    """Async client for PokeAPI with caching."""
    
    def __init__(self, cache_ttl: int = 3600, cache_maxsize: int = 1000):
        self.base_url = "https://pokeapi.co/api/v2"
        self.cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        return self._client
    
    async def get_pokemon(self, identifier: str) -> PokemonData:
        """Get Pokemon data by name or ID."""
        cache_key = f"pokemon:{identifier.lower()}"
        
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {identifier}")
            return self.cache[cache_key]
        
        try:
            # Fetch Pokemon data
            response = await self.client.get(f"/pokemon/{identifier.lower()}")
            response.raise_for_status()
            data = response.json()
            
            # Parse Pokemon data
            pokemon = PokemonData(
                id=data["id"],
                name=data["name"],
                types=[t["type"]["name"] for t in data["types"]],
                stats={
                    stat["stat"]["name"].replace("-", "_"): stat["base_stat"]
                    for stat in data["stats"]
                },
                abilities=[
                    ability["ability"]["name"] 
                    for ability in data["abilities"]
                ],
                height=data["height"],
                weight=data["weight"]
            )
            
            # Cache the result
            self.cache[cache_key] = pokemon
            logger.debug(f"Cached Pokemon data for {identifier}")
            
            return pokemon
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Pokemon '{identifier}' not found")
            raise RuntimeError(f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch Pokemon {identifier}: {e}")
            raise
    
    async def search_pokemon(self, query: str, limit: int = 20) -> List[str]:
        """Search for Pokemon names matching query."""
        cache_key = f"search:{query.lower()}:{limit}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get Pokemon list (first 1000 for search)
            response = await self.client.get("/pokemon?limit=1000")
            response.raise_for_status()
            data = response.json()
            
            # Filter Pokemon names
            query_lower = query.lower()
            matches = [
                pokemon["name"] 
                for pokemon in data["results"]
                if query_lower in pokemon["name"]
            ][:limit]
            
            # Cache results
            self.cache[cache_key] = matches
            return matches
            
        except Exception as e:
            logger.error(f"Failed to search Pokemon: {e}")
            return []
    
    async def get_type_effectiveness(self, attacking_type: str) -> Dict[str, float]:
        """Get type effectiveness for an attacking type."""
        cache_key = f"type:{attacking_type.lower()}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            response = await self.client.get(f"/type/{attacking_type.lower()}")
            response.raise_for_status()
            data = response.json()
            
            effectiveness = {}
            
            # Super effective (2x)
            for relation in data["damage_relations"]["double_damage_to"]:
                effectiveness[relation["name"]] = 2.0
            
            # Not very effective (0.5x)
            for relation in data["damage_relations"]["half_damage_to"]:
                effectiveness[relation["name"]] = 0.5
            
            # No effect (0x)
            for relation in data["damage_relations"]["no_damage_to"]:
                effectiveness[relation["name"]] = 0.0
            
            # Cache results
            self.cache[cache_key] = effectiveness
            return effectiveness
            
        except Exception as e:
            logger.error(f"Failed to get type effectiveness: {e}")
            return {}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_maxsize": self.cache.maxsize,
            "cache_ttl": self.cache.ttl,
            "hit_rate": getattr(self.cache, 'hits', 0) / max(getattr(self.cache, 'hits', 0) + getattr(self.cache, 'misses', 0), 1)
        }


# Global client instance
_client_instance: Optional[PokeAPIClient] = None

async def get_client() -> PokeAPIClient:
    """Get or create global PokeAPI client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = PokeAPIClient()
    return _client_instance