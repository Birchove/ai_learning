"""预言家角色"""
from player_agent import PlayerAgent
from game_state import Role


class SeerAgent(PlayerAgent):
    def __init__(self, player_id: int, name: str):
        super().__init__(player_id, name, Role.SEER)
        self.checked_players: set[int] = set()

    def on_night_turn(self) -> int | None:
        alive = self.game_state.get_alive_players()
        for p in alive:
            if p.id != self.player_id and p.id not in self.checked_players:
                prompt = f"你是预言家 Player {self.player_id}。夜晚到来，请选择查验一名玩家。\n"
                prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
                prompt += "请给出要查验的玩家ID。"
                response = self.call_llm(prompt)
                target = self._parse_target_response(response)
                if target and target != self.player_id:
                    return target
        return None

    def on_day_phase(self, is_first_day: bool) -> str:
        prompt = f"你是预言家 Player {self.player_id}。当前是{'第一个' if is_first_day else '后续'}白天。\n"
        prompt += f"你的查验结果: {self.game_state.seer_results}\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "请以预言家身份发言，可以适当透露查验信息。"
        return self.call_llm(prompt)

    def on_vote_phase(self) -> int:
        prompt = f"你是预言家 Player {self.player_id}。投票阶段。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "请投票给最可疑的玩家。"
        response = self.call_llm(prompt)
        return self._parse_vote_response(response)

    def _parse_target_response(self, response: str) -> int | None:
        import re
        numbers = re.findall(r'\d+', response)
        for num in numbers:
            pid = int(num)
            if pid != self.player_id:
                player = self.game_state.get_player_by_id(pid)
                if player and player.alive:
                    self.checked_players.add(pid)
                    return pid
        return None

    def _parse_vote_response(self, response: str) -> int:
        import re
        numbers = re.findall(r'\d+', response)
        for num in numbers:
            pid = int(num)
            if pid != self.player_id:
                player = self.game_state.get_player_by_id(pid)
                if player and player.alive:
                    return pid
        return self.player_id