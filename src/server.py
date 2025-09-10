#!/usr/bin/env python3
"""
Pokémon Battle Simulation MCP Server

A Model Context Protocol server that provides AI models with access to:
1. Comprehensive Pokémon data from PokeAPI
2. Battle simulation capabilities with realistic mechanics
3. Type effectiveness analysis and battle predictions

This server exposes resources for Pokémon data queries and tools for battle simulations,
allowing LLMs to understand and interact with the Pokémon world.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from fastmcp import FastMCP, Context
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from resources.pokemon_data import setup_pokemon_resources
from tools.battle_simulator import setup_battle_tools
from services.cache import get_global_cache, cleanup_global_cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pokemon_mcp.log') if os.getenv('ENABLE_LOGGING') == 'true' else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Server configuration
SERVER_NAME = os.getenv("SERVER_NAME", "pokemon-battle-mcp-server")
SERVER_VERSION = os.getenv("SERVER_VERSION", "1.0.0")

# Create FastMCP server instance
mcp = FastMCP(SERVER_NAME)


@mcp.tool
async def get_server_info(ctx: Context = None) -> Dict[str, Any]:
    """
    Get information about this MCP server
    
    Returns server capabilities, version info, and usage instructions.
    """
    if ctx:
        await ctx.info("Providing server information")
    
    return {
        "server_name": SERVER_NAME,
        "version": SERVER_VERSION,
        "description": "Pokémon Battle Simulation MCP Server - Provides comprehensive Pokémon data and battle simulation capabilities",
        "capabilities": {
            "resources": [
                "pokemon://list - List all available Pokémon",
                "pokemon://info/{name} - Get detailed Pokémon information",
                "pokemon://stats/{name} - Get Pokémon battle statistics",
                "pokemon://type/{type} - Get Pokémon by type",
                "pokemon://search/{query} - Search for Pokémon",
                "pokemon://compare/{name1}/{name2} - Compare two Pokémon",
                "pokemon://types - Get type effectiveness chart"
            ],
            "tools": [
                "simulate_battle - Simulate a battle between two Pokémon",
                "predict_battle_outcome - Predict battle results without full simulation",
                "battle_multiple_pokemon - Run tournaments or sequential battles",
                "get_server_info - Get server information and capabilities"
            ],
            "features": [
                "Accurate Generation 9 damage calculations",
                "Type effectiveness system with all 18 types",
                "Status effects (Paralysis, Burn, Poison)",
                "Critical hit mechanics and STAB bonuses",
                "Comprehensive battle logging",
                "Data caching for optimal performance",
                "Support for levels 1-100",
                "Tournament-style multi-Pokémon battles"
            ]
        },
        "data_source": "PokéAPI (https://pokeapi.co/)",
        "usage_examples": {
            "get_pokemon_info": "Use resource pokemon://info/pikachu",
            "simulate_battle": "Use tool simulate_battle with pokemon1_name='charizard' and pokemon2_name='blastoise'",
            "type_analysis": "Use resource pokemon://type/fire to get all Fire-type Pokémon",
            "battle_prediction": "Use tool predict_battle_outcome for quick matchup analysis"
        },
        "battle_mechanics": {
            "damage_formula": "Generation 9 standard formula with level, stats, type effectiveness, STAB, and random factor",
            "type_system": "Complete 18-type chart with immunities, resistances, and weaknesses",
            "status_effects": ["Paralysis (25% skip chance, -50% speed)", "Burn (1/16 HP damage, -50% attack)", "Poison (1/8 HP damage)"],
            "critical_hits": "1.5x damage with 1/24 base rate",
            "stab_bonus": "1.5x damage for same-type moves"
        }
    }


@mcp.tool
async def cleanup_cache(ctx: Context = None) -> Dict[str, Any]:
    """
    Clean up expired cache entries
    
    Removes expired Pokemon data from both memory and file caches to free up space.
    """
    if ctx:
        await ctx.info("Cleaning up expired cache entries...")
    
    try:
        cleanup_results = await cleanup_global_cache()
        
        total_cleaned = cleanup_results.get("memory", 0) + cleanup_results.get("file", 0)
        
        if ctx:
            await ctx.info(f"Cache cleanup complete: {total_cleaned} expired entries removed")
        
        return {
            "status": "success",
            "cleaned_entries": cleanup_results,
            "total_cleaned": total_cleaned,
            "message": f"Successfully cleaned up {total_cleaned} expired cache entries"
        }
        
    except Exception as e:
        error_msg = f"Cache cleanup failed: {str(e)}"
        logger.error(error_msg)
        if ctx:
            await ctx.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }


@mcp.tool
async def get_cache_stats(ctx: Context = None) -> Dict[str, Any]:
    """
    Get cache statistics and status
    
    Returns information about cache usage and performance.
    """
    if ctx:
        await ctx.info("Retrieving cache statistics...")
    
    try:
        cache = get_global_cache()
        
        # Get cache sizes (this is a simplified version)
        memory_size = await cache.memory_cache.size()
        
        return {
            "cache_status": "active",
            "memory_cache_entries": memory_size,
            "cache_directory": str(cache.file_cache.cache_dir),
            "memory_ttl_seconds": cache.memory_ttl,
            "file_ttl_seconds": cache.file_ttl,
            "max_memory_size": cache.max_memory_size
        }
        
    except Exception as e:
        error_msg = f"Failed to get cache stats: {str(e)}"
        logger.error(error_msg)
        if ctx:
            await ctx.error(error_msg)
        return {
            "error": error_msg
        }


# Setup resources and tools
setup_pokemon_resources(mcp)
setup_battle_tools(mcp)

logger.info(f"Pokémon MCP Server initialized with {len(mcp._resources)} resources and {len(mcp._tools)} tools")


async def main():
    """Main entry point for the MCP server"""
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    
    try:
        # Initialize cache
        cache = get_global_cache()
        logger.info("Cache system initialized")
        
        # Run the MCP server
        await mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Server shutting down...")


if __name__ == "__main__":
    # Handle different invocation methods
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "info":
            # Print server info and exit
            print(f"Pokémon Battle Simulation MCP Server v{SERVER_VERSION}")
            print("=" * 50)
            print("A Model Context Protocol server for Pokémon data and battle simulation")
            print()
            print("Resources:")
            print("  - pokemon://list - List all Pokémon")
            print("  - pokemon://info/{name} - Detailed Pokémon information")
            print("  - pokemon://stats/{name} - Battle statistics")
            print("  - pokemon://type/{type} - Pokémon by type")
            print("  - pokemon://search/{query} - Search Pokémon")
            print("  - pokemon://compare/{name1}/{name2} - Compare Pokémon")
            print("  - pokemon://types - Type effectiveness chart")
            print()
            print("Tools:")
            print("  - simulate_battle - Full battle simulation")
            print("  - predict_battle_outcome - Quick battle prediction")
            print("  - battle_multiple_pokemon - Tournament battles")
            print("  - get_server_info - Server capabilities")
            print()
            print("Data Source: PokéAPI (https://pokeapi.co/)")
            print("Battle System: Generation 9 mechanics")
            sys.exit(0)
            
        elif command == "test":
            # Run a quick test
            print("Testing server components...")
            
            # Test imports
            try:
                from services.pokeapi import PokeAPIClient
                from battle.engine import BattleEngine
                from battle.types import PokemonTypes
                print("✓ All imports successful")
            except ImportError as e:
                print(f"✗ Import error: {e}")
                sys.exit(1)
            
            # Test type system
            try:
                types = PokemonTypes()
                effectiveness = types.get_effectiveness("fire", "grass")
                assert effectiveness == 2.0, "Type effectiveness test failed"
                print("✓ Type system working")
            except Exception as e:
                print(f"✗ Type system error: {e}")
                sys.exit(1)
            
            print("✓ All tests passed")
            sys.exit(0)
    
    # Default: run the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)