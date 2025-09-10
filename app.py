#!/usr/bin/env python3
"""
Pokemon MCP Server - FastAPI Application

A Model Context Protocol server that provides Pokemon data resources and battle simulation tools.
Combines FastAPI for HTTP endpoints with MCP protocol support.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import MCP components
from mcp_server.resources.pokemon_resource import PokemonResource
from mcp_server.tools.battle_tool import BattleTool
from mcp_server.utils.pokeapi_client import get_client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Pokemon MCP Server",
    description="Model Context Protocol server for Pokemon data and battle simulation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pokemon_resource = PokemonResource()
battle_tool = BattleTool()


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Pokemon MCP Server",
        "version": "1.0.0",
        "description": "Model Context Protocol server for Pokemon data and battle simulation",
        "endpoints": {
            "resources": [
                "/resource/pokemon/list",
                "/resource/pokemon/{name}",
                "/resource/pokemon/search",
                "/resource/pokemon/compare",
                "/resource/pokemon/types"
            ],
            "tools": [
                "/tool/battle/simulate",
                "/tool/battle/predict"
            ],
            "docs": "/docs"
        },
        "features": [
            "Complete Pokemon data from PokeAPI",
            "Realistic battle simulation",
            "Type effectiveness calculations",
            "Battle outcome predictions",
            "Caching for performance"
        ]
    }


# Resource Endpoints
@app.get("/resource/pokemon/list")
async def list_pokemon(limit: int = Query(151, ge=1, le=1000)):
    """List Pokemon names."""
    try:
        return await pokemon_resource.list_pokemon(limit)
    except Exception as e:
        logger.error(f"Failed to list Pokemon: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/resource/pokemon/{name}")
async def get_pokemon(name: str):
    """Get detailed Pokemon information."""
    return await pokemon_resource.get_pokemon(name)


@app.get("/resource/pokemon/search")
async def search_pokemon(q: str = Query(..., description="Search query")):
    """Search for Pokemon by name."""
    return await pokemon_resource.search_pokemon(q)


@app.get("/resource/pokemon/compare")
async def compare_pokemon(
    name1: str = Query(..., description="First Pokemon name"),
    name2: str = Query(..., description="Second Pokemon name")
):
    """Compare two Pokemon."""
    return await pokemon_resource.compare_pokemon(name1, name2)


@app.get("/resource/pokemon/types")
async def get_type_chart():
    """Get complete type effectiveness chart."""
    return await pokemon_resource.get_type_chart()


# Tool Endpoints
class BattleRequest(BaseModel):
    pokemon1_name: str
    pokemon2_name: str
    level: int = 50

@app.post("/tool/battle/simulate")
async def simulate_battle(request: BattleRequest):
    """Simulate a Pokemon battle."""
    return await battle_tool.simulate_battle(request.pokemon1_name, request.pokemon2_name, request.level)


@app.post("/tool/battle/predict")
async def predict_battle(request: BattleRequest):
    """Predict battle outcome without full simulation."""
    return await battle_tool.predict_battle(request.pokemon1_name, request.pokemon2_name, request.level)


# Utility Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test PokeAPI connection
        async with await get_client() as client:
            await client.get_pokemon("pikachu")
        
        return {
            "status": "healthy",
            "pokeapi": "connected",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        async with await get_client() as client:
            stats = client.get_cache_stats()
            return {
                "cache_stats": stats,
                "timestamp": asyncio.get_event_loop().time()
            }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Error Handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    logger.info("Pokemon MCP Server starting up...")
    
    # Test PokeAPI connection
    try:
        async with await get_client() as client:
            await client.get_pokemon("pikachu")
        logger.info("PokeAPI connection successful")
    except Exception as e:
        logger.warning(f"PokeAPI connection failed: {e}")
    
    logger.info("Pokemon MCP Server ready!")


@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Pokemon MCP Server shutting down...")


def main():
    """Run the server."""
    import sys
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            print("Testing server components...")
            
            # Test imports
            try:
                import httpx
                import fastapi
                import pydantic
                from mcp_server.utils.type_chart import get_type_effectiveness
                print("✓ All imports successful")
            except ImportError as e:
                print(f"✗ Import error: {e}")
                return 1
            
            # Test type system
            try:
                effectiveness = get_type_effectiveness("fire", "grass")
                assert effectiveness == 2.0, "Type effectiveness test failed"
                print("✓ Type system working")
            except Exception as e:
                print(f"✗ Type system error: {e}")
                return 1
            
            print("✓ All tests passed")
            return 0
            
        elif command == "info":
            print("Pokemon MCP Server")
            print("=" * 50)
            print("FastAPI-based MCP server for Pokemon data and battle simulation")
            print()
            print("Endpoints:")
            print("  GET  /                     - Server info")
            print("  GET  /resource/pokemon/{name} - Pokemon details")
            print("  GET  /resource/pokemon/list   - List Pokemon")
            print("  GET  /resource/pokemon/search - Search Pokemon")
            print("  POST /tool/battle/simulate    - Simulate battle")
            print("  POST /tool/battle/predict     - Predict battle")
            print("  GET  /health                  - Health check")
            print("  GET  /docs                    - API documentation")
            print()
            print("Quick start:")
            print("  python app.py              - Start server")
            print("  python app.py test         - Run tests")
            print("  python app.py info         - Show this info")
            return 0
    
    # Default: run the server
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting Pokemon MCP Server on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level="info"
    )


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        exit(exit_code)