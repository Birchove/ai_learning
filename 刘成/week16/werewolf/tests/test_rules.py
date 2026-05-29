"""Tests for game rules."""

import pytest
from werewolf.engine.rules import GameRules
from werewolf.models.player import Player
from werewolf.config import Role, Camp


class TestGameRules:
    """Test cases for GameRules class."""

    def test_validate_player_count_valid(self):
        """Test validation with valid player count."""
        valid, msg = GameRules.validate_player_count({
            "werewolf": 3,
            "seer": 1,
            "witch": 1,
            "guard": 1,
            "hunter": 1,
            "villager": 3,
        })
        assert valid is True
        assert msg == "OK"

    def test_validate_player_count_too_few(self):
        """Test validation with too few players."""
        valid, msg = GameRules.validate_player_count({
            "werewolf": 1,
            "villager": 2,
        })
        assert valid is False
        assert "at least" in msg

    def test_validate_player_count_no_werewolf(self):
        """Test validation with no werewolf."""
        valid, msg = GameRules.validate_player_count({
            "seer": 1,
            "villager": 5,
        })
        assert valid is False
        assert "werewolf" in msg

    def test_check_win_condition_werewolf_wins(self):
        """Test werewolf win condition."""
        werewolves = [Player(player_id=1, name="W1", role=Role.WEREWOLF, is_alive=True)]
        goods = [Player(player_id=2, name="G1", role=Role.VILLAGER, is_alive=True)]

        winner = GameRules.check_win_condition(
            alive_players=werewolves + goods,
            dead_players=[],
            werewolf_count=1,
            good_count=1
        )
        assert winner == Camp.WEREWOLF

    def test_check_win_condition_good_wins(self):
        """Test good players win condition."""
        werewolves = [Player(player_id=1, name="W1", role=Role.WEREWOLF, is_alive=True)]
        goods = [
            Player(player_id=2, name="G1", role=Role.VILLAGER, is_alive=True),
            Player(player_id=3, name="G2", role=Role.VILLAGER, is_alive=True),
        ]

        winner = GameRules.check_win_condition(
            alive_players=werewolves + goods,
            dead_players=[],
            werewolf_count=1,
            good_count=2
        )
        assert winner is None  # Game continues

    def test_check_win_condition_all_werewolves_dead(self):
        """Test good wins when all werewolves dead."""
        goods = [
            Player(player_id=1, name="G1", role=Role.VILLAGER, is_alive=True),
            Player(player_id=2, name="G2", role=Role.VILLAGER, is_alive=True),
        ]

        winner = GameRules.check_win_condition(
            alive_players=goods,
            dead_players=[],
            werewolf_count=0,
            good_count=2
        )
        assert winner == Camp.GOOD

    def test_distribute_roles(self):
        """Test role distribution."""
        config = {
            "werewolf": 2,
            "villager": 2,
        }
        roles = GameRules.distribute_roles(config)

        assert len(roles) == 4
        assert roles.count(Role.WEREWOLF) == 2
        assert roles.count(Role.VILLAGER) == 2

    def test_get_default_config(self):
        """Test default configuration."""
        config = GameRules.get_default_config()

        assert config["werewolf"] == 3
        assert config["seer"] == 1
        assert config["witch"] == 1
        assert config["guard"] == 1
        assert config["hunter"] == 1
        assert config["villager"] == 3