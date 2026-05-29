"""Game rules and validations."""

from typing import Optional
from werewolf.config import Role, Camp, MIN_PLAYERS, MAX_PLAYERS


class GameRules:
    """Handles game rules and validations."""

    @staticmethod
    def validate_player_count(player_count: dict[str, int]) -> tuple[bool, str]:
        """Validate player count configuration."""
        total = sum(player_count.values())

        if total < MIN_PLAYERS:
            return False, f"Total players must be at least {MIN_PLAYERS}"
        if total > MAX_PLAYERS:
            return False, f"Total players cannot exceed {MAX_PLAYERS}"

        # Must have at least one werewolf
        if player_count.get("werewolf", 0) < 1:
            return False, "Must have at least one werewolf"

        # Must have at least some good players
        good_players = sum([
            player_count.get("villager", 0),
            player_count.get("seer", 0),
            player_count.get("witch", 0),
            player_count.get("guard", 0),
            player_count.get("hunter", 0),
        ])
        if good_players < 1:
            return False, "Must have at least some good players"

        return True, "OK"

    @staticmethod
    def check_win_condition(
        alive_players: list,
        dead_players: list,
        werewolf_count: int,
        good_count: int
    ) -> Optional[str]:
        """Check if game has a winner.

        Returns:
            Camp constant if game ended, None if game continues
        """
        # No players left
        if not alive_players:
            return Camp.NEUTRAL

        # Count alive werewolves and goods
        alive_werewolves = werewolf_count
        alive_goods = sum(1 for p in alive_players if p.role != "werewolf")

        # Win conditions for werewolves
        if alive_werewolves > 0 and alive_werewolves >= alive_goods:
            return Camp.WEREWOLF

        # Win conditions for goods
        if alive_werewolves == 0:
            return Camp.GOOD

        return None

    @staticmethod
    def can_seer_check(target_player, already_checked: dict[str, str]) -> bool:
        """Check if seer can verify a target."""
        if not target_player.is_alive:
            return False
        if str(target_player.player_id) in already_checked:
            return False
        return True

    @staticmethod
    def can_guard_guard(target_player, guard_last_target: Optional[int], all_players: list) -> bool:
        """Check if guard can guard a target."""
        if not target_player.is_alive:
            return False
        # Cannot guard same player consecutively
        if guard_last_target is not None and target_player.player_id == guard_last_target:
            return False
        return True

    @staticmethod
    def can_witch_save(witch_can_save: bool, target_was_attacked: bool) -> bool:
        """Check if witch can save."""
        return witch_can_save and target_was_attacked

    @staticmethod
    def can_witch_poison(witch_can_poison: bool, target_player) -> bool:
        """Check if witch can poison."""
        return witch_can_poison and target_player.is_alive

    @staticmethod
    def get_default_config() -> dict[str, int]:
        """Get default player count configuration."""
        return {
            "werewolf": 3,
            "seer": 1,
            "witch": 1,
            "guard": 1,
            "hunter": 1,
            "villager": 3,
        }

    @staticmethod
    def distribute_roles(player_count: dict[str, int]) -> list[str]:
        """Distribute roles based on player count configuration.

        Returns:
            List of role names for each player position
        """
        roles = []
        for role, count in player_count.items():
            roles.extend([role] * count)
        return roles