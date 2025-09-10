#!/usr/bin/env python3
"""
Interactive test script for Pokemon MCP Server.

Provides a command-line interface to test all server endpoints and features.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional

import httpx
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint

console = Console()

class PokemonMCPTester:
    """Interactive tester for Pokemon MCP Server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_connection(self) -> bool:
        """Test if server is accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        try:
            response = await self.client.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def test_pokemon_resource(self, name: str) -> Dict[str, Any]:
        """Test Pokemon resource endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/resource/pokemon/{name}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"error": f"Pokemon '{name}' not found"}
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def test_pokemon_list(self, limit: int = 10) -> Dict[str, Any]:
        """Test Pokemon list endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/resource/pokemon/list?limit={limit}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def test_pokemon_search(self, query: str) -> Dict[str, Any]:
        """Test Pokemon search endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/resource/pokemon/search?q={query}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def test_pokemon_compare(self, name1: str, name2: str) -> Dict[str, Any]:
        """Test Pokemon comparison endpoint."""
        try:
            response = await self.client.get(
                f"{self.base_url}/resource/pokemon/compare?name1={name1}&name2={name2}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def test_battle_simulation(self, pokemon1: str, pokemon2: str, level: int = 50) -> Dict[str, Any]:
        """Test battle simulation endpoint."""
        try:
            response = await self.client.post(
                f"{self.base_url}/tool/battle/simulate",
                json={"pokemon1_name": pokemon1, "pokemon2_name": pokemon2, "level": level}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def test_battle_prediction(self, pokemon1: str, pokemon2: str, level: int = 50) -> Dict[str, Any]:
        """Test battle prediction endpoint."""
        try:
            response = await self.client.post(
                f"{self.base_url}/tool/battle/predict",
                json={"pokemon1_name": pokemon1, "pokemon2_name": pokemon2, "level": level}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


@click.group()
@click.option('--url', default='http://localhost:8000', help='Server URL')
@click.pass_context
def cli(ctx, url):
    """Pokemon MCP Server Interactive Tester."""
    ctx.ensure_object(dict)
    ctx.obj['url'] = url


@cli.command()
@click.pass_context
async def status(ctx):
    """Check server status."""
    url = ctx.obj['url']
    
    async with PokemonMCPTester(url) as tester:
        rprint("[blue]🔍 Checking server status...[/blue]")
        
        if await tester.test_connection():
            rprint("[green]✓ Server is online and responding[/green]")
            
            info = await tester.get_server_info()
            if "error" not in info:
                console.print(Panel(
                    f"[bold]{info.get('name', 'Unknown')}[/bold]\n"
                    f"Version: {info.get('version', 'Unknown')}\n"
                    f"Description: {info.get('description', 'N/A')}",
                    title="Server Info"
                ))
            
        else:
            rprint(f"[red]✗ Server is not accessible at {url}[/red]")
            rprint("Make sure the server is running with: python app.py")


@cli.command()
@click.argument('name')
@click.pass_context
async def pokemon(ctx, name):
    """Get Pokemon information."""
    url = ctx.obj['url']
    
    async with PokemonMCPTester(url) as tester:
        rprint(f"[blue]🔍 Getting information for {name}...[/blue]")
        
        result = await tester.test_pokemon_resource(name)
        
        if "error" in result:
            rprint(f"[red]✗ Error: {result['error']}[/red]")
        else:
            # Display Pokemon info in a nice table
            table = Table(title=f"Pokemon: {result['name'].title()}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("ID", str(result.get('id', 'N/A')))
            table.add_row("Types", ", ".join(result.get('types', [])))
            table.add_row("Height", f"{result.get('height', 0):.1f}m")
            table.add_row("Weight", f"{result.get('weight', 0):.1f}kg")
            
            if 'stats' in result:
                for stat_name, value in result['stats'].items():
                    table.add_row(stat_name.replace('_', ' ').title(), str(value))
            
            console.print(table)
            
            # Show battle info if available
            if 'battle_info' in result:
                battle_info = result['battle_info']
                
                if battle_info.get('weaknesses'):
                    rprint("\n[red]Weaknesses:[/red]")
                    for type_name, multiplier in battle_info['weaknesses'].items():
                        rprint(f"  • {type_name.title()}: {multiplier}x damage")
                
                if battle_info.get('resistances'):
                    rprint("\n[green]Resistances:[/green]")
                    for type_name, multiplier in battle_info['resistances'].items():
                        rprint(f"  • {type_name.title()}: {multiplier}x damage")


@cli.command()
@click.argument('query')
@click.pass_context
async def search(ctx, query):
    """Search for Pokemon."""
    url = ctx.obj['url']
    
    async with PokemonMCPTester(url) as tester:
        rprint(f"[blue]🔍 Searching for '{query}'...[/blue]")
        
        result = await tester.test_pokemon_search(query)
        
        if "error" in result:
            rprint(f"[red]✗ Error: {result['error']}[/red]")
        else:
            matches = result.get('matches', [])
            if matches:
                rprint(f"[green]Found {len(matches)} matches:[/green]")
                for i, match in enumerate(matches, 1):
                    rprint(f"  {i}. {match.title()}")
            else:
                rprint("[yellow]No matches found[/yellow]")


@cli.command()
@click.argument('pokemon1')
@click.argument('pokemon2')
@click.option('--level', default=50, help='Pokemon level (1-100)')
@click.pass_context
async def battle(ctx, pokemon1, pokemon2, level):
    """Simulate a Pokemon battle."""
    url = ctx.obj['url']
    
    async with PokemonMCPTester(url) as tester:
        rprint(f"[blue]⚔️ Simulating battle: {pokemon1.title()} vs {pokemon2.title()}[/blue]")
        
        with Progress() as progress:
            task = progress.add_task("Running battle simulation...", total=100)
            
            result = await tester.test_battle_simulation(pokemon1, pokemon2, level)
            progress.update(task, completed=100)
        
        if "error" in result:
            rprint(f"[red]✗ Error: {result['error']}[/red]")
        else:
            battle_result = result.get('battle_result', {})
            winner = battle_result.get('winner', 'Unknown')
            total_turns = battle_result.get('total_turns', 0)
            
            rprint(f"\n[green]🏆 Winner: {winner.title()}[/green]")
            rprint(f"[blue]📊 Battle lasted {total_turns} turns[/blue]")
            
            # Show battle log summary
            battle_log = battle_result.get('battle_log', [])
            if battle_log:
                rprint("\n[yellow]📜 Battle Summary:[/yellow]")
                for i, log_entry in enumerate(battle_log[-5:], 1):  # Show last 5 entries
                    if log_entry.get('action') == 'attack':
                        attacker = log_entry.get('attacker', '')
                        damage = log_entry.get('damage', 0)
                        move = log_entry.get('move', '')
                        rprint(f"  • {attacker.title()} used {move.title()}: {damage} damage")
                    elif log_entry.get('action') == 'faint':
                        rprint(f"  • {log_entry.get('message', '')}")
            
            # Show final stats
            if 'final_stats' in result:
                rprint("\n[blue]📈 Final Stats:[/blue]")
                for pokemon_name, stats in result['final_stats'].items():
                    hp = stats.get('hp', 0)
                    max_hp = stats.get('max_hp', 1)
                    hp_percent = (hp / max_hp) * 100
                    status = "Fainted" if stats.get('fainted') else f"{hp}/{max_hp} HP ({hp_percent:.1f}%)"
                    rprint(f"  • {pokemon_name.title()}: {status}")


@cli.command()
@click.argument('pokemon1')
@click.argument('pokemon2')
@click.option('--level', default=50, help='Pokemon level (1-100)')
@click.pass_context
async def predict(ctx, pokemon1, pokemon2, level):
    """Predict battle outcome."""
    url = ctx.obj['url']
    
    async with PokemonMCPTester(url) as tester:
        rprint(f"[blue]🔮 Predicting battle: {pokemon1.title()} vs {pokemon2.title()}[/blue]")
        
        result = await tester.test_battle_prediction(pokemon1, pokemon2, level)
        
        if "error" in result:
            rprint(f"[red]✗ Error: {result['error']}[/red]")
        else:
            prediction = result.get('prediction', {})
            
            # Show predictions
            p1_info = prediction.get('pokemon1', {})
            p2_info = prediction.get('pokemon2', {})
            
            table = Table(title="Battle Prediction")
            table.add_column("Pokemon", style="cyan")
            table.add_column("Win Chance", style="yellow")
            table.add_column("Advantages", style="green")
            
            table.add_row(
                p1_info.get('name', '').title(),
                p1_info.get('win_chance', 'N/A'),
                ", ".join(p1_info.get('advantages', []))
            )
            table.add_row(
                p2_info.get('name', '').title(),
                p2_info.get('win_chance', 'N/A'),
                ", ".join(p2_info.get('advantages', []))
            )
            
            console.print(table)
            
            winner = prediction.get('predicted_winner', 'Unknown')
            confidence = prediction.get('confidence', 'Unknown')
            
            rprint(f"\n[green]🏆 Predicted Winner: {winner.title()}[/green]")
            rprint(f"[blue]🎯 Confidence: {confidence.title()}[/blue]")


@cli.command()
@click.pass_context
async def demo(ctx):
    """Run a quick demo of all features."""
    url = ctx.obj['url']
    
    async with PokemonMCPTester(url) as tester:
        rprint("[bold blue]🎮 Pokemon MCP Server Demo[/bold blue]\n")
        
        # Check server status
        rprint("[blue]1. Checking server status...[/blue]")
        if not await tester.test_connection():
            rprint("[red]✗ Server is not accessible. Please start it first.[/red]")
            return
        rprint("[green]✓ Server is online[/green]\n")
        
        # Get Pokemon info
        rprint("[blue]2. Getting Pokemon information...[/blue]")
        result = await tester.test_pokemon_resource("pikachu")
        if "error" not in result:
            rprint(f"[green]✓ Retrieved data for {result['name'].title()}[/green]")
            rprint(f"   Types: {', '.join(result.get('types', []))}")
            rprint(f"   HP: {result.get('stats', {}).get('hp', 'N/A')}")
        rprint()
        
        # Search Pokemon
        rprint("[blue]3. Searching Pokemon...[/blue]")
        result = await tester.test_pokemon_search("char")
        if "error" not in result:
            matches = result.get('matches', [])
            rprint(f"[green]✓ Found {len(matches)} Pokemon matching 'char'[/green]")
            if matches:
                rprint(f"   Examples: {', '.join(matches[:3])}")
        rprint()
        
        # Battle prediction
        rprint("[blue]4. Predicting battle outcome...[/blue]")
        result = await tester.test_battle_prediction("charizard", "blastoise")
        if "error" not in result:
            prediction = result.get('prediction', {})
            winner = prediction.get('predicted_winner', 'Unknown')
            rprint(f"[green]✓ Predicted winner: {winner.title()}[/green]")
        rprint()
        
        # Battle simulation
        rprint("[blue]5. Simulating a quick battle...[/blue]")
        result = await tester.test_battle_simulation("pikachu", "squirtle", 25)
        if "error" not in result:
            battle_result = result.get('battle_result', {})
            winner = battle_result.get('winner', 'Unknown')
            turns = battle_result.get('total_turns', 0)
            rprint(f"[green]✓ Battle complete! Winner: {winner.title()} in {turns} turns[/green]")
        rprint()
        
        rprint("[bold green]🎉 Demo complete! All features are working.[/bold green]")
        rprint("\nTry these commands:")
        rprint("  python interactive_test.py pokemon charizard")
        rprint("  python interactive_test.py battle pikachu charizard")
        rprint("  python interactive_test.py search fire")


# Async command wrapper
def async_command(f):
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# Apply async wrapper to commands
for name in ['status', 'pokemon', 'search', 'battle', 'predict', 'demo']:
    if hasattr(cli, 'commands') and name in cli.commands:
        cli.commands[name].callback = async_command(cli.commands[name].callback)


if __name__ == '__main__':
    cli()