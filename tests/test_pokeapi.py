"""
Unit tests for PokeAPI client
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.pokeapi import PokeAPIClient, PokeAPIError
from models.pokemon import Pokemon, PokemonStats


class TestPokeAPIClient:
    """Test the PokeAPI client"""
    
    @pytest.fixture
    async def client(self):
        """Create a test client"""
        async with PokeAPIClient() as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client context manager"""
        async with PokeAPIClient() as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)
    
    def test_normalize_name(self):
        """Test name normalization"""
        client = PokeAPIClient()
        
        assert client._normalize_name("Pikachu") == "pikachu"
        assert client._normalize_name("Mr. Mime") == "mr.-mime"
        assert client._normalize_name("Nidoran♀") == "nidoran♀"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_fetch_json_success(self, mock_get):
        """Test successful JSON fetch"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"name": "pikachu", "id": 25}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        async with PokeAPIClient() as client:
            result = await client._fetch_json("pokemon/pikachu")
            
        assert result == {"name": "pikachu", "id": 25}
        mock_get.assert_called_once_with("pokemon/pikachu")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_fetch_json_404_error(self, mock_get):
        """Test 404 error handling"""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        mock_get.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        
        async with PokeAPIClient() as client:
            with pytest.raises(PokeAPIError) as exc_info:
                await client._fetch_json("pokemon/nonexistent")
            
            assert "Resource not found" in str(exc_info.value)
    
    def test_extract_stat_value(self):
        """Test stat value extraction"""
        client = PokeAPIClient()
        
        stats_data = [
            {"stat": {"name": "hp"}, "base_stat": 35},
            {"stat": {"name": "attack"}, "base_stat": 55},
            {"stat": {"name": "defense"}, "base_stat": 40},
        ]
        
        assert client._extract_stat_value(stats_data, "hp") == 35
        assert client._extract_stat_value(stats_data, "attack") == 55
        assert client._extract_stat_value(stats_data, "speed") == 0  # Not in data
    
    @pytest.mark.asyncio
    @patch('services.pokeapi.PokeAPIClient._fetch_json')
    async def test_get_pokemon_success(self, mock_fetch):
        """Test successful Pokemon fetch"""
        # Mock Pokemon data
        pokemon_data = {
            "id": 25,
            "name": "pikachu",
            "height": 4,
            "weight": 60,
            "base_experience": 112,
            "types": [
                {"slot": 1, "type": {"name": "electric"}}
            ],
            "abilities": [
                {"ability": {"name": "static", "url": "test"}, "is_hidden": False, "slot": 1}
            ],
            "stats": [
                {"stat": {"name": "hp"}, "base_stat": 35},
                {"stat": {"name": "attack"}, "base_stat": 55},
                {"stat": {"name": "defense"}, "base_stat": 40},
                {"stat": {"name": "special-attack"}, "base_stat": 50},
                {"stat": {"name": "special-defense"}, "base_stat": 50},
                {"stat": {"name": "speed"}, "base_stat": 90},
            ],
            "moves": [
                {
                    "move": {"name": "thundershock", "url": "test"},
                    "version_group_details": [
                        {"move_learn_method": {"name": "level-up"}, "level_learned_at": 1}
                    ]
                }
            ],
            "species": {"url": "https://pokeapi.co/api/v2/pokemon-species/25/"}
        }
        
        species_data = {
            "name": "pikachu",
            "evolution_chain": {"url": "test"}
        }
        
        mock_fetch.side_effect = [pokemon_data, species_data]
        
        async with PokeAPIClient() as client:
            pokemon = await client.get_pokemon("pikachu")
        
        assert isinstance(pokemon, Pokemon)
        assert pokemon.name == "pikachu"
        assert pokemon.id == 25
        assert pokemon.types == ["electric"]
        assert pokemon.stats.hp == 35
        assert pokemon.stats.attack == 55
        assert pokemon.stats.speed == 90
        assert len(pokemon.abilities) == 1
        assert pokemon.abilities[0].name == "static"
    
    @pytest.mark.asyncio
    @patch('services.pokeapi.PokeAPIClient._fetch_json')
    async def test_get_move_details_success(self, mock_fetch):
        """Test successful move details fetch"""
        move_data = {
            "name": "thunderbolt",
            "power": 90,
            "accuracy": 100,
            "pp": 15,
            "priority": 0,
            "damage_class": {"name": "special"},
            "type": {"name": "electric"},
            "target": {"name": "selected-pokemon"},
            "effect_chance": 10,
            "effect_entries": []
        }
        
        mock_fetch.return_value = move_data
        
        async with PokeAPIClient() as client:
            move = await client.get_move_details("thunderbolt")
        
        assert move.name == "thunderbolt"
        assert move.power == 90
        assert move.accuracy == 100
        assert move.damage_class == "special"
        assert move.type == "electric"
    
    @pytest.mark.asyncio
    @patch('services.pokeapi.PokeAPIClient._fetch_json')
    async def test_get_type_effectiveness(self, mock_fetch):
        """Test type effectiveness fetch"""
        type_data = {
            "damage_relations": {
                "double_damage_to": [
                    {"name": "water"}, {"name": "flying"}
                ],
                "half_damage_to": [
                    {"name": "electric"}, {"name": "grass"}
                ],
                "no_damage_to": [
                    {"name": "ground"}
                ]
            }
        }
        
        mock_fetch.return_value = type_data
        
        async with PokeAPIClient() as client:
            effectiveness = await client.get_type_effectiveness("electric")
        
        assert effectiveness["water"] == 2.0
        assert effectiveness["flying"] == 2.0
        assert effectiveness["electric"] == 0.5
        assert effectiveness["grass"] == 0.5
        assert effectiveness["ground"] == 0.0
    
    @pytest.mark.asyncio
    @patch('services.pokeapi.PokeAPIClient._fetch_json')
    async def test_get_pokemon_by_type(self, mock_fetch):
        """Test getting Pokemon by type"""
        type_data = {
            "pokemon": [
                {"pokemon": {"name": "charmander"}},
                {"pokemon": {"name": "charmeleon"}},
                {"pokemon": {"name": "charizard"}},
            ]
        }
        
        mock_fetch.return_value = type_data
        
        async with PokeAPIClient() as client:
            pokemon_list = await client.get_pokemon_by_type("fire", limit=2)
        
        assert len(pokemon_list) == 2
        assert "charmander" in pokemon_list
        assert "charmeleon" in pokemon_list
    
    @pytest.mark.asyncio
    @patch('services.pokeapi.PokeAPIClient._fetch_json')
    async def test_search_pokemon(self, mock_fetch):
        """Test Pokemon search"""
        pokemon_list_data = {
            "results": [
                {"name": "pikachu"}, {"name": "pichu"}, {"name": "raichu"},
                {"name": "bulbasaur"}, {"name": "charmander"}
            ]
        }
        
        mock_fetch.return_value = pokemon_list_data
        
        async with PokeAPIClient() as client:
            results = await client.search_pokemon("pik", limit=5)
        
        # Should match names containing "pik"
        assert "pikachu" in results
        assert len(results) <= 5


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    @patch('services.pokeapi.PokeAPIClient')
    async def test_fetch_pokemon(self, mock_client_class):
        """Test convenience function for fetching single Pokemon"""
        from services.pokeapi import fetch_pokemon
        
        # Mock client and its methods
        mock_client = AsyncMock()
        mock_pokemon = Mock(spec=Pokemon)
        mock_pokemon.name = "pikachu"
        mock_client.get_pokemon.return_value = mock_pokemon
        
        # Mock context manager
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        result = await fetch_pokemon("pikachu")
        
        assert result.name == "pikachu"
        mock_client.get_pokemon.assert_called_once_with("pikachu")
    
    @pytest.mark.asyncio
    @patch('services.pokeapi.PokeAPIClient')
    async def test_fetch_multiple_pokemon(self, mock_client_class):
        """Test convenience function for fetching multiple Pokemon"""
        from services.pokeapi import fetch_multiple_pokemon
        
        # Mock client and Pokemon
        mock_client = AsyncMock()
        
        mock_pokemon1 = Mock(spec=Pokemon)
        mock_pokemon1.name = "pikachu"
        
        mock_pokemon2 = Mock(spec=Pokemon)
        mock_pokemon2.name = "charizard"
        
        # Mock get_pokemon to return different Pokemon based on input
        async def mock_get_pokemon(name):
            if name == "pikachu":
                return mock_pokemon1
            elif name == "charizard":
                return mock_pokemon2
            else:
                raise PokeAPIError("Not found")
        
        mock_client.get_pokemon.side_effect = mock_get_pokemon
        
        # Mock context manager
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        results = await fetch_multiple_pokemon(["pikachu", "charizard", "nonexistent"])
        
        # Should return the two successful fetches
        assert len(results) == 2
        assert results[0].name == "pikachu"
        assert results[1].name == "charizard"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])