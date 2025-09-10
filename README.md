# Pokémon Battle Simulation MCP Server

A comprehensive Model Context Protocol (MCP) server that provides AI models with access to Pokémon data and realistic battle simulation capabilities.

## 🎯 Overview

This MCP server bridges the gap between AI models and the Pokémon world by providing:

- **Comprehensive Pokémon Data Access**: Complete information about 800+ Pokémon including stats, types, abilities, moves, and evolution chains
- **Realistic Battle Simulation**: Full battle engine with Generation 9 mechanics, type effectiveness, status effects, and damage calculations
- **Advanced Analytics**: Battle predictions, type matchup analysis, and tournament simulations

## ⚡ Quick Start

### Prerequisites

- Python 3.10 or higher
- Internet connection (for PokeAPI access)

### Installation

1. Clone or extract the project:
```bash
cd POKEMON_MCP
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Server

1. Basic server start:
```bash
python src/server.py
```

2. Get server information:
```bash
python src/server.py info
```

3. Run component tests:
```bash
python src/server.py test
```

4. Run unit tests:
```bash
pytest tests/ -v
```

## 📚 Features

### Part 1: Pokémon Data Resource

The server exposes comprehensive Pokémon data through MCP resources:

#### Available Resources

| Resource URI | Description | Example |
|-------------|-------------|---------|
| `pokemon://list` | List all available Pokémon | Get first 151 Pokémon |
| `pokemon://info/{name}` | Detailed Pokémon information | `pokemon://info/charizard` |
| `pokemon://stats/{name}` | Battle statistics & analysis | `pokemon://stats/pikachu` |
| `pokemon://type/{type}` | Pokémon by type | `pokemon://type/fire` |
| `pokemon://search/{query}` | Search Pokémon by name | `pokemon://search/pika` |
| `pokemon://compare/{name1}/{name2}` | Compare two Pokémon | `pokemon://compare/charizard/blastoise` |
| `pokemon://types` | Complete type effectiveness chart | All type relationships |

#### Example Resource Queries

**Get Pokémon Information:**
```json
{
  "name": "charizard",
  "types": ["fire", "flying"],
  "stats": {
    "hp": 78,
    "attack": 84,
    "defense": 78,
    "special_attack": 109,
    "special_defense": 85,
    "speed": 100,
    "total": 534
  },
  "battle_info": {
    "weaknesses": {"rock": 4.0, "electric": 2.0, "water": 2.0},
    "resistances": {"fire": 0.5, "grass": 0.25, "fighting": 0.5},
    "immunities": ["ground"]
  }
}
```

### Part 2: Battle Simulation Tools

The server provides advanced battle simulation through MCP tools:

#### Available Tools

| Tool | Description | Key Features |
|------|-------------|--------------|
| `simulate_battle` | Full battle simulation | Turn-by-turn logs, realistic mechanics |
| `predict_battle_outcome` | Quick battle prediction | Statistical analysis, no full simulation |
| `battle_multiple_pokemon` | Tournament battles | Round-robin or elimination formats |
| `get_server_info` | Server capabilities | Available resources and tools |

#### Example Battle Simulation

```python
# Simulate Charizard vs Blastoise
{
  "pokemon1_name": "charizard",
  "pokemon2_name": "blastoise", 
  "level": 50,
  "detailed_log": true
}
```

**Sample Battle Result:**
```json
{
  "battle_result": {
    "winner": "blastoise",
    "loser": "charizard",
    "total_turns": 8,
    "victory_type": "knockout"
  },
  "battle_summary": {
    "total_actions": 12,
    "critical_hits": 2,
    "status_effects_applied": 1,
    "average_damage": 67.3,
    "type_advantages": {
      "super_effective": 3,
      "not_very_effective": 1
    }
  },
  "detailed_log": [
    {
      "turn": 1,
      "action": "attack",
      "attacker": "blastoise",
      "move_used": "surf",
      "damage": 156,
      "effectiveness": "super effective",
      "message": "Blastoise used Surf! It's super effective!"
    }
  ]
}
```

## 🔧 Battle Mechanics

### Damage Calculation

Implements the Generation 9 Pokémon damage formula:

```
Damage = (((2 × Level ÷ 5 + 2) × Power × A ÷ D) ÷ 50 + 2) × Modifiers
```

**Modifiers include:**
- **STAB (Same Type Attack Bonus)**: 1.5× for matching types
- **Type Effectiveness**: 0× to 4× based on type chart
- **Critical Hits**: 1.5× damage with 1/24 base rate
- **Random Factor**: 85-100% variance
- **Status Effects**: Burn reduces Attack by 50%
- **Weather Effects**: Rain boosts Water moves, etc.

### Type System

Complete 18-type effectiveness chart:
- **18 Types**: Normal, Fire, Water, Electric, Grass, Ice, Fighting, Poison, Ground, Flying, Psychic, Bug, Rock, Ghost, Dragon, Dark, Steel, Fairy
- **Effectiveness Values**: 0× (immune), 0.5× (not very effective), 1× (normal), 2× (super effective)
- **Dual-Type Support**: Multiplies effectiveness against both types

### Status Effects

Three core status effects implemented:

| Status | Effect | Duration |
|--------|--------|----------|
| **Paralysis** | 25% skip turn, -50% Speed | Until cured |
| **Burn** | 1/16 max HP damage/turn, -50% Attack | Until cured |
| **Poison** | 1/8 max HP damage/turn | Until cured |

### Battle Flow

1. **Setup Phase**: Initialize Pokémon at specified level
2. **Turn Order**: Determined by Speed stats (with paralysis effects)
3. **Action Phase**: Move selection and execution
4. **Damage Resolution**: Calculate and apply damage
5. **Status Processing**: Apply start/end-of-turn status effects
6. **Victory Check**: Battle ends when one Pokémon faints

## 🏗️ Architecture

### Project Structure

```
POKEMON_MCP/
├── src/
│   ├── server.py              # Main MCP server entry point
│   ├── models/
│   │   └── pokemon.py         # Pydantic data models
│   ├── resources/
│   │   └── pokemon_data.py    # MCP resource handlers
│   ├── tools/
│   │   └── battle_simulator.py # MCP battle tools
│   ├── services/
│   │   ├── pokeapi.py         # PokeAPI client
│   │   └── cache.py           # Caching system
│   └── battle/
│       ├── engine.py          # Battle simulation engine
│       ├── calculator.py      # Damage calculations
│       ├── types.py           # Type effectiveness system
│       └── status.py          # Status effect handlers
├── tests/                     # Unit tests
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

### Key Components

#### 1. Data Layer
- **PokeAPIClient**: Async HTTP client for PokeAPI integration
- **CachedPokeAPIClient**: Hybrid memory/file caching system
- **Pydantic Models**: Type-safe data structures

#### 2. Battle System
- **BattleEngine**: Orchestrates complete battles
- **DamageCalculator**: Implements damage formulas
- **StatusManager**: Handles status effect logic
- **PokemonTypes**: Type effectiveness calculations

#### 3. MCP Interface
- **FastMCP**: High-level MCP framework
- **Resources**: Data query endpoints
- **Tools**: Battle simulation functions

### Performance Optimizations

- **Hybrid Caching**: Memory + file-based caching with TTL
- **Async Architecture**: Non-blocking I/O operations
- **Request Batching**: Concurrent API calls
- **Data Validation**: Pydantic for fast serialization
- **Connection Pooling**: Persistent HTTP connections

## 📝 Usage Examples

### LLM Resource Queries

**Get Pokémon List:**
```
Query: pokemon://list
Returns: List of 151 Pokémon with basic info
```

**Analyze a Pokémon:**
```
Query: pokemon://info/garchomp
Returns: Complete stats, types, abilities, moves, weaknesses
```

**Type Matchup:**
```
Query: pokemon://compare/lucario/metagross
Returns: Stat comparison, type advantages, battle prediction
```

### Battle Simulations

**Basic Battle:**
```python
simulate_battle(
    pokemon1_name="charizard",
    pokemon2_name="venusaur",
    level=75
)
```

**Tournament Mode:**
```python
battle_multiple_pokemon(
    pokemon_list=["charizard", "blastoise", "venusaur", "pikachu"],
    level=50,
    tournament_style=True
)
```

**Quick Analysis:**
```python
predict_battle_outcome(
    pokemon1_name="dragonite", 
    pokemon2_name="garchomp",
    level=100
)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_battle.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

- **Battle Mechanics**: Damage calculations, type effectiveness, status effects
- **PokeAPI Integration**: HTTP client, error handling, data parsing
- **Caching System**: Memory and file cache operations
- **MCP Interface**: Resource and tool functionality

### Manual Testing

```bash
# Test server components
python src/server.py test

# Get server info
python src/server.py info
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (optional):

```env
# Server settings
SERVER_NAME=pokemon-battle-mcp-server
SERVER_VERSION=1.0.0

# PokeAPI settings  
POKEAPI_BASE_URL=https://pokeapi.co/api/v2
CACHE_TTL_SECONDS=3600

# Performance settings
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT_SECONDS=30

# Logging
ENABLE_LOGGING=true
```

### Cache Configuration

The caching system automatically:
- Stores Pokémon data for 1 hour (configurable)
- Uses hybrid memory/file storage
- Cleans up expired entries
- Handles up to 100 items in memory

## 🚀 Advanced Features

### Tournament Simulations

Run complex multi-Pokémon battles:

```python
# Round-robin tournament
battle_multiple_pokemon([
    "charizard", "blastoise", "venusaur", 
    "pikachu", "lucario", "garchomp"
], tournament_style=True)

# Elimination bracket
battle_multiple_pokemon([
    "rayquaza", "mewtwo", "arceus", "dialga"
], tournament_style=False)
```

### Battle Predictions

Get statistical analysis without full simulation:

```python
predict_battle_outcome("metagross", "garchomp")
# Returns win probabilities, key factors, reasoning
```

### Data Analytics

Comprehensive Pokémon analysis:

```python
# Type effectiveness analysis
GET pokemon://type/dragon
# Returns all Dragon types with offensive/defensive analysis

# Stat comparison
GET pokemon://compare/alakazam/mewtwo  
# Returns detailed stat breakdown and battle factors
```

## 📊 API Reference

### MCP Resources

All resources return JSON data optimized for LLM consumption:

- **Error Handling**: Graceful degradation with error messages
- **Data Validation**: Pydantic models ensure data integrity  
- **Caching**: Automatic performance optimization
- **Rate Limiting**: Respectful API usage

### MCP Tools

All tools support FastMCP Context for logging and progress updates:

- **Async Support**: Non-blocking operations
- **Error Recovery**: Robust error handling
- **Detailed Logging**: Turn-by-turn battle logs
- **Flexible Parameters**: Customizable battle conditions

## 🤝 Contributing

### Development Setup

1. Clone the repository
2. Set up virtual environment
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```
4. Run tests to ensure everything works
5. Start developing!

### Code Style

- **Formatting**: Black (line length 88)
- **Linting**: Ruff with standard rules
- **Type Hints**: MyPy for static type checking
- **Testing**: Pytest with async support

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- **PokéAPI**: Comprehensive Pokémon data source (https://pokeapi.co/)
- **FastMCP**: High-level MCP framework for Python
- **Anthropic**: Model Context Protocol specification
- **Nintendo/Game Freak**: Original Pokémon game mechanics

## 🐛 Support

For issues, questions, or contributions:

1. Check the existing documentation
2. Run `python src/server.py test` to verify setup
3. Review logs in `pokemon_mcp.log`
4. Create detailed issue reports with:
   - Python version
   - Error messages
   - Steps to reproduce
   - Expected vs actual behavior

---

**Happy battling!** 🎮⚡🔥💧🌱

*This MCP server brings the excitement of Pokémon battles to AI models with scientifically accurate battle mechanics and comprehensive data access.*