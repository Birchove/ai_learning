"""Auto game runner for AI-driven gameplay."""

import asyncio
import logging
from typing import Optional

from werewolf.agents.factory import create_agent
from werewolf.llm.qwen_client import QwenClient
from werewolf.config import Phase, ActionType
from werewolf.utils.logger import log_agent_action

logger = logging.getLogger(__name__)


class AutoGameRunner:
    """Automatically runs the game with AI players."""

    def __init__(self, engine, llm_client: Optional[QwenClient] = None):
        self.engine = engine
        self.llm_client = llm_client or QwenClient()
        self.agents: dict[int, any] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def setup_agents(self):
        """Create agents for all players."""
        if not self.engine.state:
            raise RuntimeError("Game not created")

        for player in self.engine.state.players:
            agent = create_agent(
                role=player.role,
                player_id=player.player_id,
                name=player.name,
                llm_client=self.llm_client
            )
            self.agents[player.player_id] = agent

        logger.info(f"Created {len(self.agents)} agents")

    async def run_night_phase(self) -> dict:
        """Run night phase with AI agents taking actions."""
        if not self.engine.state:
            return {}

        night_results = {}

        # Get alive players
        alive_players = [p for p in self.engine.state.players if p.is_alive]
        alive_player_ids = [p.player_id for p in alive_players]

        for player in alive_players:
            if not player.is_ai:
                continue  # Skip human players

            agent = self.agents.get(player.player_id)
            if not agent:
                continue

            # Get visible state for this agent
            state = self.engine.get_visible_state(player.player_id)

            # Handle night action based on role
            if player.role == "werewolf":
                action = agent.night_action(state)
                if action and action.get("target_id"):
                    self.engine.process_night_action(
                        player.player_id,
                        ActionType.KILL,
                        action["target_id"]
                    )
                    night_results[player.player_id] = {"action": "kill", "target": action["target_id"]}
                    log_agent_action(self.engine.state.game_id, player.player_id, player.role, "kill", action)

            elif player.role == "seer":
                action = agent.night_action(state)
                if action and action.get("target_id"):
                    self.engine.process_night_action(
                        player.player_id,
                        ActionType.CHECK,
                        action["target_id"]
                    )
                    night_results[player.player_id] = {"action": "check", "target": action["target_id"]}

            elif player.role == "witch":
                action = agent.night_action(state)
                if action:
                    if action.get("action_type") == ActionType.SAVE:
                        self.engine.process_night_action(
                            player.player_id,
                            ActionType.SAVE,
                            action.get("target_id")
                        )
                        night_results[player.player_id] = {"action": "save", "target": action.get("target_id")}
                    elif action.get("action_type") == ActionType.POISON:
                        self.engine.process_night_action(
                            player.player_id,
                            ActionType.POISON,
                            action.get("target_id")
                        )
                        night_results[player.player_id] = {"action": "poison", "target": action.get("target_id")}

            elif player.role == "guard":
                action = agent.night_action(state)
                if action and action.get("target_id"):
                    self.engine.process_night_action(
                        player.player_id,
                        ActionType.GUARD,
                        action["target_id"]
                    )
                    night_results[player.player_id] = {"action": "guard", "target": action["target_id"]}

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        return night_results

    async def run_day_phase(self) -> list:
        """Run day phase with AI agents speaking."""
        if not self.engine.state:
            return []

        speeches = []
        alive_players = [p for p in self.engine.state.players if p.is_alive]

        for player in alive_players:
            if not player.is_ai:
                continue  # Skip human players

            agent = self.agents.get(player.player_id)
            if not agent:
                continue

            # Get visible state for this agent
            state = self.engine.get_visible_state(player.player_id)

            # Generate speech
            speech = agent.speak(state)
            if speech:
                self.engine.add_speech(player.player_id, speech)
                speeches.append({
                    "player_id": player.player_id,
                    "content": speech
                })
                log_agent_action(self.engine.state.game_id, player.player_id, player.role, "speak", {"content": speech})

            # Small delay to avoid rate limiting
            await asyncio.sleep(1)

        return speeches

    async def run_vote_phase(self) -> dict:
        """Run vote phase with AI agents voting."""
        if not self.engine.state:
            return {}

        votes = {}
        alive_players = [p for p in self.engine.state.players if p.is_alive]

        for player in alive_players:
            if not player.is_ai:
                continue  # Skip human players

            agent = self.agents.get(player.player_id)
            if not agent:
                continue

            # Get visible state for this agent
            state = self.engine.get_visible_state(player.player_id)

            # Make vote decision
            target_id = agent.vote(state)
            if target_id and target_id > 0:
                self.engine.add_vote(player.player_id, target_id)
                votes[player.player_id] = target_id
                log_agent_action(self.engine.state.game_id, player.player_id, player.role, "vote", {"target": target_id})

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        return votes

    async def run_full_round(self) -> dict:
        """Run a complete round (night -> day -> vote -> result)."""
        if not self.engine.state or not self.agents:
            return {}

        results = {}

        # Night phase
        self.engine.next_phase()  # Start night (already in night from start_game)
        night_results = await self.run_night_phase()
        results["night"] = night_results

        # Execute night actions
        night_execution = self.engine.execute_night_actions()
        results["night_execution"] = night_execution

        # Process deaths from night
        if night_execution.get("kill_target"):
            kill_target = night_execution["kill_target"]
            saved = night_execution.get("saved")
            if kill_target != saved:
                self.engine.eliminate_player(kill_target, "werewolf_kill")

        # Check win condition
        winner = self.engine.check_win_condition()
        if winner:
            results["winner"] = winner
            return results

        # Day phase
        self.engine.next_phase()  # Night -> Day
        day_speeches = await self.run_day_phase()
        results["speeches"] = day_speeches

        # Check win condition
        winner = self.engine.check_win_condition()
        if winner:
            results["winner"] = winner
            return results

        # Vote phase
        self.engine.next_phase()  # Day -> Vote
        votes = await self.run_vote_phase()
        results["votes"] = votes

        # Process vote
        eliminated = self.engine.process_vote_phase()
        if eliminated > 0:
            self.engine.eliminate_player(eliminated, "vote")

        # Next day (dead_speech -> night)
        self.engine.next_phase()

        # Check win condition
        winner = self.engine.check_win_condition()
        if winner:
            results["winner"] = winner

        return results

    async def run_game(self, max_rounds: int = 20):
        """Run the entire game automatically."""
        if not self.engine.state:
            raise RuntimeError("Game not created")

        self._running = True
        round_num = 0

        # Start game if not started
        if self.engine.state.status == "waiting":
            self.engine.start_game()

        # Setup agents
        self.setup_agents()

        while self._running and round_num < max_rounds:
            round_num += 1
            logger.info(f"Starting round {round_num}")

            results = await self.run_full_round()

            if results.get("winner"):
                logger.info(f"Game ended. Winner: {results['winner']}")
                self.engine.save_to_json()
                break

            # Check if game state ended
            if self.engine.state.status == "ended":
                break

        self._running = False
        return {
            "rounds": round_num,
            "winner": self.engine.state.winner,
            "status": self.engine.state.status
        }

    def stop(self):
        """Stop the auto game runner."""
        self._running = False
        if self._task:
            self._task.cancel()


def create_auto_runner(engine, llm_client: QwenClient = None) -> AutoGameRunner:
    """Factory function to create an auto game runner."""
    return AutoGameRunner(engine, llm_client)