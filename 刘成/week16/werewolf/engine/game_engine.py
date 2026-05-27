"""Game engine - core game logic."""

import uuid
import json
import logging
import os
from datetime import datetime
from typing import Optional
from werewolf.models.game import GameState
from werewolf.models.player import Player
from werewolf.config import Phase, GameStatus, Camp, AI_NAME_PREFIX
from werewolf.engine.phase import PhaseManager
from werewolf.engine.rules import GameRules
from werewolf.utils.logger import log_game_event, log_phase_change, log_game_result

logger = logging.getLogger(__name__)


class GameEngine:
    """Core game engine handling game flow and state."""

    def __init__(self):
        self.state: Optional[GameState] = None
        self.phase_manager = PhaseManager()
        self.rules = GameRules()
        self._pending_night_actions: dict[int, dict] = {}

    def create_game(self, name: str, player_count: dict[str, int]) -> tuple[str, GameState]:
        """Create a new game.

        Args:
            name: Game name
            player_count: Player count configuration

        Returns:
            game_id and initial game state
        """
        valid, msg = self.rules.validate_player_count(player_count)
        if not valid:
            raise ValueError(msg)

        game_id = str(uuid.uuid4())[:8]
        self.state = GameState(
            game_id=game_id,
            name=name,
            status=GameStatus.WAITING,
        )
        self.phase_manager = PhaseManager()

        log_game_event(game_id, "game_created", {"name": name, "player_count": player_count})
        logger.info(f"Game {game_id} created with config: {player_count}")

        return game_id, self.state

    def setup_players(self, ai_count: int = 0, human_count: int = 0):
        """Setup players based on configuration.

        Args:
            ai_count: Number of AI players
            human_count: Number of human players
        """
        if not self.state:
            raise RuntimeError("Game not created")

        # Distribute roles
        player_count = self._calculate_player_count()
        roles = self.rules.distribute_roles(player_count)

        total_players = len(roles)
        player_id = 1

        for i in range(total_players):
            is_ai = i < ai_count if ai_count > 0 else True
            name = f"{AI_NAME_PREFIX}_{player_id}" if is_ai else f"Player_{player_id}"

            player = Player(
                player_id=player_id,
                name=name,
                role=roles[i],
                is_alive=True,
                is_ai=is_ai,
            )
            self.state.players.append(player)
            player_id += 1

        log_game_event(self.state.game_id, "players_setup", {
            "total": len(self.state.players),
            "roles": {r: roles.count(r) for r in set(roles)}
        })

    def _calculate_player_count(self) -> dict[str, int]:
        """Calculate player count from current state or default."""
        if self.state and hasattr(self, '_player_count'):
            return self._player_count
        return self.rules.get_default_config()

    def set_player_count(self, player_count: dict[str, int]):
        """Set player count configuration."""
        self._player_count = player_count

    def start_game(self) -> GameState:
        """Start the game."""
        if not self.state:
            raise RuntimeError("Game not created")
        if len(self.state.players) == 0:
            raise RuntimeError("No players in game")

        self.state.status = GameStatus.RUNNING
        self.state.day = 1
        self.state.phase = Phase.NIGHT
        self.phase_manager.start_game()

        log_game_event(self.state.game_id, "game_started", {"day": self.state.day})
        logger.info(f"Game {self.state.game_id} started")

        return self.state

    def next_phase(self) -> tuple[int, str]:
        """Move to the next game phase."""
        if not self.state:
            raise RuntimeError("Game not created")

        old_phase = self.state.phase
        day, new_phase = self.phase_manager.next_phase()

        self.state.day = day
        self.state.phase = new_phase

        # Handle phase-specific logic
        if new_phase == Phase.NIGHT:
            self.state.current_night += 1

        log_phase_change(self.state.game_id, day, old_phase, new_phase)
        logger.info(f"Game {self.state.game_id} phase changed: {old_phase} -> {new_phase}")

        return day, new_phase

    def eliminate_player(self, player_id: int, reason: str = "vote"):
        """Eliminate a player from the game."""
        if not self.state:
            raise RuntimeError("Game not created")

        player = self.state.get_player_by_id(player_id)
        if not player:
            return

        player.is_alive = False
        self.state.dead_players.append(player)

        log_game_event(self.state.game_id, "player_dead", {
            "player_id": player_id,
            "name": player.name,
            "role": player.role,
            "reason": reason
        })
        logger.info(f"Player {player_id} ({player.name}) eliminated: {reason}")

    def get_visible_state(self, player_id: int) -> dict:
        """Get game state visible to a specific player (information isolation)."""
        if not self.state:
            raise RuntimeError("Game not created")

        player = self.state.get_player_by_id(player_id)
        if not player:
            return {}

        visible = {
            "game_id": self.state.game_id,
            "day": self.state.day,
            "phase": self.state.phase,
            "my_id": player_id,
            "my_role": player.role,
            "my_is_alive": player.is_alive,
        }

        # All players see basic player info
        visible["players"] = []
        for p in self.state.players:
            info = {
                "player_id": p.player_id,
                "name": p.name,
                "is_alive": p.is_alive,
            }
            # Dead players reveal their role to everyone
            if not p.is_alive:
                info["role"] = p.role
            visible["players"].append(info)

        # Werewolf sees other werewolves' real identity
        if player.role == "werewolf":
            for p in visible["players"]:
                if p["player_id"] != player_id:
                    actual = self.state.get_player_by_id(p["player_id"])
                    if actual and actual.role == "werewolf":
                        p["role"] = "werewolf"

        # Seer sees their check results
        if player.role == "seer":
            visible["seer_checks"] = self.state.seer_checks

        # Add recent speeches
        visible["speech_records"] = [
            {"player_id": s.player_id, "content": s.content}
            for s in self.state.speech_records[-10:]
        ]

        # Add vote records
        visible["vote_records"] = [
            {"voter_id": v.voter_id, "target_id": v.target_id, "day": v.day}
            for v in self.state.vote_records[-10:]
        ]

        # Add night actions (only for current night after they happen)
        visible["night_actions"] = [
            {"player_id": a.player_id, "action_type": a.action_type, "target_id": a.target_id}
            for a in self.state.night_actions if a.night == self.state.current_night
        ]

        return visible

    def check_win_condition(self) -> Optional[str]:
        """Check if game has ended and return winner."""
        if not self.state:
            return None

        alive = self.state.get_alive_players()
        werewolf_count = len(self.state.get_werewolf_players())
        good_count = len([p for p in alive if p.role != "werewolf"])

        winner = self.rules.check_win_condition(alive, self.state.dead_players, werewolf_count, good_count)

        if winner:
            self.state.status = GameStatus.ENDED
            self.state.winner = winner
            log_game_result(self.state.game_id, winner, "win_condition_met")
            logger.info(f"Game {self.state.game_id} ended. Winner: {winner}")

        return winner

    def add_speech(self, player_id: int, content: str):
        """Add a speech record."""
        if self.state:
            self.state.add_speech(player_id, content)

    def add_vote(self, voter_id: int, target_id: int):
        """Add a vote record."""
        if self.state:
            self.state.add_vote(voter_id, target_id)

    def process_night_action(self, player_id: int, action_type: str, target_id: Optional[int] = None):
        """Process a night action."""
        if not self.state:
            return

        self.state.add_night_action(player_id, action_type, target_id)

        # Store pending action
        self._pending_night_actions[player_id] = {
            "action_type": action_type,
            "target_id": target_id,
        }

    def execute_night_actions(self) -> dict:
        """Execute all collected night actions and return results."""
        if not self.state:
            return {}

        results = {}

        # Werewolf kill action
        werewolf_kills = [p for p, a in self._pending_night_actions.items()
                         if a["action_type"] == "kill" and a["target_id"]]
        if werewolf_kills:
            # Use last werewolf's target
            last_kill = self._pending_night_actions[werewolf_kills[-1]]
            results["kill_target"] = last_kill["target_id"]

        # Seer check action
        seer_checks = [p for p, a in self._pending_night_actions.items() if a["action_type"] == "check"]
        if seer_checks:
            seer_action = self._pending_night_actions[seer_checks[-1]]
            if seer_action["target_id"]:
                target = self.state.get_player_by_id(seer_action["target_id"])
                if target:
                    self.state.seer_checks[str(seer_action["target_id"])] = target.role

        # Guard guard action
        guard_guards = [p for p, a in self._pending_night_actions.items() if a["action_type"] == "guard"]
        if guard_guards:
            guard_action = self._pending_night_actions[guard_guards[-1]]
            if guard_action["target_id"]:
                self.state.guard_last_target = guard_action["target_id"]
                results["guard_target"] = guard_action["target_id"]

        # Clear pending actions
        self._pending_night_actions = {}

        # Execute witch actions if any
        witch_save = self._pending_night_actions.get("witch_save")
        if witch_save and results.get("kill_target"):
            results["saved"] = results["kill_target"]
            self.state.witch_can_save = False

        return results

    def process_day_phase(self) -> dict:
        """Process day phase - daylight discussion."""
        if not self.state:
            return {}

        return {
            "phase": self.state.phase,
            "day": self.state.day,
            "players": [
                {"player_id": p.player_id, "name": p.name, "is_alive": p.is_alive}
                for p in self.state.players
            ]
        }

    def process_vote_phase(self) -> int:
        """Process vote and return eliminated player id."""
        if not self.state:
            return -1

        # Count votes
        vote_count: dict[int, int] = {}
        for vote in self.state.vote_records:
            if vote.day == self.state.day:
                target = vote.target_id
                vote_count[target] = vote_count.get(target, 0) + 1

        if not vote_count:
            return -1

        # Find player with most votes
        max_votes = max(vote_count.values())
        candidates = [p for p, c in vote_count.items() if c == max_votes]

        # If tie, no elimination
        if len(candidates) > 1:
            return -1

        return candidates[0]

    def get_game_summary(self) -> dict:
        """Get game summary for log output."""
        if not self.state:
            return {}

        return {
            "game_id": self.state.game_id,
            "name": self.state.name,
            "status": self.state.status,
            "winner": self.state.winner,
            "day": self.state.day,
            "players": [
                {"player_id": p.player_id, "name": p.name, "role": p.role, "is_alive": p.is_alive}
                for p in self.state.players
            ],
            "dead_players": [
                {"player_id": p.player_id, "name": p.name, "role": p.role}
                for p in self.state.dead_players
            ],
            "speech_records": [
                {"day": s.day, "player_id": s.player_id, "content": s.content}
                for s in self.state.speech_records
            ],
            "vote_records": [
                {"day": v.day, "voter_id": v.voter_id, "target_id": v.target_id}
                for v in self.state.vote_records
            ],
        }

    def save_to_json(self, filepath: str = None) -> str:
        """Save game summary to a JSON file for replay.

        Args:
            filepath: Custom filepath. If None, auto-generate from game_id.

        Returns:
            Path to saved file.
        """
        if not self.state:
            return ""

        summary = self.get_game_summary()
        summary["saved_at"] = datetime.now().isoformat()

        if not filepath:
            # Create logs directory if not exists
            logs_dir = "game_logs"
            os.makedirs(logs_dir, exist_ok=True)
            filepath = os.path.join(logs_dir, f"game_{self.state.game_id}.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"Game saved to {filepath}")
        return filepath

    @staticmethod
    def load_from_json(filepath: str) -> dict:
        """Load game summary from a JSON file.

        Args:
            filepath: Path to the JSON file.

        Returns:
            Game summary dict.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)