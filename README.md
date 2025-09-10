# Pokemon MCP Server

A Model Context Protocol (MCP) server that provides Pokemon data resources and battle simulation tools.

## Project Structure

```
mcp_server/
├── app.py               # FastAPI application & MCP server
├── mcp_server/
│   ├── resources/
│   │   └── pokemon_resource.py  # Pokemon data resource
│   ├── tools/
│   │   └── battle_tool.py   # Battle simulation tool
│   └── utils/
│       ├── type_chart.py    # Type effectiveness calculations
│       ├── status_effects.py # Status effect implementations
│       └── pokeapi_client.py # PokeAPI integration with caching
├── start_server.sh      # Quick start script
├── test_all.sh         # Automated test suite
├── interactive_test.py  # Interactive testing tool
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Installation & Setup

1. Clone the repository or extract the project files:

   ```bash
   git clone https://github.com/amitabhsingh64/Pokemon_mcp.git
   cd Pokemon_mcp
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Quick Start

```bash
./start_server.sh
```

Or manually:

```bash
python app.py
```

The server will start on `http://localhost:8000`.

### Server Commands

```bash
python app.py          # Start the server
python app.py info     # Show server information
python app.py test     # Run component tests
```

## Testing

### Quick Test

```bash
# Run automated test suite
./test_all.sh

# Interactive testing
python interactive_test.py demo

# Test specific features
python interactive_test.py pokemon charizard
python interactive_test.py battle pikachu charizard --level 50
python interactive_test.py search fire
```

### Manual API Testing

```bash
# Test server status
curl "http://localhost:8000/health"

# Get Pokemon data
curl "http://localhost:8000/resource/pokemon/pikachu" | python -m json.tool

# List Pokemon
curl "http://localhost:8000/resource/pokemon/list?limit=10" | python -m json.tool

# Search Pokemon
curl "http://localhost:8000/resource/pokemon/search?q=fire" | python -m json.tool

# Compare Pokemon
curl "http://localhost:8000/resource/pokemon/compare?name1=charizard&name2=blastoise" | python -m json.tool

# Simulate battle (POST request)
curl -X POST "http://localhost:8000/tool/battle/simulate" \
     -H "Content-Type: application/json" \
     -d '{"pokemon1_name": "charizard", "pokemon2_name": "blastoise", "level": 50}' | python -m json.tool
```

## API Endpoints

### Resources (GET requests)

| Endpoint | Description | Example |
|----------|-------------|---------|
| `/` | Server information | Basic server details |
| `/resource/pokemon/{name}` | Pokemon details | `/resource/pokemon/pikachu` |
| `/resource/pokemon/list` | List Pokemon | `/resource/pokemon/list?limit=50` |
| `/resource/pokemon/search` | Search Pokemon | `/resource/pokemon/search?q=fire` |
| `/resource/pokemon/compare` | Compare Pokemon | `/resource/pokemon/compare?name1=a&name2=b` |
| `/resource/pokemon/types` | Type effectiveness chart | Complete type system |
| `/health` | Health check | Server status |
| `/cache/stats` | Cache statistics | Cache performance |

### Tools (POST requests)

| Endpoint | Description | Payload |
|----------|-------------|---------|
| `/tool/battle/simulate` | Simulate Pokemon battle | `{"pokemon1_name": "a", "pokemon2_name": "b", "level": 50}` |
| `/tool/battle/predict` | Predict battle outcome | `{"pokemon1_name": "a", "pokemon2_name": "b", "level": 50}` |

### Interactive Documentation

Visit `http://localhost:8000/docs` for interactive API documentation with Swagger UI.

## Features

### Pokemon Data Access
- **Complete Pokemon Information**: Stats, types, abilities, height, weight
- **Search Functionality**: Find Pokemon by name patterns  
- **Pokemon Comparison**: Side-by-side stat and type analysis
- **Type System**: Complete 18-type effectiveness chart
- **Caching**: Intelligent caching for optimal performance

### Battle Simulation
- **Realistic Battle Mechanics**: Generation-accurate damage calculations
- **Turn-based Combat**: Speed-based turn order, move execution
- **Status Effects**: Paralysis, Burn, Poison with proper mechanics
- **Type Effectiveness**: Full type chart with STAB bonuses
- **Battle Logging**: Detailed turn-by-turn battle records
- **Battle Prediction**: Quick statistical analysis without full simulation

### Battle Mechanics
- **Damage Formula**: `Damage = (((2×Level÷5+2)×Power×A÷D)÷50+2) × Modifiers`
- **STAB Bonus**: 1.5× damage for same-type moves
- **Critical Hits**: 1.5× damage with 1/24 base chance
- **Random Factor**: 85-100% damage variance
- **Status Effects**:
  - **Paralysis**: 25% skip turn, 50% speed reduction
  - **Burn**: 1/16 max HP damage/turn, 50% attack reduction  
  - **Poison**: 1/8 max HP damage/turn

## Usage Examples

### Get Pokemon Information
```bash
python interactive_test.py pokemon charizard
```

### Search for Pokemon
```bash
python interactive_test.py search "pika"
```

### Simulate a Battle
```bash
python interactive_test.py battle charizard blastoise --level 75
```

### Predict Battle Outcome
```bash
python interactive_test.py predict dragonite garchomp --level 100
```

### Run Interactive Demo
```bash
python interactive_test.py demo
```

## Claude Desktop Integration

To use with Claude Desktop, add this configuration to your `claude_desktop_config.json`:

### Windows
File location: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration
```json
{
  "mcpServers": {
    "pokemon-server": {
      "command": "python",
      "args": ["C:/path/to/Pokemon_mcp/app.py"],
      "env": {
        "PYTHONPATH": "C:/path/to/Pokemon_mcp"
      }
    }
  }
}
```

Replace `C:/path/to/Pokemon_mcp` with your actual project path.

### Restart Claude Desktop
Close and reopen Claude Desktop to load the MCP server.

### Test Integration
Ask Claude: *"Can you get information about Charizard using the Pokemon resource?"*

## Dependencies

### Core Dependencies
* **FastAPI** - Modern web framework for building APIs
* **httpx** - Async HTTP client for PokeAPI integration
* **pydantic** - Data validation and serialization
* **cachetools** - In-memory caching for performance
* **uvicorn** - ASGI server for running FastAPI

### Development Dependencies
* **rich** - Beautiful terminal output
* **click** - Command-line interface creation
* **pytest** - Testing framework

### Optional Dependencies
* **python-dotenv** - Environment variable management

## Performance

- **Caching**: Automatic caching of PokeAPI responses
- **Async Architecture**: Non-blocking I/O operations
- **Connection Pooling**: Efficient HTTP connection management
- **Rate Limiting**: Respectful API usage patterns

## Troubleshooting

### Server Won't Start
1. Check Python version (3.7+ required)
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Test with: `python app.py test`

### PokeAPI Connection Issues
1. Check internet connectivity
2. Verify PokeAPI is accessible: `curl https://pokeapi.co/api/v2/pokemon/pikachu`
3. Check server health: `curl http://localhost:8000/health`

### Claude Desktop Integration Issues
1. Verify file paths in configuration are correct
2. Check that Python and project are accessible
3. Restart Claude Desktop after configuration changes
4. Check Claude Desktop logs for errors

### Testing Issues
1. Make sure server is running before testing endpoints
2. Use `python interactive_test.py status` to check connectivity
3. Run `./test_all.sh` for comprehensive testing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `./test_all.sh`
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- **PokéAPI**: Comprehensive Pokemon data source (https://pokeapi.co/)
- **FastAPI**: Modern Python web framework
- **Anthropic**: Model Context Protocol specification
- **Nintendo/Game Freak**: Original Pokemon game mechanics

---

**Ready to battle!** 🎮⚡🔥💧🌱

Start the server with `./start_server.sh` and begin exploring the Pokemon world with AI assistance!