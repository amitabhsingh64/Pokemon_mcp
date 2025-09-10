"""
Unit tests for battle mechanics
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from battle.types import PokemonTypes
from battle.calculator import DamageCalculator, DamageResult
from battle.status import StatusManager, StatusType, ParalysisEffect, BurnEffect, PoisonEffect
from battle.engine import BattleEngine
from models.pokemon import Pokemon, PokemonStats, BattlePokemon, MoveDetails


class TestPokemonTypes:
    """Test the type effectiveness system"""
    
    def test_basic_type_effectiveness(self):
        """Test basic type matchups"""
        types = PokemonTypes()
        
        # Fire vs Grass (super effective)
        assert types.get_effectiveness("fire", "grass") == 2.0
        
        # Water vs Fire (super effective)
        assert types.get_effectiveness("water", "fire") == 2.0
        
        # Fire vs Water (not very effective)
        assert types.get_effectiveness("fire", "water") == 0.5
        
        # Normal vs Ghost (no effect)
        assert types.get_effectiveness("normal", "ghost") == 0.0
        
        # Fire vs Fire (normal)
        assert types.get_effectiveness("fire", "fire") == 0.5  # Actually resisted
    
    def test_dual_type_effectiveness(self):
        """Test effectiveness against dual-type Pokemon"""
        types = PokemonTypes()
        
        # Fire vs Grass/Poison (Bulbasaur)
        effectiveness = types.get_dual_type_effectiveness("fire", ["grass", "poison"])
        assert effectiveness == 2.0  # 2.0 * 1.0
        
        # Rock vs Flying/Fire (Charizard)
        effectiveness = types.get_dual_type_effectiveness("rock", ["flying", "fire"])
        assert effectiveness == 4.0  # 2.0 * 2.0
        
        # Water vs Ground/Rock (Onix)
        effectiveness = types.get_dual_type_effectiveness("water", ["ground", "rock"])
        assert effectiveness == 4.0  # 2.0 * 2.0
    
    def test_stab_calculation(self):
        """Test Same Type Attack Bonus"""
        types = PokemonTypes()
        
        # Fire move used by Fire-type Pokemon
        assert types.is_same_type_attack_bonus("fire", ["fire"]) is True
        assert types.get_stab_multiplier("fire", ["fire"]) == 1.5
        
        # Fire move used by Water-type Pokemon
        assert types.is_same_type_attack_bonus("fire", ["water"]) is False
        assert types.get_stab_multiplier("fire", ["water"]) == 1.0
        
        # Fire move used by Fire/Flying Pokemon
        assert types.is_same_type_attack_bonus("fire", ["fire", "flying"]) is True
        assert types.get_stab_multiplier("fire", ["fire", "flying"]) == 1.5
    
    def test_type_weaknesses_and_resistances(self):
        """Test weakness and resistance calculation"""
        types = PokemonTypes()
        
        # Fire type weaknesses and resistances
        fire_weaknesses = types.get_type_weaknesses(["fire"])
        assert "water" in fire_weaknesses
        assert "ground" in fire_weaknesses
        assert "rock" in fire_weaknesses
        
        fire_resistances = types.get_type_resistances(["fire"])
        assert "fire" in fire_resistances
        assert "grass" in fire_resistances
        assert "ice" in fire_resistances


class TestStatusEffects:
    """Test status effect mechanics"""
    
    def test_paralysis_effect(self):
        """Test paralysis status effect"""
        paralysis = ParalysisEffect()
        
        # Should reduce speed by 50%
        assert paralysis.get_stat_modifier("speed") == 0.5
        assert paralysis.get_stat_modifier("attack") == 1.0
        
        # Name should be correct
        assert paralysis.name == "paralysis"
    
    def test_burn_effect(self):
        """Test burn status effect"""
        burn = BurnEffect()
        
        # Should reduce attack by 50%
        assert burn.get_stat_modifier("attack") == 0.5
        assert burn.get_stat_modifier("speed") == 1.0
        
        # Should not prevent actions
        mock_pokemon = Mock()
        assert burn.prevents_action(mock_pokemon) is False
    
    def test_poison_effect(self):
        """Test poison status effect"""
        poison = PoisonEffect()
        
        # Should not affect stats
        assert poison.get_stat_modifier("attack") == 1.0
        assert poison.get_stat_modifier("speed") == 1.0
        
        # Should not prevent actions
        mock_pokemon = Mock()
        assert poison.prevents_action(mock_pokemon) is False
    
    def test_status_manager(self):
        """Test status effect management"""
        manager = StatusManager()
        
        # Create mock Pokemon
        mock_pokemon = Mock()
        mock_pokemon.pokemon.types = ["normal"]
        mock_pokemon.status_effects = []
        
        # Apply paralysis
        result = manager.apply_status(mock_pokemon, StatusType.PARALYSIS)
        assert "now paralysis" in result
        assert StatusType.PARALYSIS.value in manager.active_effects
        
        # Try to apply paralysis again (should fail)
        result = manager.apply_status(mock_pokemon, StatusType.PARALYSIS)
        assert "already paralysis" in result
        
        # Remove paralysis
        result = manager.remove_status(mock_pokemon, StatusType.PARALYSIS)
        assert "no longer paralysis" in result
        assert StatusType.PARALYSIS.value not in manager.active_effects


class TestDamageCalculator:
    """Test damage calculation mechanics"""
    
    def create_test_pokemon(self, name: str, types: list, stats: dict, level: int = 50) -> BattlePokemon:
        """Create a test Pokemon for calculations"""
        pokemon_stats = PokemonStats(
            hp=stats.get("hp", 100),
            attack=stats.get("attack", 100),
            defense=stats.get("defense", 100),
            special_attack=stats.get("special_attack", 100),
            special_defense=stats.get("special_defense", 100),
            speed=stats.get("speed", 100)
        )
        
        pokemon = Pokemon(
            id=1,
            name=name,
            height=10,
            weight=100,
            base_experience=100,
            types=types,
            abilities=[],
            stats=pokemon_stats,
            moves=[]
        )
        
        return BattlePokemon(pokemon, level)
    
    def create_test_move(self, name: str, move_type: str, power: int, damage_class: str = "physical") -> MoveDetails:
        """Create a test move for calculations"""
        return MoveDetails(
            name=name,
            power=power,
            accuracy=100,
            pp=10,
            priority=0,
            damage_class=damage_class,
            type=move_type,
            target="normal"
        )
    
    def test_basic_damage_calculation(self):
        """Test basic damage formula"""
        calculator = DamageCalculator()
        
        # Create test Pokemon
        attacker = self.create_test_pokemon("Attacker", ["normal"], {"attack": 100})
        defender = self.create_test_pokemon("Defender", ["normal"], {"defense": 100})
        
        # Create test move
        move = self.create_test_move("Tackle", "normal", 40)
        
        # Calculate damage
        result = calculator.calculate_damage(attacker, defender, move, critical_override=False)
        
        assert isinstance(result, DamageResult)
        assert result.damage > 0
        assert result.type_effectiveness == 1.0  # Normal effectiveness
        assert result.stab_applied is True  # Normal move by Normal-type Pokemon
    
    def test_type_effectiveness_in_damage(self):
        """Test type effectiveness in damage calculation"""
        calculator = DamageCalculator()
        
        # Fire attacker vs Grass defender
        attacker = self.create_test_pokemon("Fire", ["fire"], {"special_attack": 100})
        defender = self.create_test_pokemon("Grass", ["grass"], {"special_defense": 100})
        
        move = self.create_test_move("Ember", "fire", 40, "special")
        
        result = calculator.calculate_damage(attacker, defender, move, critical_override=False)
        
        assert result.type_effectiveness == 2.0  # Super effective
        assert result.stab_applied is True  # Fire move by Fire-type
        assert "super effective" in result.effectiveness_message
    
    def test_critical_hit_calculation(self):
        """Test critical hit mechanics"""
        calculator = DamageCalculator()
        
        attacker = self.create_test_pokemon("Attacker", ["normal"], {"attack": 100})
        defender = self.create_test_pokemon("Defender", ["normal"], {"defense": 100})
        move = self.create_test_move("Tackle", "normal", 40)
        
        # Force critical hit
        crit_result = calculator.calculate_damage(attacker, defender, move, critical_override=True)
        
        # Force no critical hit
        normal_result = calculator.calculate_damage(attacker, defender, move, critical_override=False)
        
        assert crit_result.is_critical is True
        assert normal_result.is_critical is False
        assert crit_result.damage >= normal_result.damage  # Critical should deal more damage
    
    def test_status_move_no_damage(self):
        """Test that status moves deal no damage"""
        calculator = DamageCalculator()
        
        attacker = self.create_test_pokemon("Attacker", ["normal"], {"attack": 100})
        defender = self.create_test_pokemon("Defender", ["normal"], {"defense": 100})
        
        # Status move
        status_move = MoveDetails(
            name="Thunder Wave",
            power=None,  # Status moves have no power
            accuracy=100,
            pp=10,
            priority=0,
            damage_class="status",
            type="electric",
            target="normal"
        )
        
        result = calculator.calculate_damage(attacker, defender, status_move)
        
        assert result.damage == 0
        assert result.is_critical is False
    
    def test_turn_order_calculation(self):
        """Test turn order based on speed"""
        calculator = DamageCalculator()
        
        fast_pokemon = self.create_test_pokemon("Fast", ["normal"], {"speed": 150})
        slow_pokemon = self.create_test_pokemon("Slow", ["normal"], {"speed": 50})
        
        first, second = calculator.get_turn_order(fast_pokemon, slow_pokemon)
        
        assert first.pokemon.name == "Fast"
        assert second.pokemon.name == "Slow"
        
        # Test reverse
        first, second = calculator.get_turn_order(slow_pokemon, fast_pokemon)
        
        assert first.pokemon.name == "Fast"
        assert second.pokemon.name == "Slow"


class TestBattleEngine:
    """Test the complete battle engine"""
    
    def create_test_pokemon(self, name: str, types: list, stats: dict, level: int = 50) -> BattlePokemon:
        """Create a test Pokemon for battle testing"""
        pokemon_stats = PokemonStats(
            hp=stats.get("hp", 100),
            attack=stats.get("attack", 100),
            defense=stats.get("defense", 100),
            special_attack=stats.get("special_attack", 100),
            special_defense=stats.get("special_defense", 100),
            speed=stats.get("speed", 100)
        )
        
        # Add some basic moves
        from models.pokemon import PokemonMove
        moves = [
            PokemonMove(name="tackle", url="", level_learned=1),
            PokemonMove(name="scratch", url="", level_learned=1),
        ]
        
        pokemon = Pokemon(
            id=1,
            name=name,
            height=10,
            weight=100,
            base_experience=100,
            types=types,
            abilities=[],
            stats=pokemon_stats,
            moves=moves
        )
        
        return BattlePokemon(pokemon, level)
    
    @pytest.mark.asyncio
    async def test_battle_setup(self):
        """Test battle initialization"""
        engine = BattleEngine()
        
        pokemon1 = self.create_test_pokemon("Pokemon1", ["normal"], {"hp": 100})
        pokemon2 = self.create_test_pokemon("Pokemon2", ["normal"], {"hp": 100})
        
        engine.setup_battle(pokemon1, pokemon2)
        
        assert engine.pokemon1 == pokemon1
        assert engine.pokemon2 == pokemon2
        assert engine.turn_counter == 0
        assert len(engine.battle_log) > 0  # Should have battle start log
    
    @pytest.mark.asyncio
    async def test_battle_simulation(self):
        """Test complete battle simulation"""
        engine = BattleEngine()
        
        # Create Pokemon with different HP to ensure battle ends
        strong_pokemon = self.create_test_pokemon("Strong", ["normal"], {"hp": 200, "attack": 150})
        weak_pokemon = self.create_test_pokemon("Weak", ["normal"], {"hp": 50, "defense": 50})
        
        result = await engine.simulate_battle(strong_pokemon, weak_pokemon)
        
        assert result.winner is not None
        assert result.loser is not None
        assert result.total_turns > 0
        assert len(result.battle_log) > 0
        assert result.winner != result.loser
    
    def test_battle_state_tracking(self):
        """Test battle state management"""
        engine = BattleEngine()
        
        pokemon1 = self.create_test_pokemon("Pokemon1", ["normal"], {"hp": 100})
        pokemon2 = self.create_test_pokemon("Pokemon2", ["normal"], {"hp": 100})
        
        # Before setup
        state = engine.get_battle_state()
        assert state["state"] == "setup"
        
        # After setup
        engine.setup_battle(pokemon1, pokemon2)
        state = engine.get_battle_state()
        assert state["pokemon1"]["name"] == "Pokemon1"
        assert state["pokemon2"]["name"] == "Pokemon2"
        assert state["turn"] == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])