"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from werewolf.main import app
from werewolf.api.routes import games, agents


class TestAPI:
    """Test cases for REST API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test."""
        games.clear()
        agents.clear()

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_create_game(self, client):
        """Test game creation."""
        response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {
                "werewolf": 2,
                "seer": 1,
                "villager": 3,
            },
            "ai_count": 6,
            "human_count": 0
        })

        assert response.status_code == 200
        data = response.json()
        assert "game_id" in data
        assert data["name"] == "Test Game"

    def test_list_games(self, client):
        """Test listing games."""
        # Create a game first
        client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })

        response = client.get("/api/games")
        assert response.status_code == 200
        assert "games" in response.json()

    def test_get_game(self, client):
        """Test getting game details."""
        # Create a game first
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]

        response = client.get(f"/api/games/{game_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == game_id
        assert data["name"] == "Test Game"

    def test_get_game_not_found(self, client):
        """Test getting non-existent game."""
        response = client.get("/api/games/nonexistent")
        assert response.status_code == 404

    def test_delete_game(self, client):
        """Test deleting a game."""
        # Create a game first
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]

        response = client.delete(f"/api/games/{game_id}")
        assert response.status_code == 200

        # Verify game is deleted
        get_response = client.get(f"/api/games/{game_id}")
        assert get_response.status_code == 404

    def test_start_game(self, client):
        """Test starting a game."""
        # Create a game first
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]

        response = client.post(f"/api/games/{game_id}/start")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_submit_action_speak(self, client):
        """Test submitting a speak action."""
        # Create and start a game
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]
        client.post(f"/api/games/{game_id}/start")

        response = client.post(f"/api/games/{game_id}/action", json={
            "player_id": 1,
            "action_type": "speak",
            "content": "Hello everyone!"
        })

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_submit_action_vote(self, client):
        """Test submitting a vote action."""
        # Create and start a game
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]
        client.post(f"/api/games/{game_id}/start")

        response = client.post(f"/api/games/{game_id}/action", json={
            "player_id": 1,
            "action_type": "vote",
            "target_id": 2
        })

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_get_game_state(self, client):
        """Test getting game state."""
        # Create and start a game
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]
        client.post(f"/api/games/{game_id}/start")

        response = client.get(f"/api/games/{game_id}/state", params={"player_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        assert "phase" in data

    def test_get_game_log(self, client):
        """Test getting game log."""
        # Create and start a game
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]
        client.post(f"/api/games/{game_id}/start")

        response = client.get(f"/api/games/{game_id}/log")
        assert response.status_code == 200
        data = response.json()
        assert "players" in data

    def test_get_speeches(self, client):
        """Test getting speeches."""
        # Create and start a game
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]
        client.post(f"/api/games/{game_id}/start")

        response = client.get(f"/api/games/{game_id}/speeches")
        assert response.status_code == 200
        assert "speeches" in response.json()

    def test_advance_phase(self, client):
        """Test advancing phase."""
        # Create and start a game
        create_response = client.post("/api/games", json={
            "name": "Test Game",
            "player_count": {"werewolf": 2, "seer": 1, "villager": 3},
            "ai_count": 5
        })
        game_id = create_response.json()["game_id"]
        client.post(f"/api/games/{game_id}/start")

        response = client.post(f"/api/games/{game_id}/next_phase")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["phase"] == "day"