from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class PokemonType(BaseModel):
    """Represents a Pokémon type (e.g., Fire, Water, Grass)"""
    name: str
    url: str


class PokemonAbility(BaseModel):
    """Represents a Pokémon ability"""
    name: str
    url: str
    is_hidden: bool = False
    slot: int


class PokemonStat(BaseModel):
    """Represents a single Pokémon stat"""
    name: Literal["hp", "attack", "defense", "special-attack", "special-defense", "speed"]
    base_stat: int
    effort: int = 0


class PokemonStats(BaseModel):
    """Complete stat set for a Pokémon"""
    hp: int
    attack: int
    defense: int
    special_attack: int = Field(alias="special-attack")
    special_defense: int = Field(alias="special-defense") 
    speed: int
    
    class Config:
        allow_population_by_field_name = True


class MoveLearnMethod(BaseModel):
    """How a Pokémon learns a move"""
    name: str
    url: str


class MoveVersionGroupDetails(BaseModel):
    """Move learning details for specific game versions"""
    level_learned_at: int
    move_learn_method: MoveLearnMethod
    version_group: Dict[str, str]


class PokemonMove(BaseModel):
    """A move that a Pokémon can learn"""
    name: str
    url: str
    level_learned: int = 0
    learn_method: str = "level-up"


class MoveDetails(BaseModel):
    """Detailed information about a move"""
    name: str
    power: Optional[int] = None
    accuracy: Optional[int] = None
    pp: int
    priority: int = 0
    damage_class: str  # physical, special, status
    type: str
    target: str
    effect_chance: Optional[int] = None
    effect_entries: List[Dict[str, Any]] = []


class EvolutionChain(BaseModel):
    """Represents an evolution chain"""
    species_name: str
    evolves_to: List["EvolutionChain"] = []
    evolution_details: List[Dict[str, Any]] = []


class Pokemon(BaseModel):
    """Complete Pokémon data model"""
    id: int
    name: str
    height: int  # in decimeters
    weight: int  # in hectograms
    base_experience: int
    types: List[str]  # Simplified to just type names
    abilities: List[PokemonAbility]
    stats: PokemonStats
    moves: List[PokemonMove] = []
    species_url: str = ""
    
    @property
    def primary_type(self) -> str:
        """Returns the primary (first) type"""
        return self.types[0] if self.types else "normal"
    
    @property
    def secondary_type(self) -> Optional[str]:
        """Returns the secondary type if it exists"""
        return self.types[1] if len(self.types) > 1 else None
    
    @property
    def is_dual_type(self) -> bool:
        """Returns True if Pokémon has two types"""
        return len(self.types) == 2


class BattlePokemon(BaseModel):
    """Pokémon instance configured for battle"""
    pokemon: Pokemon
    level: int = 50
    current_hp: int
    max_hp: int
    status_effects: List[str] = []  # paralysis, burn, poison, etc.
    stat_modifiers: Dict[str, int] = Field(default_factory=dict)  # -6 to +6 for each stat
    
    def __init__(self, pokemon: Pokemon, level: int = 50, **data):
        # Calculate HP based on level and base stats
        max_hp = int(((2 * pokemon.stats.hp * level) / 100) + level + 10)
        super().__init__(
            pokemon=pokemon,
            level=level,
            current_hp=max_hp,
            max_hp=max_hp,
            **data
        )
    
    @property
    def is_fainted(self) -> bool:
        """Returns True if Pokémon has fainted"""
        return self.current_hp <= 0
    
    @property
    def hp_percentage(self) -> float:
        """Returns HP as percentage (0.0 to 1.0)"""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0
    
    def get_effective_stat(self, stat_name: str) -> int:
        """Get effective stat value including modifiers"""
        base_stat = getattr(self.pokemon.stats, stat_name)
        modifier = self.stat_modifiers.get(stat_name, 0)
        
        # Calculate stat at current level
        if stat_name == "hp":
            return self.max_hp
        else:
            level_stat = int(((2 * base_stat * self.level) / 100) + 5)
            
            # Apply stat modifier (stages from -6 to +6)
            multiplier = max(2, 2 + modifier) / max(2, 2 - modifier)
            return int(level_stat * multiplier)


class BattleLog(BaseModel):
    """Represents a single battle log entry"""
    turn: int
    action: str
    attacker: str
    defender: str
    move_used: Optional[str] = None
    damage: Optional[int] = None
    effectiveness: Optional[str] = None  # "super effective", "not very effective", etc.
    critical_hit: bool = False
    status_applied: Optional[str] = None
    message: str


class BattleResult(BaseModel):
    """Complete battle simulation result"""
    winner: str
    loser: str
    total_turns: int
    battle_log: List[BattleLog]
    final_stats: Dict[str, Dict[str, Any]]  # HP and status for both Pokemon


# Update forward references
EvolutionChain.model_rebuild()