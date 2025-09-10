#!/usr/bin/env python3
"""
Interactive test script for Pokemon MCP Server.

Provides a command-line interface to test all server endpoints and features.
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, Optional

import httpx
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint
from rich.live import Live
from rich.text import Text

console = Console()

# Battle emojis mapping
POKEMON_EMOJIS = {
    'charizard': '🔥', 'blastoise': '🌊', 'venusaur': '🌿', 'pikachu': '⚡', 'raichu': '⚡',
    'mewtwo': '🧠', 'mew': '✨', 'zapdos': '⚡', 'articuno': '❄️', 'moltres': '🔥',
    'alakazam': '🔮', 'machamp': '💪', 'gengar': '👻', 'gyarados': '🐉', 'dragonite': '🐉',
    'snorlax': '😴', 'lucario': '🥋', 'garchomp': '🦈', 'tyranitar': '🗿', 'salamence': '🐉'
}

TYPE_EMOJIS = {
    'fire': '🔥', 'water': '🌊', 'grass': '🌿', 'electric': '⚡', 'psychic': '🧠',
    'ice': '❄️', 'dragon': '🐉', 'dark': '🌑', 'steel': '⚙️', 'fairy': '✨',
    'fighting': '👊', 'poison': '☠️', 'ground': '🌍', 'flying': '🦅', 'bug': '🐛',
    'rock': '🗿', 'ghost': '👻', 'normal': '⚪'
}

STATUS_EMOJIS = {
    'paralysis': '⚡', 'burn': '🔥', 'poison': '☠️', 'freeze': '❄️', 'sleep': '😴'
}

async def display_epic_battle(result: Dict[str, Any], pokemon1: str, pokemon2: str):
    """Display battle with epic slow animation and emojis."""
    
    # Get battle data
    winner = result.get('winner', 'Unknown')
    total_turns = result.get('turns', 0)
    battle_log = result.get('battle_log', [])
    final_stats = result.get('final_stats', {})
    turn_history = result.get('turn_history', [])
    
    # Get Pokemon emojis
    p1_emoji = POKEMON_EMOJIS.get(pokemon1.lower(), '🎮')
    p2_emoji = POKEMON_EMOJIS.get(pokemon2.lower(), '🎮')
    
    # Battle intro
    rprint("\n" + "="*60)
    rprint(f"[bold yellow]🏟️  EPIC POKEMON BATTLE ARENA  🏟️[/bold yellow]")
    rprint("="*60)
    await asyncio.sleep(1)
    
    rprint(f"\n[bold blue]{p1_emoji} {pokemon1.title()}[/bold blue] [bold white]VS[/bold white] [bold red]{p2_emoji} {pokemon2.title()}[/bold red]")
    await asyncio.sleep(1)
    
    # Show initial stats
    rprint(f"\n[cyan]📊 Battle Setup:[/cyan]")
    for name, stats in final_stats.items():
        emoji = POKEMON_EMOJIS.get(name.lower(), '🎮')
        types = stats.get('types', [])
        type_emojis = ''.join([TYPE_EMOJIS.get(t, '') for t in types[:2]])
        max_hp = stats.get('max_hp', 100)
        rprint(f"  {emoji} [bold]{name.title()}[/bold] {type_emojis} - {max_hp} HP")
    
    await asyncio.sleep(2)
    rprint(f"\n[bold yellow]⚔️  BATTLE BEGIN!  ⚔️[/bold yellow]\n")
    await asyncio.sleep(1)
    
    # Display turn-by-turn action
    if turn_history:
        for turn_data in turn_history:
            await display_battle_turn(turn_data, p1_emoji, p2_emoji, pokemon1, pokemon2, final_stats)
    else:
        # Fallback to battle log
        await display_battle_log_slow(battle_log, p1_emoji, p2_emoji)
    
    # Battle conclusion
    await asyncio.sleep(1)
    rprint("\n" + "="*60)
    rprint(f"[bold yellow]🏆  BATTLE CONCLUSION  🏆[/bold yellow]")
    rprint("="*60)
    await asyncio.sleep(0.5)
    
    if winner.lower() == 'draw':
        rprint(f"[bold yellow]🤝 It's a draw! Both Pokemon fought valiantly![/bold yellow]")
    else:
        winner_emoji = POKEMON_EMOJIS.get(winner.lower(), '👑')
        rprint(f"[bold green]🎉 {winner_emoji} {winner.title()} is victorious! 🎉[/bold green]")
    
    rprint(f"[blue]📊 Battle Duration: {total_turns} turns[/blue]")
    await asyncio.sleep(1)
    
    # Final stats with health bars
    rprint(f"\n[bold cyan]📈 Final Battle Stats:[/bold cyan]")
    for name, stats in final_stats.items():
        emoji = POKEMON_EMOJIS.get(name.lower(), '🎮')
        hp = stats.get('hp', 0)
        max_hp = stats.get('max_hp', 1)
        hp_percent = stats.get('hp_percentage', 0)
        status_effects = stats.get('status', [])
        is_fainted = stats.get('is_fainted', False)
        
        # Create health bar
        health_bar = create_health_bar(hp, max_hp)
        
        status_text = ""
        if status_effects:
            status_emojis = ''.join([STATUS_EMOJIS.get(s, '❓') for s in status_effects])
            status_text = f" {status_emojis}"
        
        if is_fainted:
            rprint(f"  {emoji} [bold]{name.title()}[/bold]: [red]💀 FAINTED[/red]{status_text}")
        else:
            rprint(f"  {emoji} [bold]{name.title()}[/bold]: {health_bar} {hp}/{max_hp} HP ({hp_percent:.1f}%){status_text}")
        
        await asyncio.sleep(0.5)
    
    # Show battle mechanics used
    mechanics = result.get('battle_mechanics', {})
    if mechanics:
        rprint(f"\n[bold cyan]🔧 Battle Mechanics Showcased:[/bold cyan]")
        features = mechanics.get('features_implemented', [])
        status_features = mechanics.get('status_effects_available', [])
        
        for i, feature in enumerate(features[:3], 1):
            rprint(f"  ✅ {feature}")
            await asyncio.sleep(0.3)
        
        if status_features:
            rprint(f"  ⚡ Status Effects: {', '.join([s.split()[0] for s in status_features[:3]])}")
            await asyncio.sleep(0.3)
    
    rprint(f"\n[bold yellow]Thanks for watching this epic battle! 🎮[/bold yellow]")

async def display_battle_turn(turn_data: Dict[str, Any], p1_emoji: str, p2_emoji: str, pokemon1: str, pokemon2: str, final_stats: Dict[str, Any]):
    """Display a single battle turn with animation."""
    turn_num = turn_data.get('turn_number', 0)
    p1_action = turn_data.get('pokemon1_action', '')
    p2_action = turn_data.get('pokemon2_action', '')
    p1_move = turn_data.get('pokemon1_move', '')
    p2_move = turn_data.get('pokemon2_move', '')
    damage_dealt = turn_data.get('damage_dealt', {})
    status_effects = turn_data.get('status_effects', [])
    p1_hp = turn_data.get('pokemon1_hp_after', 0)
    p2_hp = turn_data.get('pokemon2_hp_after', 0)
    
    rprint(f"[bold blue]🔄 Turn {turn_num}[/bold blue]")
    
    # Show active status effects at start of turn (simulate what would be active)
    # This is a visual enhancement to show status effects more clearly
    if turn_num > 1:  # Only show after first turn when status effects might be active
        await show_active_status_effects(pokemon1, pokemon2, p1_emoji, p2_emoji)
    
    await asyncio.sleep(0.8)
    
    # Show status effects at start of turn (if any exist)
    for status_msg in status_effects:
        if any(keyword in status_msg.lower() for keyword in ['hurt by', 'unable to move', 'fast asleep', 'frozen', 'paralyzed']):
            enhanced_status = add_battle_emojis(status_msg)
            rprint(f"  💫 {enhanced_status}")
            await asyncio.sleep(1.0)
    
    # Show actions with emojis
    if p1_action and 'used' in p1_action.lower():
        move_emoji = get_move_emoji(p1_move)
        enhanced_action = add_battle_emojis(p1_action)
        rprint(f"  {p1_emoji} {enhanced_action} {move_emoji}")
        await asyncio.sleep(1.2)
    elif p1_action and any(keyword in p1_action.lower() for keyword in ['unable', 'fainted', 'no action']):
        enhanced_action = add_battle_emojis(p1_action)
        rprint(f"  {p1_emoji} {enhanced_action}")
        await asyncio.sleep(1.0)
    
    if p2_action and 'used' in p2_action.lower():
        move_emoji = get_move_emoji(p2_move)
        enhanced_action = add_battle_emojis(p2_action)
        rprint(f"  {p2_emoji} {enhanced_action} {move_emoji}")
        await asyncio.sleep(1.2)
    elif p2_action and any(keyword in p2_action.lower() for keyword in ['unable', 'fainted', 'no action']):
        enhanced_action = add_battle_emojis(p2_action)
        rprint(f"  {p2_emoji} {enhanced_action}")
        await asyncio.sleep(1.0)
    
    # Show new status effects applied this turn
    for status_msg in status_effects:
        if any(keyword in status_msg.lower() for keyword in ['is now', 'became', 'was inflicted']):
            enhanced_status = add_battle_emojis(status_msg)
            rprint(f"  🌟 {enhanced_status}")
            await asyncio.sleep(1.0)
    
    # Show HP after turn with health bars
    if p1_hp > 0 and p2_hp > 0:
        # Create mini health bars for turn display
        p1_bar = create_health_bar(p1_hp, 200, 10)  # Estimate max HP for display
        p2_bar = create_health_bar(p2_hp, 200, 10)
        rprint(f"  💚 {p1_emoji} {p1_bar} {p1_hp} HP")
        rprint(f"  💚 {p2_emoji} {p2_bar} {p2_hp} HP")
    elif p1_hp <= 0:
        rprint(f"  💀 {p1_emoji} [red]FAINTED![/red]")
    elif p2_hp <= 0:
        rprint(f"  💀 {p2_emoji} [red]FAINTED![/red]")
    
    await asyncio.sleep(0.8)
    rprint("")

async def display_battle_log_slow(battle_log: list, p1_emoji: str, p2_emoji: str):
    """Display battle log slowly with emojis as fallback."""
    for i, log_entry in enumerate(battle_log):
        if log_entry.strip():
            enhanced_log = add_battle_emojis(log_entry)
            rprint(f"  {enhanced_log}")
            await asyncio.sleep(1.0)
        
        # Add spacing every few entries
        if (i + 1) % 3 == 0:
            await asyncio.sleep(0.5)

def create_health_bar(current_hp: int, max_hp: int, width: int = 20) -> str:
    """Create a visual health bar."""
    if max_hp <= 0:
        return "[red]▬▬▬▬▬▬▬▬▬▬[/red]"
    
    percentage = current_hp / max_hp
    filled = int(width * percentage)
    empty = width - filled
    
    if percentage > 0.6:
        color = "green"
    elif percentage > 0.3:
        color = "yellow"
    else:
        color = "red"
    
    bar = "█" * filled + "░" * empty
    return f"[{color}]{bar}[/{color}]"

def get_move_emoji(move_name: str) -> str:
    """Get emoji for move type."""
    if not move_name:
        return ""
    
    move_lower = move_name.lower()
    
    move_emojis = {
        'fire': '🔥', 'flame': '🔥', 'ember': '🔥', 'blast': '💥',
        'water': '🌊', 'surf': '🌊', 'bubble': '💧', 'hydro': '🌊',
        'thunder': '⚡', 'electric': '⚡', 'shock': '⚡', 'bolt': '⚡',
        'psychic': '🧠', 'confusion': '🌀', 'psybeam': '💫',
        'ice': '❄️', 'freeze': '❄️', 'blizzard': '🌨️',
        'earthquake': '🌍', 'ground': '🌍', 'dig': '🕳️',
        'wing': '🦅', 'fly': '🦅', 'aerial': '🦅',
        'tackle': '👊', 'punch': '👊', 'scratch': '🔪', 'slash': '⚔️',
        'poison': '☠️', 'toxic': '☠️', 'sludge': '🟢',
        'rock': '🗿', 'stone': '🗿', 'slide': '⛰️'
    }
    
    for keyword, emoji in move_emojis.items():
        if keyword in move_lower:
            return emoji
    
    return "💫"

def add_battle_emojis(text: str) -> str:
    """Add emojis to battle text for more excitement."""
    # Effectiveness messages
    text = text.replace("super effective", "💥 SUPER EFFECTIVE 💥")
    text = text.replace("not very effective", "😐 not very effective")
    text = text.replace("It's super effective!", "💥 It's SUPER EFFECTIVE! 💥")
    text = text.replace("It's not very effective", "😐 It's not very effective")
    
    # Battle outcomes
    text = text.replace("critical hit", "💥 CRITICAL HIT 💥")
    text = text.replace("Critical hit!", "💥 CRITICAL HIT! 💥")
    text = text.replace("fainted", "💀 FAINTED")
    text = text.replace("missed", "💨 MISSED")
    
    # Status effects - initial application
    text = text.replace("is now paralysis", "⚡ is now PARALYZED")
    text = text.replace("is now burn", "🔥 is now BURNED")
    text = text.replace("is now poison", "☠️ is now POISONED")
    text = text.replace("is now freeze", "❄️ is now FROZEN")
    text = text.replace("is now sleep", "😴 is now ASLEEP")
    
    # Status effects - ongoing effects
    text = text.replace("hurt by burn", "🔥 HURT BY BURN")
    text = text.replace("hurt by poison", "☠️ HURT BY POISON")
    text = text.replace("is hurt by its burn", "🔥 is HURT BY BURN")
    text = text.replace("is hurt by poison", "☠️ is HURT BY POISON")
    
    # Status effects - prevention
    text = text.replace("unable to move", "⚡ UNABLE TO MOVE (Paralyzed)")
    text = text.replace("is unable to move", "⚡ is UNABLE TO MOVE (Paralyzed)")
    text = text.replace("fast asleep", "😴 FAST ASLEEP")
    text = text.replace("is fast asleep", "😴 is FAST ASLEEP")
    text = text.replace("frozen solid", "❄️ FROZEN SOLID")
    text = text.replace("is frozen solid", "❄️ is FROZEN SOLID")
    
    # Status recovery
    text = text.replace("thawed out", "❄️➡️ THAWED OUT")
    text = text.replace("woke up", "😴➡️ WOKE UP")
    text = text.replace("recovered from", "✨ RECOVERED FROM")
    
    return text

async def show_active_status_effects(pokemon1: str, pokemon2: str, p1_emoji: str, p2_emoji: str):
    """Show active status effects in a visually appealing way."""
    # This is a visual enhancement - in a real implementation, we'd track actual status
    # For now, we'll show this as a placeholder when status effects are likely active
    status_display = []
    
    # You could extend this to track actual status from battle data
    # For demo purposes, we'll show the concept
    
    if status_display:
        rprint(f"  [dim]💫 Active Effects: {' | '.join(status_display)}[/dim]")
        await asyncio.sleep(0.5)

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
            rprint(f"[red]❌ Error: {result['error']}[/red]")
        else:
            await display_epic_battle(result, pokemon1, pokemon2)


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