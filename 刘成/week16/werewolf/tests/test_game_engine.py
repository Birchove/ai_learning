"""Tests for game engine."""

import pytest
from werewolf.engine.game_engine import GameEngine
from werewolf.models.player import Player
from werewolf.config import Phase, GameStatus, Role


class TestGameEngine:
    """Test cases for GameEngine class."""

    def test_create_game(self):
        """Test game creation."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        game_id, state = engine.create_game("Test Game", player_count)

        assert game_id is not None
        assert state.name == "Test Game"
        assert state.status == GameStatus.WAITING

    def test_setup_players(self):
        """Test player setup."""
        engine = GameEngine()
        engine.create_game("Test Game", {"werewolf": 2, "seer": 1, "villager": 3})
        engine.setup_players(ai_count=6, human_count=0)

        # Config creates 10 players total (2+1+3 + hunter+guard = 10)
        assert len(engine.state.players) == 10
        # First 6 (i < 6) are AI, rest are human
        ai_count = sum(1 for p in engine.state.players if p.is_ai)
        assert ai_count == 6
        assert engine.state.players[0].role == "werewolf"
        assert engine.state.players[0].is_ai is True

    def test_start_game(self):
        """Test game start."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        game_id, _ = engine.create_game("Test Game", player_count)
        engine.setup_players(ai_count=6, human_count=0)
        engine.start_game()

        assert engine.state.status == GameStatus.RUNNING
        assert engine.state.day == 1
        assert engine.state.phase == Phase.NIGHT

    def test_next_phase(self):
        """Test phase transitions."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        engine.create_game("Test Game", player_count)
        engine.setup_players(ai_count=6, human_count=0)
        engine.start_game()

        day, phase = engine.next_phase()
        assert phase == Phase.DAY

        day, phase = engine.next_phase()
        assert phase == Phase.VOTE

    def test_eliminate_player(self):
        """Test player elimination."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        engine.create_game("Test Game", player_count)
        engine.setup_players(ai_count=6, human_count=0)
        engine.start_game()

        engine.eliminate_player(1, "vote")

        player = engine.state.get_player_by_id(1)
        assert player.is_alive is False
        assert len(engine.state.dead_players) == 1

    def test_get_visible_state(self):
        """Test information isolation."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        engine.create_game("Test Game", player_count)
        engine.setup_players(ai_count=6, human_count=0)
        engine.start_game()

        # Get visible state for player 1 (werewolf)
        visible = engine.get_visible_state(1)

        assert visible["my_id"] == 1
        assert "players" in visible

    def test_check_win_condition(self):
        """Test win condition check."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        engine.create_game("Test Game", player_count)
        engine.setup_players(ai_count=6, human_count=0)
        engine.start_game()

        # No winner yet
        winner = engine.check_win_condition()
        assert winner is None

    def test_add_speech_and_vote(self):
        """Test adding speeches and votes."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        engine.create_game("Test Game", player_count)
        engine.setup_players(ai_count=6, human_count=0)
        engine.start_game()

        engine.add_speech(1, "I think player 3 is a werewolf.")
        engine.add_vote(2, 3)

        assert len(engine.state.speech_records) == 1
        assert len(engine.state.vote_records) == 1
        assert engine.state.speech_records[0].content == "I think player 3 is a werewolf."

    def test_process_night_action(self):
        """Test night action processing."""
        engine = GameEngine()
        player_count = {
            "werewolf": 2,
            "seer": 1,
            "villager": 3,
        }

        engine.create_game("Test Game", player_count)
        engine.setup_players(ai_count=6, human_count=0)
        engine.start_game()

        engine.process_night_action(1, "kill", 3)
        engine.process_night_action(2, "check", 4)

        results = engine.execute_night_actions()

        assert results["kill_target"] == 3
        assert "4" in engine.state.seer_checks