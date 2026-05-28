"""游戏状态管理"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Phase(Enum):
    DAY = "day"
    NIGHT = "night"
    VOTE = "vote"
    RESULT = "result"


class Role(Enum):
    VILLAGER = "villager"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"
    WEREWOLF = "werewolf"


@dataclass
class Player:
    id: int
    name: str
    role: Role
    alive: bool = True
    will_vote_for: Optional[int] = None

    def __hash__(self):
        return hash(self.id)


@dataclass
class GameState:
    phase: Phase = Phase.NIGHT
    day_number: int = 0
    players: list[Player] = field(default_factory=list)
    dead_players: list[Player] = field(default_factory=list)
    death_info: list[str] = field(default_factory=list)
    seer_results: dict = field(default_factory=dict)
    witch_potions: dict = field(default_factory=lambda: {"heal": 1, "poison": 1})
    hunter_shot: bool = False
    vote_records: list[tuple[int, int]] = field(default_factory=list)

    def get_alive_players(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def kill_player(self, player_id: int, cause: str = "died"):
        for p in self.players:
            if p.id == player_id:
                p.alive = False
                self.dead_players.append(p)
                self.death_info.append(f"Player {player_id} {cause}")
                break

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def check_winner(self) -> Optional[str]:
        alive_players = self.get_alive_players()
        alive_roles = {p.role for p in alive_players}

        werewolf_alive = Role.WEREWOLF in alive_roles
        good_alive = any(r in alive_roles for r in [Role.VILLAGER, Role.SEER, Role.WITCH, Role.HUNTER])

        if not werewolf_alive:
            return "good"
        if not good_alive:
            return "werewolf"
        if len(alive_players) <= 2 and werewolf_alive:
            return "werewolf"
        return None