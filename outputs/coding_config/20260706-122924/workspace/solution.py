```python
# solution.py
"""
Team Treasure Hunt - Multiplayer Action Game Engine

A text-based simulation of a collaborative treasure-hunt game.
Teams of up to 4 players navigate environments, overcome obstacles,
solve collaborative puzzles, collect treasures and race to the final
chamber.  Each player has a unique ability that is required to solve
specific challenges.

The module is self-contained: it defines the game model, the engine,
and a comprehensive unittest suite.
"""

from __future__ import annotations

import random
import unittest
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set


# --------------------------------------------------------------------------- #
# Constants and configuration
# --------------------------------------------------------------------------- #

MAX_PLAYERS_PER_TEAM = 4
TIME_BONUS_BASE = 1000          # Points awarded for reaching the final chamber
TIME_BONUS_PER_TICK = 10        # Penalty per tick elapsed when finishing
FINAL_CHAMBER_BONUS = 500       # Extra reward for the first team to finish
MAX_HEALTH = 100
REST_HEAL = 10


# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #

class Ability(Enum):
    """Unique player abilities used to overcome obstacles and puzzles."""
    STRENGTH = auto()      # Move heavy objects
    AGILITY = auto()       # Navigate tight spaces / thorn bushes
    INTELLIGENCE = auto()  # Solve complex puzzles
    STEALTH = auto()       # Avoid traps


class ActionType(Enum):
    """All actions a player may queue for a tick."""
    MOVE = auto()      # Advance to the next environment if puzzles are solved
    SOLVE = auto()     # Contribute to a puzzle using the player's ability
    ASSIST = auto()    # Alias for SOLVE (collaborative contribution)
    COLLECT = auto()   # Pick up a treasure
    REST = auto()      # Recover a small amount of health
    LEAVE = auto()     # Disconnect / leave the game


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class Action:
    """A single player action queued for the next tick."""
    team_name: str
    player_name: str
    action_type: ActionType
    target: Optional[str] = None  # e.g. puzzle name, treasure name


@dataclass
class Player:
    """A participant in the treasure hunt."""
    name: str
    ability: Ability
    team_name: str
    health: int = MAX_HEALTH
    active: bool = True

    def take_damage(self, amount: int) -> None:
        """Apply damage and deactivate the player if health drops to zero."""
        if not self.active:
            return
        self.health = max(0, self.health - amount)
        if self.health == 0:
            self.active = False

    def heal(self, amount: int) -> None:
        """Restore health up to the maximum."""
        if self.active:
            self.health = min(MAX_HEALTH, self.health + amount)

    def leave(self) -> None:
        """Mark the player as inactive (disconnected)."""
        self.active = False


@dataclass
class Obstacle:
    """
    An environmental hazard that is automatically overcome if a team has a
    player with the required ability.  Otherwise the whole active team takes
    damage.
    """
    name: str
    required_ability: Ability
    damage: int

    def resolve(self, team: Team) -> List[str]:
        """
        Apply the obstacle to a team.  Returns a list of log messages.
        """
        messages: List[str] = []
        if team.has_ability(self.required_ability):
            messages.append(
                f"{self.name} is bypassed by {self.required_ability.name}."
            )
        else:
            messages.append(
                f"{self.name} triggers! Team takes {self.damage} damage."
            )
            for player in team.active_players():
                player.take_damage(self.damage)
        return messages


@dataclass
class Puzzle:
    """
    A collaborative puzzle that requires a specific number of contributions
    from players with particular abilities.  Once the requirements are met
    the puzzle is solved.
    """
    name: str
    required_abilities: Dict[Ability, int] = field(default_factory=dict)
    contributions: Dict[Ability, Set[str]] = field(default_factory=dict)
    solved: bool = False

    def __post_init__(self) -> None:
        # Ensure every required ability has a contribution container.
        for ability in self.required_abilities:
            self.contributions.setdefault(ability, set())

    def contribute(self, player: Player) -> bool:
        """
        Register a contribution from *player* if their ability is needed
        and they have not already contributed.  Returns True if the
        contribution was accepted.
        """
        if self.solved:
            return False
        ability = player.ability
        if ability not in self.required_abilities:
            return False
        if player.name in self.contributions[ability]:
            return False
        self.contributions[ability].add(player.name)
        return True

    def check_solved(self) -> bool:
        """Evaluate whether all required contributions have been made."""
        if self.solved:
            return True
        self.solved = all(
            len(self.contributions.get(ability, set())) >= needed
            for ability, needed in self.required_abilities.items()
        )
        return self.solved

    def remove_contributions(self, player_name: str) -> None:
        """Remove all contributions made by a player who left the game."""
        for ability in self.contributions:
            self.contributions[ability].discard(player_name)
        # A departed player may invalidate a previously solved puzzle.
        if self.solved and not self.check_solved():
            self.solved = False


@dataclass
class Treasure:
    """A collectible reward inside an environment."""
    name: str
    points: int
    required_ability: Optional[Ability] = None
    collected: bool = False

    def can_collect(self, player: Player) -> bool:
        """Check whether *player* meets the ability requirement."""
        if self.collected:
            return False
        if self.required_ability is None:
            return True
        return player.ability == self.required_ability

    def collect(self) -> int:
        """Mark the treasure as collected and return its point value."""
        self.collected = True
        return self.points


@dataclass
class Environment:
    """
    A game level containing obstacles, puzzles and treasures.
    """
    name: str
    difficulty: int
    obstacles: List[Obstacle] = field(default_factory=list)
    puzzles: List[Puzzle] = field(default_factory=list)
    treasures: List[Treasure] = field(default_factory=list)
    is_final: bool = False

    def all_puzzles_solved(self) -> bool:
        """True when every puzzle in this environment has been solved."""
        return all(puzzle.solved for puzzle in self.puzzles)

    def get_puzzle(self, name: str) -> Optional[Puzzle]:
        """Find a puzzle by name."""
        for puzzle in self.puzzles:
            if puzzle.name == name:
                return puzzle
        return None

    def get_treasure(self, name: str) -> Optional[Treasure]:
        """Find a treasure by name."""
        for treasure in self.treasures:
            if treasure.name == name:
                return treasure
        return None

    def on_entry(self, team: Team) -> List[str]:
        """Apply all obstacles when a team enters this environment."""
        messages: List[str] = []
        for obstacle in self.obstacles:
            messages.extend(obstacle.resolve(team))
        return messages


@dataclass
class Team:
    """
    A group of players competing together.  A team may contain up to
    MAX_PLAYERS_PER_TEAM members and each ability should be unique within
    the team for balanced gameplay.
    """
    name: str
    players: List[Player] = field(default_factory=list)
    score: int = 0
    treasures_collected: int = 0
    current_environment_index: int = 0
    finished: bool = False
    finish_tick: Optional[int] = None
    final_chamber_bonus_awarded: bool = False

    def active_players(self) -> List[Player]:
        """Return players who are still in the game."""
        return [p for p in self.players if p.active]

    def has_ability(self, ability: Ability) -> bool:
        """Check whether an active player has the given ability."""
        return any(p.ability == ability for p in self.active_players())

    def add_player(self, player: Player) -> None:
        """
        Add a player to the team, enforcing size and unique-ability rules.
        """
        if len(self.players) >= MAX_PLAYERS_PER_TEAM:
            raise ValueError(
                f"Team {self.name} already has {MAX_PLAYERS_PER_TEAM} players."
            )
        if any(p.ability == player.ability for p in self.players):
            raise ValueError(
                f"Team {self.name} already has a player with {player.ability.name}."
            )
        self.players.append(player)

    def remove_player(self, player_name: str) -> Optional[Player]:
        """
        Remove a player by name.  Returns the removed player or None.
        """
        for player in self.players:
            if player.name == player_name:
                player.leave()
                return player
        return None

    def award_points(self, points: int) -> None:
        """Add points to the team's score."""
        self.score += points


# --------------------------------------------------------------------------- #
# Game engine
# --------------------------------------------------------------------------- #

class GameEngine:
    """
    Central controller for Team Treasure Hunt.

    Responsibilities:
      - Manage teams, players and environments.
      - Accept and validate player actions.
      - Process actions simultaneously each tick.
      - Apply obstacles, puzzle solving